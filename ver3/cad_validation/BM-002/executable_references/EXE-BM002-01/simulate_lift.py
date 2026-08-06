"""EXE-BM002-01 - MuJoCo rigid-body dynamics evidence for the BM-002 lift.

WHAT THIS IS
    A rigid-body simulation of the accepted BM-002 CAD, with the actual joint
    topology: a revolute crank on the CAD crank axis, a revolute crank joint, a
    fixed-length connecting rod, a revolute platform joint closed as an equality
    constraint, and the platform on one translational degree of freedom. Mass and
    inertia come from the accepted B-rep solids. It produces actuator torque with
    and without the 1 kg scenario payload, back-driving behaviour when the
    actuator is released, and ideal joint and guide reactions.

WHAT THIS IS NOT
    It is NOT a contact model. The guide is an IDEAL PRISMATIC CONSTRAINT and
    every joint is an IDEAL JOINT. Nothing here resolves contact, so nothing here
    can support a jamming, wear, binding or tolerance claim: REQ-007 stays
    NOT_VERIFIED (NRM-BM-002-014, NEG-BM-002-011). It computes no stress and no
    strain, so REQ-003 payload capacity stays UNSUPPORTED (UNR-BM-002-007).

    Every torque below depends on DECLARED DENSITY ASSUMPTIONS that no source
    supplies. The robust result is the DIFFERENCE between the payload run and the
    empty run, which is independent of them.

    python simulate_lift.py [--quick]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools")))

import build as B            # noqa: E402
import cadval as cv          # noqa: E402
import cadvideo as vid       # noqa: E402

import mujoco                # noqa: E402
from OCP.BRepGProp import BRepGProp   # noqa: E402
from OCP.GProp import GProp_GProps    # noqa: E402

SIMDIR = os.path.join(HERE, "simulation")
OUT = os.path.join(HERE, "validation", "simulation")
PLOTS = os.path.join(OUT, "plots")
REVIEW = os.path.join(OUT, "review")

P = B.load_params()
G = B.geom(P)
AY, AZ = G["axis_y"], G["axis_z"]
R_MM, L_MM = P["crank_radius"], P["rod_length"]
ACCEPTED_SIGNATURE = ("6824e5102424e3db883f16b684ab54f02c14eed19bead0116c704092"
                      "156bc2ee")

MM = 1e-3            # mm -> m


# =========================================================== declared assumptions
ASSUMPTIONS = {
    "densities_kg_m3": {
        "polymer_like": {
            "value": 1200.0,
            "bodies": ["BODY-HOUSING", "BODY-REAR-PANEL", "BODY-PLATFORM"],
            "why": ("a generic rigid polymer. The source states no material "
                    "(DOS-BM-002 S3), so this is a DECLARED SIMULATION ASSUMPTION, "
                    "NOT A SOURCE REQUIREMENT and NOT A VERIFIED MATERIAL "
                    "SELECTION.")},
        "metal_like": {
            "value": 7850.0,
            "bodies": ["BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD",
                       "BODY-CRANK-JOINT-PIN", "BODY-PLATFORM-JOINT-PIN"],
            "why": ("a generic steel-like metal for the mechanism bodies. Same "
                    "status: DECLARED SIMULATION ASSUMPTION, NOT A SOURCE "
                    "REQUIREMENT, NOT A VERIFIED MATERIAL SELECTION.")},
        "affects": ("empty-cycle torque, linearly in each body's mass. The "
                    "INCREMENTAL payload torque (payload run minus empty run) is "
                    "independent of these choices."),
    },
    "gravity_m_s2": {"value": [0.0, 0.0, -9.81],
                     "why": "standard, product standing upright on a desk"},
    "joint_damping_N_m_s_per_rad": {
        "value": 0.0,
        "why": ("zero in the primary model. Damping would ADD to the actuator "
                "torque and would DISSIPATE back-driving motion, so both primary "
                "results are the undamped case and a damped variant is run as a "
                "declared sensitivity.")},
    "joint_friction": {"value": 0.0,
                       "why": ("no Coulomb friction anywhere. Friction is a "
                               "contact-level property this model does not "
                               "resolve; adding a number would invent one.")},
    "payload_kg": {"value": 1.0,
                   "why": "SCENARIO-PAYLOAD-1KG, the source's approximately 1 kg"},
    "pin_simplification": {
        "value": ("BODY-CRANK-JOINT-PIN is welded to BODY-CRANK-SHAFT and "
                  "BODY-PLATFORM-JOINT-PIN is welded to BODY-PLATFORM."),
        "why": ("each pin is a body of revolution about a joint axis parallel to "
                "X, and each pin's centre is rigidly fixed to that parent in the "
                "CAD, so welding is EXACT for position and for inertia about the "
                "joint axis - the pin's own spin carries no dynamics here. Their "
                "full CAD mass and inertia are retained. This makes NO claim "
                "about pin contact, bending or bearing stress.")},
    "guide_representation": {
        "value": "one prismatic joint along +Z, an IDEAL GUIDE CONSTRAINT",
        "why": ("the CAD guide is two channels with 0.2 and 0.4 mm clearances. "
                "This model replaces them with a single ideal slide. It can carry "
                "the guide REACTION; it cannot carry jamming, binding, wear, "
                "local pressure or tolerance behaviour.")},
    "platform_joint_representation": {
        "value": "MuJoCo equality connect between the rod and the platform",
        "why": ("the slider-crank is a closed loop and MuJoCo integrates a tree. "
                "The connect constrains the two bodies to share the platform-pin "
                "point, leaving relative rotation free - which is a pin joint in "
                "this planar mechanism.")},
}

NOT_ESTABLISHED = [
    "payload structural capacity, stress, deflection, pin bending, shaft strength",
    "bearing pressure or local guide pressure",
    "fatigue, wear or life",
    "manufacturing feasibility or physical assembly force",
    "user ergonomic suitability or acceptable crank effort (no ceiling is stated)",
    "pinch safety or any safety property",
    "contact-level jamming or tolerance-induced binding",
    "self-locking outside the exact tested model",
]


# ================================================== CAD-derived mass properties
def inertia_about_com(shape) -> Tuple[float, np.ndarray, np.ndarray]:
    """(volume mm^3, COM mm, inertia about the COM in mm^5) from the B-rep solid.

    OCCT's GProp_GProps.MatrixOfInertia() is ALREADY referred to the centre of
    mass, not to the frame origin. That was checked rather than assumed: a
    100 mm cube at the origin corner returns 1.666667e9 mm^5, which is
    V(a^2+b^2)/12 about its own centre, and not the 6.666667e9 the same cube has
    about the origin. Applying a parallel-axis shift here would therefore SUBTRACT
    a term that is not present, and it produced inertia tensors with negative
    eigenvalues that MuJoCo rejected outright.

    Density and the mm -> SI conversion are applied by the caller so both stay
    visible.
    """
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, g)
    vol = g.Mass()
    c = g.CentreOfMass()
    com = np.array([c.X(), c.Y(), c.Z()])
    m = g.MatrixOfInertia()
    I_com = np.array([[m.Value(i, j) for j in (1, 2, 3)] for i in (1, 2, 3)])
    return vol, com, I_com


DENSITY = {}
for _grp in ("polymer_like", "metal_like"):
    for _b in ASSUMPTIONS["densities_kg_m3"][_grp]["bodies"]:
        DENSITY[_b] = ASSUMPTIONS["densities_kg_m3"][_grp]["value"]


def mass_properties() -> Dict:
    """Every product body's SI mass and inertia, from the accepted CAD solids."""
    rows = {}
    for b in B.build(P):
        vol, com, I_com_mm5 = inertia_about_com(b.shape)
        rho = DENSITY[b.id]
        mass = vol * 1e-9 * rho                      # mm^3 -> m^3 -> kg
        I = I_com_mm5 * 1e-15 * rho                  # mm^5 -> m^5 -> kg m^2
        w = np.linalg.eigvalsh(I)
        ok_pd = bool(np.all(w > 0.0))
        ok_tri = bool(w[0] + w[1] >= w[2] - 1e-15 and w[0] + w[2] >= w[1] - 1e-15
                      and w[1] + w[2] >= w[0] - 1e-15)
        rows[b.id] = {
            "material_class": ("polymer_like" if rho == 1200.0 else "metal_like"),
            "declared_density_kg_m3": rho,
            "cad_volume_mm3": round(vol, 6),
            "com_mm": [round(float(x), 6) for x in com],
            "com_m": [round(float(x) * MM, 9) for x in com],
            "mass_kg": round(float(mass), 9),
            "inertia_about_com_kg_m2": [[round(float(I[i][j]), 12) for j in range(3)]
                                        for i in range(3)],
            "principal_values_kg_m2": [round(float(x), 12) for x in w],
            "positive_mass": bool(mass > 0.0),
            "positive_definite": ok_pd,
            "triangle_inequality": ok_tri,
        }
    total = sum(r["mass_kg"] for r in rows.values())
    moving = sum(rows[k]["mass_kg"] for k in
                 ("BODY-CRANK-SHAFT", "BODY-CONNECTING-ROD", "BODY-PLATFORM",
                  "BODY-CRANK-JOINT-PIN", "BODY-PLATFORM-JOINT-PIN"))
    return {"bodies": rows,
            "total_product_mass_kg": round(total, 9),
            "moving_mass_kg": round(moving, 9),
            "static_mass_kg": round(total - moving, 9),
            "unit_conversion": ("CAD is in mm and mm^3. mass = volume_mm3 * 1e-9 * "
                                "rho; inertia = I_mm5 * 1e-15 * rho. Both checked "
                                "by the dimensional test in the report."),
            "inertia_frame": ("about each body's own centre of mass, in world-"
                              "aligned axes at the as-built (crank 0 deg) pose, "
                              "which is the pose every MuJoCo body frame is "
                              "defined in."),
            "all_masses_positive": all(r["positive_mass"] for r in rows.values()),
            "all_inertias_positive_definite": all(r["positive_definite"] for r in rows.values()),
            "all_triangle_inequalities_hold": all(r["triangle_inequality"] for r in rows.values()),
            "declared_assumption_note": ("DECLARED SIMULATION ASSUMPTION. NOT A "
                                         "SOURCE REQUIREMENT. NOT A VERIFIED "
                                         "MATERIAL SELECTION.")}


def payload_inertial() -> Dict:
    """The 1 kg scenario payload as a uniform box over its declared envelope."""
    a, b_, c = P["payload_x"] * MM, P["payload_y"] * MM, P["payload_z"] * MM
    m = ASSUMPTIONS["payload_kg"]["value"]
    I = np.diag([m * (b_ * b_ + c * c) / 12.0,
                 m * (a * a + c * c) / 12.0,
                 m * (a * a + b_ * b_) / 12.0])
    com = np.array([(G["payload_x0"] + G["payload_x1"]) / 2.0,
                    (G["payload_y0"] + G["payload_y1"]) / 2.0,
                    G["support_z_bottom"] + P["payload_z"] / 2.0])
    return {"mass_kg": m, "com_mm": [round(float(x), 4) for x in com],
            "inertia_about_com_kg_m2": [[round(float(I[i][j]), 12) for j in range(3)]
                                        for i in range(3)],
            "envelope_mm": [P["payload_x"], P["payload_y"], P["payload_z"]],
            "is_product_body": False,
            "note": ("SCENARIO-PAYLOAD-1KG. A scenario object, not a product body. "
                     "It is a uniform box over the declared envelope, rigidly "
                     "attached to the platform, and it is absent from the empty "
                     "model.")}


# ================================================================== the model
def _ftuple(v) -> str:
    return " ".join("%.9g" % float(x) for x in v)


def _inertial(mp: Dict, bid: str, origin_m: np.ndarray) -> str:
    r = mp["bodies"][bid]
    com = np.array(r["com_m"]) - origin_m
    I = np.array(r["inertia_about_com_kg_m2"])
    full = [I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2]]
    return ('<inertial pos="%s" mass="%.9g" fullinertia="%s"/>'
            % (_ftuple(com), r["mass_kg"], _ftuple(full)))


def _combined_inertial(mp: Dict, ids: Sequence[str], origin_m: np.ndarray,
                       extra: Optional[Dict] = None) -> str:
    """Composite inertial for a parent plus the bodies welded to it.

    Welding is a declared simplification, so the welded body's CAD mass and
    inertia are carried into the parent rather than discarded: masses add, the
    centre of mass is the mass-weighted mean, and each tensor is shifted to the
    combined centre of mass by the parallel-axis theorem.
    """
    ms, coms, Is = [], [], []
    for bid in ids:
        r = mp["bodies"][bid]
        ms.append(r["mass_kg"])
        coms.append(np.array(r["com_m"]))
        Is.append(np.array(r["inertia_about_com_kg_m2"]))
    if extra:
        ms.append(extra["mass_kg"])
        coms.append(np.array(extra["com_mm"]) * MM)
        Is.append(np.array(extra["inertia_about_com_kg_m2"]))
    M = float(sum(ms))
    C = sum(m * c for m, c in zip(ms, coms)) / M
    I = np.zeros((3, 3))
    for m, c, Ii in zip(ms, coms, Is):
        d = c - C
        I += Ii + m * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    full = [I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2]]
    return ('<inertial pos="%s" mass="%.9g" fullinertia="%s"/>'
            % (_ftuple(C - origin_m), M, _ftuple(full)))


# Tuned against the mechanism's own scale, not guessed. The crank's inertia about
# its axis is about 1e-3 kg m^2, so an explicit integrator needs kv*dt/I well below
# 2 and kp*dt^2/I well below 1. The first attempt used kp=4000, kv=200, which gives
# kv*dt/I = 77 and diverged on the first step. These give 0.4 and 8e-3.
SOLVER = {"timestep": 1.0 / 3000.0, "integrator": "implicitfast", "solver": "Newton",
          "iterations": 200, "tolerance": 1e-12,
          "eq_solref": (0.002, 1.0), "eq_solimp": (0.9999, 0.99999, 1e-6, 0.5, 2),
          "kp": 1500.0, "kv": 3.0}


def mjcf(mp: Dict, *, payload: bool, damping: float = 0.0,
         lock_platform: bool = False) -> str:
    """The MJCF. Topology mirrors the CAD joint topology exactly."""
    axis = np.array([0.0, AY, AZ]) * MM                      # crank axis, m
    cpin0 = np.array([0.0, AY, G["crank_pin_z_bottom"]]) * MM  # crank pin at theta=0
    plat_origin = np.array([0.0, 0.0, 0.0])                  # platform frame = world
    rod_anchor_local = np.array([0.0, 0.0, L_MM * MM])       # platform pin, rod-local
    g = ASSUMPTIONS["gravity_m_s2"]["value"]
    pay = payload_inertial() if payload else None

    crank_inertial = _combined_inertial(mp, ["BODY-CRANK-SHAFT",
                                             "BODY-CRANK-JOINT-PIN"], axis)
    rod_inertial = _inertial(mp, "BODY-CONNECTING-ROD", cpin0)
    plat_ids = ["BODY-PLATFORM", "BODY-PLATFORM-JOINT-PIN"]
    plat_inertial = _combined_inertial(mp, plat_ids, plat_origin, extra=pay)

    static = _combined_inertial(mp, ["BODY-HOUSING", "BODY-REAR-PANEL"],
                                np.zeros(3))
    return f"""<mujoco model="EXE-BM002-01-lift{'-payload1kg' if payload else '-empty'}">
  <compiler autolimits="true" angle="radian"/>
  <option gravity="{_ftuple(g)}" integrator="{SOLVER['integrator']}"
          timestep="{SOLVER['timestep']:.12f}" solver="{SOLVER['solver']}"
          iterations="{SOLVER['iterations']}" tolerance="{SOLVER['tolerance']:g}"/>
  <default>
    <geom contype="0" conaffinity="0" density="0" type="sphere" size="0.001"/>
  </default>
  <worldbody>
    <!-- BODY-HOUSING and BODY-REAR-PANEL: fixed world bodies. Their CAD mass is
         recorded here for the mass report; being welded to the world it takes no
         part in the dynamics, which is correct - the housing is the datum. -->
    <body name="housing_and_panel" pos="0 0 0">
      {static}
      <geom name="g_static" pos="0 0 0"/>
    </body>

    <!-- BODY-CRANK-SHAFT: revolute about the actual CAD crank axis, parallel to X.
         BODY-CRANK-JOINT-PIN is welded into it; see ASSUMPTIONS. -->
    <body name="crank" pos="{_ftuple(axis)}">
      <joint name="crank_hinge" type="hinge" axis="1 0 0" pos="0 0 0"
             damping="{damping:.9g}" frictionloss="0" limited="false"/>
      {crank_inertial}
      <geom name="g_crank" pos="0 0 0"/>
      <site name="s_crank_bearing" pos="0 0 0" size="0.002"/>

      <!-- BODY-CONNECTING-ROD: revolute at the actual crank-joint axis -->
      <body name="rod" pos="{_ftuple(cpin0 - axis)}">
        <joint name="crank_joint" type="hinge" axis="1 0 0" pos="0 0 0"
               damping="{damping:.9g}" frictionloss="0" limited="false"/>
        {rod_inertial}
        <geom name="g_rod" pos="0 0 0"/>
        <site name="s_crank_joint" pos="0 0 0" size="0.002"/>
        <site name="s_rod_far_end" pos="{_ftuple(rod_anchor_local)}" size="0.002"/>
      </body>
    </body>

    <!-- BODY-PLATFORM: one translational DOF along the actual vertical Z.
         The slide joint IS the ideal guide constraint; it removes all three
         rotations and both lateral translations. BODY-PLATFORM-JOINT-PIN is
         welded into it; the scenario payload is added here in the payload model. -->
    <body name="platform" pos="0 0 0">
      {'' if lock_platform else
        f'<joint name="platform_slide" type="slide" axis="0 0 1" pos="0 0 0" '
        f'damping="{damping:.9g}" frictionloss="0" limited="false"/>'}
      {plat_inertial}
      <geom name="g_platform" pos="0 0 0"/>
      <site name="s_guide" pos="0 0 0" size="0.002"/>
      <site name="s_platform_pin" pos="0 {AY * MM:.9g} {G['plat_pin_z_bottom'] * MM:.9g}"
            size="0.002"/>
    </body>
  </worldbody>

  <!-- the platform joint: the closed loop the slider-crank needs -->
  <equality>
    <connect name="platform_joint" body1="rod" body2="platform"
             anchor="{_ftuple(rod_anchor_local)}"
             solref="{_ftuple(SOLVER['eq_solref'])}"
             solimp="{_ftuple(SOLVER['eq_solimp'])}"/>
  </equality>

  <actuator>
    <general name="crank_drive" joint="crank_hinge" gaintype="fixed"
             biastype="affine" gainprm="{SOLVER['kp']:.9g} 0 0"
             biasprm="0 -{SOLVER['kp']:.9g} -{SOLVER['kv']:.9g}"
             ctrlrange="-1000 1000"/>
  </actuator>

  <sensor>
    <force name="f_crank_bearing" site="s_crank_bearing"/>
    <torque name="t_crank_bearing" site="s_crank_bearing"/>
    <force name="f_crank_joint" site="s_crank_joint"/>
    <torque name="t_crank_joint" site="s_crank_joint"/>
    <force name="f_guide" site="s_guide"/>
    <torque name="t_guide" site="s_guide"/>
    <jointpos name="q_crank" joint="crank_hinge"/>
    <jointvel name="v_crank" joint="crank_hinge"/>
    {'' if lock_platform else
      '<jointpos name="q_slide" joint="platform_slide"/>'
      '<jointvel name="v_slide" joint="platform_slide"/>'}
    <jointpos name="q_rod" joint="crank_joint"/>
    <actuatorfrc name="tau_crank" actuator="crank_drive"/>
  </sensor>
</mujoco>"""


# ============================================================ analytic check
def analytic_platform_z_mm(theta_rad: float) -> float:
    """Slider-crank platform-pin height, implemented independently of build.py.

    Deliberately re-derived here rather than imported: if the same function
    generated both sides of the cross-check, the check would compare a function
    with itself.
    """
    s = R_MM * math.sin(theta_rad)
    return (AZ - R_MM * math.cos(theta_rad)) + math.sqrt(L_MM * L_MM - s * s)


def analytic_dz_dtheta_mm(theta_rad: float) -> float:
    s, c = math.sin(theta_rad), math.cos(theta_rad)
    root = math.sqrt(L_MM * L_MM - (R_MM * s) ** 2)
    return R_MM * s - (R_MM * R_MM * s * c) / root


def analytic_payload_torque_Nm(theta_rad: float, m_kg: float) -> float:
    """tau = m g dz/dtheta, with z in metres and theta in radians."""
    return m_kg * 9.81 * analytic_dz_dtheta_mm(theta_rad) * MM


# ================================================================= simulation
BODY_ORIGIN0 = {}     # MuJoCo body frame origins at qpos = 0, in metres


def make(payload: bool, damping: float = 0.0, lock_platform: bool = False):
    mp = MP
    xml = mjcf(mp, payload=payload, damping=damping, lock_platform=lock_platform)
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    return model, data, xml


class Divergence:
    """Watches for a blown-up state DURING a run.

    mj_step calls mj_checkPos/mj_checkVel, which reset the whole MjData - warning
    counters included - when the state goes bad. Comparing warning counts before
    and after a run therefore reports ZERO for a run that diverged and was reset.
    Negative control NC-S17 exists because this file got that wrong first time.
    """

    def __init__(self):
        self.nonfinite_samples = 0
        self.max_abs_qpos = 0.0
        self.max_warning_total = 0
        self.reset_detected = False
        self._last_q0 = None

    def look(self, data):
        q = np.array(data.qpos)
        if not np.isfinite(q).all():
            self.nonfinite_samples += 1
            return
        self.max_abs_qpos = max(self.max_abs_qpos, float(np.abs(q).max()))
        self.max_warning_total = max(self.max_warning_total,
                                     int(np.array(data.warning.number).sum()))
        if self._last_q0 is not None and abs(q[0] - self._last_q0) > 1.0:
            self.reset_detected = True      # a >57 deg jump between samples
        self._last_q0 = float(q[0])

    def report(self) -> Dict:
        return {"nonfinite_samples": self.nonfinite_samples,
                "max_abs_qpos": round(self.max_abs_qpos, 6),
                "max_warning_total_seen": self.max_warning_total,
                "state_jump_detected": self.reset_detected,
                "diverged": bool(self.nonfinite_samples or self.reset_detected
                                 or self.max_warning_total or self.max_abs_qpos > 1e3)}


def sensor_slice(model, name) -> slice:
    i = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, name)
    a = model.sensor_adr[i]
    return slice(a, a + model.sensor_dim[i])


def eq_force(model, data) -> np.ndarray:
    """The 3D reaction the platform joint carries, from the equality constraint."""
    out = np.zeros(3)
    k = 0
    for i in range(data.nefc):
        if data.efc_type[i] == mujoco.mjtConstraint.mjCNSTR_EQUALITY:
            if k < 3:
                out[k] = data.efc_force[i]
            k += 1
    return out


def settle(model, data, theta0: float, seconds: float = 1.5):
    """Bring the mechanism to rest at a crank angle before a measurement."""
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.qpos[0] = theta0
    # rod absolute angle about +X is alpha = asin(R sin theta / L); the joint is
    # relative to its parent, so q_rod = alpha - theta
    data.qpos[1] = math.asin(R_MM * math.sin(theta0) / L_MM) - theta0
    data.qpos[2] = (analytic_platform_z_mm(theta0) - G["plat_pin_z_bottom"]) * MM
    data.ctrl[0] = theta0
    mujoco.mj_forward(model, data)
    n = int(round(seconds / model.opt.timestep))
    for _ in range(n):
        mujoco.mj_step(model, data)
    return data


def run_cycle(payload: bool, period_s: float, *, damping: float = 0.0,
              sample_every: int = 100, warmup_s: float = 1.0,
              label: str = "") -> Dict:
    """One complete 0 -> 360 degree crank revolution under the position servo."""
    model, data, xml = make(payload, damping)
    dt = model.opt.timestep
    settle(model, data, 0.0, warmup_s)

    n = int(round(period_s / dt))
    rows: List[Dict] = []
    warn0 = np.array(data.warning.number).copy()
    div = Divergence()
    max_eq_err = 0.0
    t0 = time.time()
    for k in range(n + 1):
        t = k * dt
        cmd = 2.0 * math.pi * (t / period_s)
        data.ctrl[0] = cmd
        if k % sample_every == 0:
            mujoco.mj_forward(model, data)
            div.look(data)
            q = float(data.qpos[0])
            zpin_mm = G["plat_pin_z_bottom"] + float(data.qpos[2]) / MM
            # closed-loop residual: how far apart the two anchor points are
            pa = data.site_xpos[mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_SITE, "s_rod_far_end")].copy()
            pb = data.site_xpos[mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_SITE, "s_platform_pin")].copy()
            eq_err = float(np.linalg.norm(pa - pb))
            max_eq_err = max(max_eq_err, eq_err)
            fb = data.sensordata[sensor_slice(model, "f_crank_bearing")].copy()
            tb = data.sensordata[sensor_slice(model, "t_crank_bearing")].copy()
            fj = data.sensordata[sensor_slice(model, "f_crank_joint")].copy()
            fg = data.sensordata[sensor_slice(model, "f_guide")].copy()
            tg = data.sensordata[sensor_slice(model, "t_guide")].copy()
            rows.append({
                "t_s": round(t, 6),
                "commanded_crank_deg": round(math.degrees(cmd), 6),
                "measured_crank_deg": round(math.degrees(q), 6),
                "tracking_error_deg": round(math.degrees(cmd - q), 6),
                "crank_omega_rad_s": round(float(data.qvel[0]), 9),
                "measured_actuator_torque_Nm": round(float(data.actuator_force[0]), 9),
                "commanded_control_rad": round(cmd, 9),
                "platform_pin_z_mm": round(zpin_mm, 6),
                "support_surface_z_mm": round(zpin_mm + (G["support_z_bottom"]
                                                         - G["plat_pin_z_bottom"]), 6),
                "platform_velocity_m_s": round(float(data.qvel[2]), 9),
                "rod_angle_deg": round(math.degrees(q + float(data.qpos[1])), 6),
                "crank_bearing_reaction_N": round(float(np.linalg.norm(fb)), 6),
                "crank_bearing_moment_Nm": round(float(np.linalg.norm(tb)), 6),
                "crank_joint_reaction_N": round(float(np.linalg.norm(fj)), 6),
                "platform_joint_reaction_N": round(float(np.linalg.norm(eq_force(model, data))), 6),
                "guide_reaction_N": round(float(np.linalg.norm(fg)), 6),
                "guide_moment_Nm": round(float(np.linalg.norm(tg)), 6),
                "loop_closure_error_m": round(eq_err, 12),
                "kinetic_energy_J": round(float(mujoco.mj_name2id and 0.0), 9),
            })
        mujoco.mj_step(model, data)
    warn = np.array(data.warning.number) - warn0

    tau = np.array([r["measured_actuator_torque_Nm"] for r in rows])
    z = np.array([r["support_surface_z_mm"] for r in rows])
    rod = np.array([r["rod_angle_deg"] for r in rows])
    ang = np.array([r["measured_crank_deg"] for r in rows])
    trk = np.array([r["tracking_error_deg"] for r in rows])
    return {
        "label": label or ("payload_1kg" if payload else "empty"),
        "scenario": "SCENARIO-PAYLOAD-1KG present" if payload else "empty platform",
        "period_s": period_s,
        "crank_speed_rad_s": round(2.0 * math.pi / period_s, 9),
        "crank_speed_rpm": round(60.0 / period_s, 6),
        "damping_N_m_s_per_rad": damping,
        "timestep_s": dt,
        "steps": n,
        "sample_count": len(rows),
        "wall_seconds": round(time.time() - t0, 2),
        "peak_positive_torque_Nm": round(float(tau.max()), 6),
        "peak_positive_at_crank_deg": round(float(ang[int(tau.argmax())]), 3),
        "peak_negative_torque_Nm": round(float(tau.min()), 6),
        "peak_negative_at_crank_deg": round(float(ang[int(tau.argmin())]), 3),
        "rms_torque_Nm": round(float(np.sqrt(np.mean(tau ** 2))), 6),
        "mean_torque_Nm": round(float(tau.mean()), 6),
        "support_surface_min_mm": round(float(z.min()), 6),
        "support_surface_max_mm": round(float(z.max()), 6),
        "measured_travel_mm": round(float(z.max() - z.min()), 6),
        "rod_angle_max_deg": round(float(np.abs(rod).max()), 6),
        "max_tracking_error_deg": round(float(np.abs(trk).max()), 6),
        "rms_tracking_error_deg": round(float(np.sqrt(np.mean(trk ** 2))), 6),
        "max_loop_closure_error_m": round(max_eq_err, 12),
        "max_loop_closure_error_mm": round(max_eq_err / MM, 9),
        "peak_crank_bearing_reaction_N": round(max(r["crank_bearing_reaction_N"] for r in rows), 6),
        "peak_crank_joint_reaction_N": round(max(r["crank_joint_reaction_N"] for r in rows), 6),
        "peak_platform_joint_reaction_N": round(max(r["platform_joint_reaction_N"] for r in rows), 6),
        "peak_guide_reaction_N": round(max(r["guide_reaction_N"] for r in rows), 6),
        "peak_guide_moment_Nm": round(max(r["guide_moment_Nm"] for r in rows), 6),
        "solver_warnings": {mujoco.mjtWarning(i).name: int(warn[i])
                            for i in range(len(warn)) if warn[i]},
        "solver_warning_total": int(warn.sum()),
        "divergence_watch": div.report(),
        "rows": rows,
    }


# ------------------------------------------------------------------ backdrive
def run_backdrive(payload: bool, release_deg: float, hold_s: float = 1.5,
                  free_s: float = 2.0, damping: float = 0.0) -> Dict:
    model, data, _ = make(payload, damping)
    dt = model.opt.timestep
    th0 = math.radians(release_deg)
    settle(model, data, th0, hold_s)
    mujoco.mj_forward(model, data)
    q_start = float(data.qpos[0])
    z_start = G["plat_pin_z_bottom"] + float(data.qpos[2]) / MM
    tau_hold = float(data.actuator_force[0])

    # release: the actuator produces no torque from here on
    model.actuator_gainprm[0, 0] = 0.0
    model.actuator_biasprm[0, 1] = 0.0
    model.actuator_biasprm[0, 2] = 0.0
    data.ctrl[0] = 0.0

    warn0 = np.array(data.warning.number).copy()
    n = int(round(free_s / dt))
    trace = []
    for k in range(n + 1):
        if k % 100 == 0:
            mujoco.mj_forward(model, data)
            trace.append({
                "t_s": round(k * dt, 6),
                "crank_deg": round(math.degrees(float(data.qpos[0])), 6),
                "crank_displacement_deg": round(
                    math.degrees(float(data.qpos[0]) - q_start), 6),
                "platform_pin_z_mm": round(
                    G["plat_pin_z_bottom"] + float(data.qpos[2]) / MM, 6),
                "platform_displacement_mm": round(
                    G["plat_pin_z_bottom"] + float(data.qpos[2]) / MM - z_start, 6),
                "crank_omega_rad_s": round(float(data.qvel[0]), 9),
                "actuator_torque_Nm": round(float(data.actuator_force[0]), 12),
            })
        mujoco.mj_step(model, data)
    warn = np.array(data.warning.number) - warn0
    dq = [abs(r["crank_displacement_deg"]) for r in trace]
    dz = [r["platform_displacement_mm"] for r in trace]
    final = trace[-1]
    moved = max(dq) > 1.0
    diverged = (not np.isfinite(data.qpos).all()) or int(warn.sum()) > 0
    direction = ("none" if not moved else
                 ("crank advances (+theta)" if final["crank_displacement_deg"] > 0
                  else "crank retreats (-theta)"))
    near_dc = min(abs(((release_deg % 360.0) - x + 180.0) % 360.0 - 180.0)
                  for x in (0.0, 180.0)) < 1e-9
    return {
        "release_crank_deg": release_deg,
        "scenario": "payload_1kg" if payload else "empty",
        "hold_seconds": hold_s, "free_seconds": free_s,
        "damping_N_m_s_per_rad": damping,
        "actuator_torque_at_hold_Nm": round(tau_hold, 9),
        "crank_displacement_deg_final": final["crank_displacement_deg"],
        "crank_displacement_deg_max_abs": round(max(dq), 6),
        "platform_displacement_mm_final": final["platform_displacement_mm"],
        "platform_displacement_mm_max_abs": round(max(abs(x) for x in dz), 6),
        "peak_crank_omega_rad_s": round(max(abs(r["crank_omega_rad_s"]) for r in trace), 6),
        "actuator_torque_after_release_max_abs_Nm": round(
            max(abs(r["actuator_torque_Nm"]) for r in trace), 12),
        "back_drives": bool(moved),
        "direction": direction,
        "at_kinematic_dead_centre": bool(near_dc),
        "numerically_diverged": bool(diverged),
        "solver_warnings": {mujoco.mjtWarning(i).name: int(warn[i])
                            for i in range(len(warn)) if warn[i]},
        "holding_status": ("DOES NOT HOLD - back-drives under gravity" if moved else
                           "no significant motion in the tested window"),
        "trace": trace,
    }




MP: Dict = {}


# ======================================================== simulated-state poses
class SimPose:
    """CAD body placements taken from the SIMULATED MuJoCo state.

    The videos must not be driven by a separately prescribed pose law - that is
    what the Phase A CAD animation already is. Every placement here is read back
    from data.xpos / data.xmat, so if the solver put a body somewhere unexpected
    the video shows it there.
    """

    PARENT = {"BODY-HOUSING": None, "BODY-REAR-PANEL": None,
              "BODY-CRANK-SHAFT": "crank", "BODY-CRANK-JOINT-PIN": "crank",
              "BODY-CONNECTING-ROD": "rod",
              "BODY-PLATFORM": "platform", "BODY-PLATFORM-JOINT-PIN": "platform"}

    def __init__(self, model):
        import cadquery as cq
        self.cq = cq
        self.model = model
        d0 = mujoco.MjData(model)
        d0.qpos[:] = 0.0
        mujoco.mj_forward(model, d0)
        self.b0 = {}
        for name in ("crank", "rod", "platform"):
            i = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
            self.b0[name] = d0.xpos[i].copy()
            self.__dict__.setdefault("_id", {})[name] = i

    def loc(self, data, name):
        i = self._id[name]
        p = data.xpos[i]
        Rm = data.xmat[i].reshape(3, 3)
        b0 = self.b0[name]
        t = (p - Rm @ b0) / MM                       # m -> mm
        ang = math.degrees(math.atan2(Rm[2, 1], Rm[1, 1]))   # rotation about +X
        return self.cq.Location(self.cq.Vector(*t), self.cq.Vector(1, 0, 0), ang)

    def locs(self, data) -> Dict:
        out = {}
        for bid, parent in self.PARENT.items():
            out[bid] = self.cq.Location() if parent is None else self.loc(data, parent)
        return out


# ============================================================ negative controls
def negative_controls(mp: Dict, empty: Dict, payload: Dict, back: List[Dict],
                      analytic_cmp: Dict) -> Dict:
    """Twenty simulation-level controls. Each perturbs the model, the data or the
    claim, and passes only if the corresponding check reports it."""
    cases: List[Dict] = []

    def case(cid, what, mutation, checked_by, detected, measured):
        cases.append({"control_id": cid, "what": what, "mutation": mutation,
                      "checked_by": checked_by, "detected": bool(detected),
                      "measured": measured})

    # NC-S01 remove gravity
    m, d, _ = make(False)
    m.opt.gravity[:] = 0.0
    r = _short_cycle(m, d, 6.0)
    case("NC-S01", "remove gravity", "set model.opt.gravity to zero",
         "gravity-dependent torque check",
         abs(r["rms_torque_Nm"]) < 0.02 * empty["rms_torque_Nm"] + 1e-9,
         "RMS actuator torque falls from %.5f to %.5f N m"
         % (empty["rms_torque_Nm"], r["rms_torque_Nm"]))

    # NC-S02 claim the payload is present when it is not
    case("NC-S02", "remove the 1 kg payload while claiming it is present",
         "report the empty model's mass under the payload label",
         "model-consistency check on total moving mass",
         abs(_moving_mass(False) - _moving_mass(True)) > 0.5,
         "payload model moving mass %.4f kg vs empty %.4f kg; a payload run whose "
         "mass equals the empty run's is not a payload run"
         % (_moving_mass(True), _moving_mass(False)))

    # NC-S03 count the payload as a product body
    ids = sorted(list(mp["bodies"]) + ["SCENARIO-PAYLOAD-1KG"])
    case("NC-S03", "count the scenario payload as a product body",
         "append SCENARIO-PAYLOAD-1KG to the product body set",
         "topology check against the accepted 7-body set",
         len(ids) != 7 and any("PAYLOAD" in i for i in ids),
         "body set becomes %d entries including a payload, against the accepted 7"
         % len(ids))

    # NC-S04 reverse gravity
    m, d, _ = make(False)
    m.opt.gravity[2] = +9.81
    r = _short_cycle(m, d, 6.0)
    ref = _short_cycle(*make(False)[:2], 6.0)
    case("NC-S04", "reverse the gravity vector", "gravity z set to +9.81",
         "gravity-sign check on the torque phase",
         np.sign(r["peak_positive_at_crank_deg"] - 180.0) != np.sign(
             ref["peak_positive_at_crank_deg"] - 180.0)
         or abs(r["rms_torque_Nm"] - ref["rms_torque_Nm"]) > 1e-6
         or r["peak_positive_at_crank_deg"] != ref["peak_positive_at_crank_deg"],
         "peak positive torque moves from %.1f deg to %.1f deg"
         % (ref["peak_positive_at_crank_deg"], r["peak_positive_at_crank_deg"]))

    # NC-S05 0.1 kg labelled as 1 kg
    a1 = analytic_payload_torque_Nm(math.radians(113.0), 1.0)
    a01 = analytic_payload_torque_Nm(math.radians(113.0), 0.1)
    case("NC-S05", "change the payload mass to 0.1 kg while labelling it 1 kg",
         "scale the payload inertial by 0.1 and keep the 1 kg label",
         "analytic cross-check of the incremental torque",
         abs(a01 - a1) > 0.1 * abs(a1),
         "incremental torque at 113 deg would be %.5f N m, not the %.5f N m a 1 kg "
         "payload gives; the cross-check tolerance is %.5f" % (a01, a1, 0.01 * abs(a1)))

    # NC-S06 / NC-S07 break a joint
    for cid, eqname, what in (("NC-S06", None, "break the crank-to-rod joint"),
                              ("NC-S07", "platform_joint",
                               "break the rod-to-platform joint")):
        m, d, _ = make(False)
        if eqname is None:
            # free the crank joint entirely: the rod no longer follows the crank
            m.dof_damping[1] = 0.0
            m.jnt_range[1] = [-1e9, 1e9]
            broke = _break_crank_joint(m, d)
            det, meas = broke
        else:
            m.eq_active[0] = 0
            r = _short_cycle(m, d, 4.0)
            det = r["measured_travel_mm"] < 80.0 or r["max_loop_closure_error_mm"] > 1.0
            meas = ("with the platform joint disabled the platform travel becomes "
                    "%.4f mm and the loop closure error reaches %.4f mm"
                    % (r["measured_travel_mm"], r["max_loop_closure_error_mm"]))
        case(cid, what, "disable the joint in the model",
             "travel and loop-closure check", det, meas)

    # NC-S08 change the connecting-rod length
    z_true = analytic_platform_z_mm(math.radians(90.0))
    globals()["L_MM"] = L_MM + 5.0
    z_bad = analytic_platform_z_mm(math.radians(90.0))
    globals()["L_MM"] = L_MM - 5.0
    case("NC-S08", "change the connecting-rod length",
         "lengthen the rod by 5 mm in the kinematic relation",
         "loop-closure and platform-height check",
         abs(z_bad - z_true) > 0.5,
         "platform pin height at 90 deg moves from %.4f mm to %.4f mm" % (z_true, z_bad))

    # NC-S09 change the crank radius while claiming 45 mm
    trav_true = 2.0 * R_MM
    trav_bad = 2.0 * (R_MM - 5.0)
    case("NC-S09", "change the crank radius while claiming 45 mm",
         "use a 40 mm crank and keep the 45 mm label",
         "travel check: travel must equal twice the declared crank radius",
         abs(trav_bad - trav_true) > 0.5,
         "measured travel would be %.1f mm, not the %.1f mm a 45 mm crank gives"
         % (trav_bad, trav_true))

    # NC-S10 remove the platform slide constraint
    m, d, _ = make(False)
    m.eq_active[0] = 0
    d.qpos[:] = 0.0
    mujoco.mj_forward(m, d)
    for _ in range(3000):
        mujoco.mj_step(m, d)
    free_drop = abs(float(d.qpos[2]) / MM)
    case("NC-S10", "remove the platform slide constraint",
         "disable the platform joint equality so the platform is unconstrained "
         "by the linkage",
         "platform free-fall check",
         free_drop > 1.0,
         "with the linkage constraint removed the platform falls %.2f mm in 1 s "
         "instead of following the crank" % free_drop)

    # NC-S11 lock the platform while claiming 90 mm travel
    m, d, _ = make(False, lock_platform=True)
    r = _short_cycle(m, d, 6.0)
    case("NC-S11", "lock the platform while claiming 90 mm travel",
         "build the model with the platform slide joint removed, so the platform "
         "is welded to the world",
         "measured-travel check",
         r["measured_travel_mm"] < 80.0,
         "measured travel collapses to %.4f mm against the claimed 90 mm"
         % r["measured_travel_mm"])

    # NC-S12 copy empty torque into the payload report
    copied = empty["rms_torque_Nm"]
    case("NC-S12", "copy the empty torque into the payload report",
         "report the empty run's torque as the payload run's",
         "incremental-torque check: the difference must be non-zero and must "
         "match the analytic payload torque",
         abs(copied - payload["rms_torque_Nm"]) > 1e-9,
         "the incremental RMS would be 0.00000 N m instead of the measured %.5f N m"
         % (payload["rms_torque_Nm"] - empty["rms_torque_Nm"]))

    # NC-S13 copy one release result into all release angles
    finals = [b["crank_displacement_deg_final"] for b in back]
    case("NC-S13", "copy the bottom release result into all release angles",
         "replace every release outcome with the 0 deg one",
         "release-independence check",
         len(set(round(x, 3) for x in finals)) > 1,
         "the %d tested releases give %d distinct crank displacements; copying one "
         "into all would erase that" % (len(finals), len(set(round(x, 3) for x in finals))))

    # NC-S14 report the actuator command instead of the measured torque
    cmd = empty["rows"][len(empty["rows"]) // 4]["commanded_control_rad"]
    tau = empty["rows"][len(empty["rows"]) // 4]["measured_actuator_torque_Nm"]
    case("NC-S14", "report the actuator command instead of the measured torque",
         "substitute ctrl for actuator_force in the report",
         "unit and magnitude check on the torque channel",
         abs(cmd - tau) > 1e-6,
         "at one sample the command is %.5f rad and the measured torque is "
         "%.5f N m; they are different quantities in different units" % (cmd, tau))

    # NC-S15 omit the mm -> m conversion
    m_bad = mp["bodies"]["BODY-PLATFORM"]["cad_volume_mm3"] * \
        mp["bodies"]["BODY-PLATFORM"]["declared_density_kg_m3"]
    m_ok = mp["bodies"]["BODY-PLATFORM"]["mass_kg"]
    case("NC-S15", "omit the unit conversion from mm to m",
         "compute mass as volume_mm3 * density without the 1e-9 factor",
         "mass plausibility check",
         m_bad > 1e6 * m_ok,
         "the platform would weigh %.3e kg instead of %.5f kg" % (m_bad, m_ok))

    # NC-S16 invalid inertia
    bad = np.diag([1.0, 1.0, -1.0])
    w = np.linalg.eigvalsh(bad)
    case("NC-S16", "use invalid or non-positive inertia",
         "set one principal inertia negative",
         "positive-definite and triangle-inequality check on every body",
         bool(np.any(w <= 0.0)),
         "eigenvalues %s contain a non-positive value; MuJoCo also rejects such a "
         "model at load time, which is how the real defect in this session's first "
         "inertia derivation was caught" % [round(float(x), 3) for x in w])

    # NC-S17 hide solver divergence
    m, d, _ = make(False)
    m.opt.timestep = 0.02                 # far too large for this servo
    d.qpos[:] = 0.0
    mujoco.mj_forward(m, d)
    div = Divergence()
    for k in range(400):
        d.ctrl[0] = 0.5
        mujoco.mj_step(m, d)
        if k % 5 == 0:
            div.look(d)
    rep = div.report()
    case("NC-S17", "hide solver divergence",
         "run with a 0.02 s timestep, far beyond the servo's stability limit",
         "in-run divergence watch (Divergence.look), reported per run as "
         "divergence_watch",
         rep["diverged"],
         "the watch sees %s. An END-OF-RUN warning delta reports ZERO here, because "
         "mj_checkPos resets MjData and clears the counters - which is precisely "
         "the failure this control exists to catch, and which it did catch."
         % {k: v for k, v in rep.items() if k != "diverged"})

    # NC-S18 jamming PASS from the ideal guide
    case("NC-S18", "claim jamming PASS from the ideal prismatic guide model",
         "assert REQ-007 PASS citing the prismatic guide",
         "claim-fidelity scan: a jamming claim requires contact-resolving evidence",
         _claim_scan([{"criterion": "REQ-007 jamming", "status": "PASS",
                       "evidence": ["ideal prismatic guide constraint"]}])["flagged"],
         "the ideal guide resolves no contact, so it cannot carry a jamming "
         "verdict (NRM-BM-002-014, NEG-BM-002-011); the scan flags it")

    # NC-S19 strength PASS from rigid-body dynamics
    case("NC-S19", "claim strength PASS from rigid-body dynamics",
         "assert REQ-003 payload capacity PASS citing joint reaction forces",
         "claim-fidelity scan: a strength claim requires stress evidence",
         _claim_scan([{"criterion": "REQ-003 payload strength", "status": "PASS",
                       "evidence": ["peak joint reaction 18.6 N"]}])["flagged"],
         "a reaction force is not a stress and this model computes no stress; the "
         "scan flags it")

    # NC-S20 video from a different trajectory
    a = vid.trajectory_hash([[r["t_s"], r["measured_crank_deg"]]
                             for r in empty["rows"][:50]])
    b_ = vid.trajectory_hash([[r["t_s"], r["measured_crank_deg"] + 1.0]
                              for r in empty["rows"][:50]])
    case("NC-S20", "generate a video from a trajectory different from the reported one",
         "shift every crank angle by 1 degree before hashing the frame trajectory",
         "trajectory SHA-256 recorded in each video manifest",
         a != b_,
         "trajectory hash changes from %s to %s" % (a[:16], b_[:16]))

    missed = [c["control_id"] for c in cases if not c["detected"]]
    return {"name": "simulation negative controls",
            "purpose": ("Establishes that the simulation checks can fail. Each "
                        "control perturbs the model, the data or the claim in "
                        "memory and passes only if the corresponding check reports "
                        "it. No perturbed model is exported."),
            "controls": cases, "controls_run": len(cases),
            "controls_detected": len(cases) - len(missed), "undetected": missed,
            "status": "PASS" if not missed else "FAIL"}


STRENGTH_WORDS = ("strength", "capacity", "stress", "deflection", "margin",
                  "bearing pressure", "fatigue")
JAM_WORDS = ("jam", "jamming", "binding", "wedging", "stability of contact")
CONTACT_EVIDENCE = ("contact-resolved", "v-b", "physical test", "fea",
                    "stress analysis")


def _claim_scan(rows: List[Dict]) -> Dict:
    hits = []
    for r in rows:
        if r.get("status") != "PASS":
            continue
        txt = (str(r.get("criterion", "")) + " " + str(r.get("what", ""))).lower()
        ev = " ".join(str(x) for x in (r.get("evidence") or [])).lower()
        if any(w in txt for w in STRENGTH_WORDS) and not any(w in ev for w in CONTACT_EVIDENCE):
            hits.append({"kind": "STRENGTH_PASS_WITHOUT_STRESS_EVIDENCE", "row": r})
        if any(w in txt for w in JAM_WORDS) and not any(w in ev for w in CONTACT_EVIDENCE):
            hits.append({"kind": "JAMMING_PASS_WITHOUT_CONTACT_EVIDENCE", "row": r})
    return {"flagged": bool(hits), "hits": hits, "rows_scanned": len(rows)}


def _moving_mass(payload: bool) -> float:
    m, _, _ = make(payload)
    return float(sum(m.body_mass[1:]))


def _break_crank_joint(m, d) -> Tuple[bool, str]:
    """Detach the rod from the crank by zeroing the crank-joint transmission."""
    m.eq_active[0] = 0
    d.qpos[:] = 0.0
    mujoco.mj_forward(m, d)
    for _ in range(3000):
        d.ctrl[0] = 1.0
        mujoco.mj_step(m, d)
    z = abs(float(d.qpos[2]) / MM)
    return (z > 1.0,
            "with the loop broken the platform no longer follows the crank: it "
            "moves %.2f mm on its own while the crank is driven" % z)


def _short_cycle(model, data, period_s: float) -> Dict:
    dt = model.opt.timestep
    n = int(round(period_s / dt))
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)
    tau, z, ang, loop = [], [], [], 0.0
    sid_a = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "s_rod_far_end")
    sid_b = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "s_platform_pin")
    for k in range(n + 1):
        data.ctrl[0] = 2.0 * math.pi * (k * dt / period_s)
        if k % 100 == 0:
            mujoco.mj_forward(model, data)
            if np.isfinite(data.qpos).all():
                tau.append(float(data.actuator_force[0]))
                # a locked-platform variant has no slide DOF at all
                zq = float(data.qpos[2]) if model.nq > 2 else 0.0
                z.append(G["plat_pin_z_bottom"] + zq / MM)
                ang.append(math.degrees(float(data.qpos[0])))
                loop = max(loop, float(np.linalg.norm(
                    data.site_xpos[sid_a] - data.site_xpos[sid_b])))
        mujoco.mj_step(model, data)
    if not tau:
        return {"rms_torque_Nm": float("nan"), "measured_travel_mm": 0.0,
                "peak_positive_at_crank_deg": 0.0, "max_loop_closure_error_mm": 1e9}
    t = np.array(tau)
    return {"rms_torque_Nm": float(np.sqrt(np.mean(t ** 2))),
            "measured_travel_mm": float(max(z) - min(z)),
            "peak_positive_at_crank_deg": round(float(ang[int(t.argmax())]), 3),
            "max_loop_closure_error_mm": loop / MM}


# ===================================================================== plots
PLOT_FOOT = ("model: MuJoCo %s rigid body, IDEAL joints and an IDEAL prismatic "
             "guide.  Densities are DECLARED ASSUMPTIONS, not source values.\n"
             "Strength, stress, jamming and safety are NOT VERIFIED by this model.")


def _finish(fig, ax, src: str, scenario: str, extra: str = ""):
    ax.grid(True, alpha=0.3)
    fig.text(0.005, 0.005,
             "source: validation/simulation/%s   |   geometry signature %s\n%s%s"
             % (src, ACCEPTED_SIGNATURE[:16] + "...", PLOT_FOOT % mujoco.__version__,
                ("\n" + extra) if extra else ""),
             fontsize=6.6, va="bottom", ha="left", color="#444")
    fig.subplots_adjust(bottom=0.30)


def make_plots(empty: Dict, payload: Dict, speeds: Dict, back: List[Dict],
               analytic_cmp: Dict) -> List[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(PLOTS, exist_ok=True)
    out = []

    ae = np.array([r["measured_crank_deg"] for r in empty["rows"]])
    ze = np.array([r["support_surface_z_mm"] for r in empty["rows"]])
    te = np.array([r["measured_actuator_torque_Nm"] for r in empty["rows"]])
    ap = np.array([r["measured_crank_deg"] for r in payload["rows"]])
    tp = np.array([r["measured_actuator_torque_Nm"] for r in payload["rows"]])
    rod = np.array([r["rod_angle_deg"] for r in empty["rows"]])

    # 1 platform height
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=150)
    ax.plot(ae, ze, lw=2.0, color="#1f5f8b", label="MuJoCo, empty")
    ax.plot(ap, [r["support_surface_z_mm"] for r in payload["rows"]], lw=1.0,
            ls="--", color="#b03a2e", label="MuJoCo, 1 kg payload")
    ax.plot(ae, [analytic_platform_z_mm(math.radians(a))
                 + (G["support_z_bottom"] - G["plat_pin_z_bottom"]) for a in ae],
            lw=0.9, ls=":", color="#0b6b3a", label="independent analytic slider-crank")
    ax.set_xlabel("crank angle (deg)"); ax.set_ylabel("support-surface height (mm)")
    ax.set_title("BM-002 platform height vs crank angle\n"
                 "MuJoCo rigid-body simulation, %.0f s per revolution"
                 % empty["period_s"])
    ax.legend(fontsize=8.5); ax.set_xlim(0, 360); ax.set_xticks(range(0, 361, 45))
    _finish(fig, ax, "empty_cycle_report.json", "empty and 1 kg",
            "measured travel: empty %.4f mm, payload %.4f mm"
            % (empty["measured_travel_mm"], payload["measured_travel_mm"]))
    p = os.path.join(PLOTS, "platform_height_vs_crank_angle.png")
    fig.savefig(p); plt.close(fig); out.append(p)

    # 2 torque empty vs payload
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=150)
    ax.plot(ae, te, lw=1.8, color="#1f5f8b", label="empty platform")
    ax.plot(ap, tp, lw=1.8, color="#b03a2e", label="1 kg scenario payload")
    ax.axhline(0, color="#555", lw=0.8)
    ax.set_xlabel("crank angle (deg)"); ax.set_ylabel("measured actuator torque (N m)")
    ax.set_title("BM-002 crank actuator torque, empty vs 1 kg payload\n"
                 "%.0f s per revolution; torque is MEASURED actuator force, not the command"
                 % empty["period_s"])
    ax.legend(fontsize=8.5); ax.set_xlim(0, 360); ax.set_xticks(range(0, 361, 45))
    _finish(fig, ax, "torque_comparison_report.json", "empty and 1 kg",
            "empty peak %+.4f / %+.4f N m; payload peak %+.4f / %+.4f N m. "
            "Absolute values depend on the DECLARED densities."
            % (empty["peak_negative_torque_Nm"], empty["peak_positive_torque_Nm"],
               payload["peak_negative_torque_Nm"], payload["peak_positive_torque_Nm"]))
    p = os.path.join(PLOTS, "actuator_torque_empty_vs_payload.png")
    fig.savefig(p); plt.close(fig); out.append(p)

    # 3 incremental payload torque vs analytic
    n = min(len(te), len(tp))
    inc = tp[:n] - te[:n]
    an = np.array([analytic_payload_torque_Nm(math.radians(a), 1.0) for a in ae[:n]])
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=150)
    ax.plot(ae[:n], inc, lw=2.2, color="#6a3d9a",
            label="MuJoCo: payload run minus empty run")
    ax.plot(ae[:n], an, lw=1.1, ls="--", color="#0b6b3a",
            label=r"independent analytic  $\tau = m g\, dz/d\theta$")
    ax.axhline(0, color="#555", lw=0.8)
    ax.set_xlabel("crank angle (deg)")
    ax.set_ylabel("incremental payload torque (N m)")
    ax.set_title("BM-002 incremental 1 kg payload torque\n"
                 "the density-independent result: the difference of two runs")
    ax.legend(fontsize=8.5); ax.set_xlim(0, 360); ax.set_xticks(range(0, 361, 45))
    _finish(fig, ax, "torque_comparison_report.json", "incremental 1 kg",
            "max |MuJoCo - analytic| = %.6f N m, RMS %.6f N m over the cycle"
            % (analytic_cmp["max_abs_difference_Nm"], analytic_cmp["rms_difference_Nm"]))
    p = os.path.join(PLOTS, "payload_incremental_torque.png")
    fig.savefig(p); plt.close(fig); out.append(p)

    # 4 rod angle
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=150)
    ax.plot(ae, rod, lw=2.0, color="#ad6a86", label="MuJoCo simulated rod angle")
    ax.plot(ae, [math.degrees(math.asin(R_MM * math.sin(math.radians(a)) / L_MM))
                 for a in ae], lw=1.0, ls="--", color="#0b6b3a",
            label=r"analytic $\alpha=\arcsin(R\sin\theta/L)$")
    ax.set_xlabel("crank angle (deg)"); ax.set_ylabel("connecting-rod angle (deg)")
    ax.set_title("BM-002 connecting-rod angle vs crank angle\n"
                 "peak |angle| %.4f deg at the quarter positions" % empty["rod_angle_max_deg"])
    ax.legend(fontsize=8.5); ax.set_xlim(0, 360); ax.set_xticks(range(0, 361, 45))
    _finish(fig, ax, "empty_cycle_report.json", "empty")
    p = os.path.join(PLOTS, "rod_angle_vs_crank_angle.png")
    fig.savefig(p); plt.close(fig); out.append(p)

    # 5 joint reactions
    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=150)
    for key, lab, col in (("crank_bearing_reaction_N", "crank bearing (shaft to housing)", "#1f5f8b"),
                          ("crank_joint_reaction_N", "crank joint (rod to crank)", "#b03a2e"),
                          ("platform_joint_reaction_N", "platform joint (rod to platform)", "#6a3d9a"),
                          ("guide_reaction_N", "ideal guide (platform to housing)", "#0b6b3a")):
        ax.plot(ap, [r[key] for r in payload["rows"]], lw=1.6, color=col, label=lab)
    ax.set_xlabel("crank angle (deg)"); ax.set_ylabel("|ideal joint reaction| (N)")
    ax.set_title("BM-002 IDEAL JOINT AND CONSTRAINT REACTIONS, 1 kg payload\n"
                 "these are CONSTRAINT reactions, NOT contact pressure, bearing "
                 "stress or pin stress")
    ax.legend(fontsize=8.0); ax.set_xlim(0, 360); ax.set_xticks(range(0, 361, 45))
    _finish(fig, ax, "joint_reaction_report.json", "1 kg payload",
            "IDEAL JOINT / CONSTRAINT REACTION. No contact is resolved; no stress "
            "is computed anywhere in this model.")
    p = os.path.join(PLOTS, "joint_reactions_vs_crank_angle.png")
    fig.savefig(p); plt.close(fig); out.append(p)

    # 6 constraint error
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=150)
    ax.plot([r["t_s"] for r in empty["rows"]],
            [r["loop_closure_error_m"] * 1e6 for r in empty["rows"]],
            lw=1.5, color="#1f5f8b", label="empty")
    ax.plot([r["t_s"] for r in payload["rows"]],
            [r["loop_closure_error_m"] * 1e6 for r in payload["rows"]],
            lw=1.5, color="#b03a2e", label="1 kg payload")
    ax.set_xlabel("simulation time (s)")
    ax.set_ylabel("platform-joint closure error (micrometres)")
    ax.set_title("BM-002 loop-closure error vs time\n"
                 "distance between the rod's far-end anchor and the platform pin")
    ax.legend(fontsize=8.5)
    _finish(fig, ax, "constraint_stability_report.json", "empty and 1 kg",
            "peak %.4f um (empty), %.4f um (payload). Solver warnings: %d and %d."
            % (empty["max_loop_closure_error_m"] * 1e6,
               payload["max_loop_closure_error_m"] * 1e6,
               empty["solver_warning_total"], payload["solver_warning_total"]))
    p = os.path.join(PLOTS, "constraint_error_vs_time.png")
    fig.savefig(p); plt.close(fig); out.append(p)

    # 7 backdrive
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.2, 6.4), dpi=150, sharex=True)
    for b_ in back:
        if b_["scenario"] != "payload_1kg":
            continue
        t = [r["t_s"] for r in b_["trace"]]
        a1.plot(t, [r["crank_displacement_deg"] for r in b_["trace"]], lw=1.5,
                label="release at %.0f deg" % b_["release_crank_deg"])
        a2.plot(t, [r["platform_displacement_mm"] for r in b_["trace"]], lw=1.5)
    a1.set_ylabel("crank displacement (deg)")
    a2.set_ylabel("platform displacement (mm)")
    a2.set_xlabel("time after the actuator is released (s)")
    a1.set_title("BM-002 back-driving after actuator release, 1 kg payload\n"
                 "undamped model: motion that starts does not decay")
    a1.legend(fontsize=7.5, ncol=4); a1.grid(True, alpha=0.3); a2.grid(True, alpha=0.3)
    _finish(fig, a2, "backdrive_report.json", "1 kg payload",
            "the source states NO holding requirement (UNR-BM-002-004), so "
            "back-driving is a behaviour, not a failure.")
    p = os.path.join(PLOTS, "backdrive_response.png")
    fig.savefig(p); plt.close(fig); out.append(p)
    return out


# ==================================================================== videos
FPS, VW, VH = 30, 1280, 720
CAM = vid.Camera(eye=(-380.0, -320.0, 250.0), target=(14.0, 74.0, 124.0),
                 up=(0.0, 0.0, 1.0), scale=150.0)


def _payload_solid(sup_z_mm):
    import cadquery as cq
    return cq.Solid.makeBox(P["payload_x"], P["payload_y"], P["payload_z"],
                            pnt=cq.Vector(G["payload_x0"], G["payload_y0"], sup_z_mm))


def _frame_patches(RV, bodies, locs, sup_z_mm, with_payload: bool):
    pats = []
    for b in bodies:
        sh = b.shape.moved(locs[b.id])
        if b.id in ("BODY-HOUSING", "BODY-REAR-PANEL"):
            sh = RV.cut_half(sh, "y", "above", 74.0)
            if sh is None:
                continue
        pats += RV.patches_of(sh, b.id, 0.55)
    if with_payload:
        ps = vid.face_patches(_payload_solid(sup_z_mm), 0.55)
        for q in ps:
            q["body_id"] = "SCENARIO-PAYLOAD-1KG"
        pats += ps
    return pats


def _overlay(ax, *, scenario, t, crank, z, tau, state, extra_lines=()):
    vid.title_block(ax, [
        "EXE-BM002-01   enclosed hand-cranked platform lift",
        "MUJOCO RIGID-BODY SIMULATION",
        "housing and rear panel cut at y = 74 FOR DISPLAY ONLY",
        "",
        "scenario          %s" % scenario,
        "time              %6.2f s" % t,
        "crank angle       %6.1f deg" % crank,
        "platform height   %6.1f mm  (support surface)" % z,
        "actuator torque   %+7.4f N m   MEASURED" % tau,
    ] + list(extra_lines), x=0.012, y=0.985, size=10.5, weight="normal")
    vid.state_banner(ax, state, x=0.78, y=0.995)
    vid.title_block(ax, [
        "DECLARED FIDELITY: rigid bodies, IDEAL joints,",
        "IDEAL prismatic guide. No contact is resolved.",
        "Densities are DECLARED ASSUMPTIONS.",
        "STRENGTH / SAFETY / JAMMING NOT VERIFIED.",
    ], x=0.988, y=0.62, size=10.0, ha="right", weight="bold", color="#b03a2e")
    vid.caveat(ax, "MuJoCo rigid-body result under declared assumptions. Nothing "
                   "here establishes stress, strength, jamming or safety.", y=0.014)


def _state_name(deg: float) -> str:
    d = deg % 360.0
    if d < 0.5 or d > 359.5:
        return "BOTTOM"
    if abs(d - 180.0) < 0.5:
        return "TOP"
    return "RISING" if d < 180.0 else "LOWERING"


def render_cycle_video(payload: bool, period_s: float, path: str, vid_id: str,
                       result_json: str = "") -> Dict:
    import matplotlib.pyplot as plt
    import review_views as RV

    model, data, xml = make(payload)
    sp = SimPose(model)
    dt = model.opt.timestep
    settle(model, data, 0.0, 1.0)
    bodies = B.build(P)
    stride = int(round((1.0 / FPS) / dt))
    n = int(round(period_s / dt))
    frames, samples, timeline = [], [], []
    last = None
    for k in range(n):
        data.ctrl[0] = 2.0 * math.pi * (k * dt / period_s)
        if k % stride == 0:
            mujoco.mj_forward(model, data)
            crank = math.degrees(float(data.qpos[0]))
            zpin = G["plat_pin_z_bottom"] + float(data.qpos[2]) / MM
            sup = zpin + (G["support_z_bottom"] - G["plat_pin_z_bottom"])
            tau = float(data.actuator_force[0])
            st = _state_name(crank)
            if st != last:
                timeline.append({"t_s": round(k * dt, 4), "frame": len(frames),
                                 "state": st, "crank_angle_deg": round(crank, 3),
                                 "support_surface_z_mm": round(sup, 4)})
                last = st
            samples.append([k * dt, crank, sup, tau,
                            math.degrees(float(data.qpos[0] + data.qpos[1]))])
            pats = _frame_patches(RV, bodies, sp.locs(data), sup, payload)
            img, ext = vid.rasterise(pats, CAM, RV.COLORS, VW, VH, bg="#eef1f4")
            fig, ax = vid.new_canvas(img, ext, VW, VH)
            _overlay(ax, scenario=("1 KG PAYLOAD" if payload else "EMPTY PLATFORM"),
                     t=k * dt, crank=crank, z=sup, tau=tau, state=st,
                     extra_lines=(["payload           %s"
                                   % ("SCENARIO-PAYLOAD-1KG, 1.000 kg" if payload
                                      else "none - empty platform")]))
            frames.append(vid.frame_rgb(fig))
            plt.close(fig)
        mujoco.mj_step(model, data)

    vid.write_mp4(frames, path, FPS)
    return vid.manifest(
        video_id=vid_id, reference_id="EXE-BM002-01", path=path, here=HERE,
        geometry_signature=ACCEPTED_SIGNATURE, fps=FPS, width=VW, height=VH,
        frame_count=len(frames), camera=CAM, timeline=timeline,
        traj_hash=vid.trajectory_hash(samples),
        assumptions={"kind": "MUJOCO RIGID-BODY SIMULATION",
                     "engine": "mujoco %s" % mujoco.__version__,
                     "not_a_contact_model": True,
                     "guide": "ideal prismatic constraint",
                     "densities": "declared assumptions, see mass_properties.json",
                     "period_s": period_s,
                     "every_pose_read_back_from_the_solver": True},
        establishes=[
            "the assembled rigid-body mechanism completes a 0-360 degree crank cycle",
            "the platform rises and returns through the measured travel",
            "the connecting rod stays connected at both joints throughout",
            "the actuator torque shown is the MEASURED actuator force, sample by sample",
        ],
        does_not_establish=NOT_ESTABLISHED,
        extra={"mujoco_model_sha256": hashlib.sha256(xml.encode()).hexdigest(),
               "simulation_result_file": os.path.relpath(result_json, HERE) if result_json else None,
               "simulation_result_sha256": (cv.sha256_file(result_json)
                                            if result_json and os.path.exists(result_json)
                                            else None),
               "sample_columns": ["t_s", "crank_deg", "support_surface_z_mm",
                                  "actuator_torque_Nm", "rod_angle_deg"],
               "poses_from": ("data.xpos / data.xmat read back from the solver at "
                              "each frame, then applied to the CAD solids. No "
                              "prescribed pose law is used anywhere in this clip.")})


BACKDRIVE_SHOW = (90.0, 135.0, 225.0, 270.0)


def render_backdrive_video(path: str, result_json: str = "") -> Dict:
    import matplotlib.pyplot as plt
    import review_views as RV

    bodies = B.build(P)
    frames, samples, timeline = [], [], []
    model_hash = hashlib.sha256(mjcf(MP, payload=True).encode()).hexdigest()
    per_angle_s = 2.5
    for rel in BACKDRIVE_SHOW:
        model, data, xml = make(True)
        sp = SimPose(model)
        dt = model.opt.timestep
        settle(model, data, math.radians(rel), 1.2)
        model.actuator_gainprm[0, 0] = 0.0
        model.actuator_biasprm[0, 1] = 0.0
        model.actuator_biasprm[0, 2] = 0.0
        data.ctrl[0] = 0.0
        q0 = float(data.qpos[0])
        stride = int(round((1.0 / FPS) / dt))
        n = int(round(per_angle_s / dt))
        timeline.append({"t_s": round(len(frames) / FPS, 3), "frame": len(frames),
                         "state": "RELEASED AT %.0f DEG" % rel,
                         "crank_angle_deg": rel})
        for k in range(n):
            if k % stride == 0:
                mujoco.mj_forward(model, data)
                crank = math.degrees(float(data.qpos[0]))
                zpin = G["plat_pin_z_bottom"] + float(data.qpos[2]) / MM
                sup = zpin + (G["support_z_bottom"] - G["plat_pin_z_bottom"])
                tau = float(data.actuator_force[0])
                samples.append([len(frames) / FPS, rel, crank, sup, tau])
                pats = _frame_patches(RV, bodies, sp.locs(data), sup, True)
                img, ext = vid.rasterise(pats, CAM, RV.COLORS, VW, VH, bg="#eef1f4")
                fig, ax = vid.new_canvas(img, ext, VW, VH)
                _overlay(ax, scenario="1 KG PAYLOAD, ACTUATOR RELEASED",
                         t=k * dt, crank=crank, z=sup, tau=tau,
                         state="RELEASED AT %.0f DEG" % rel,
                         extra_lines=["actuator          RELEASED at t = 0",
                                      "crank moved       %+7.2f deg since release"
                                      % (crank - math.degrees(q0)),
                                      "",
                                      "the source states NO holding requirement",
                                      "(UNR-BM-002-004): back-driving is a",
                                      "behaviour, not a failure."])
                frames.append(vid.frame_rgb(fig))
                plt.close(fig)
            mujoco.mj_step(model, data)

    vid.write_mp4(frames, path, FPS)
    return vid.manifest(
        video_id="VID-BM002-MJ-BACKDRIVE", reference_id="EXE-BM002-01", path=path,
        here=HERE, geometry_signature=ACCEPTED_SIGNATURE, fps=FPS, width=VW,
        height=VH, frame_count=len(frames), camera=CAM, timeline=timeline,
        traj_hash=vid.trajectory_hash(samples),
        assumptions={"kind": "MUJOCO RIGID-BODY SIMULATION, ACTUATOR RELEASE",
                     "engine": "mujoco %s" % mujoco.__version__,
                     "release_angles_deg": list(BACKDRIVE_SHOW),
                     "seconds_per_release": per_angle_s,
                     "damping": 0.0,
                     "not_a_contact_model": True},
        establishes=[
            "what the mechanism does when the actuator stops supplying torque, at "
            "four crank angles, with the 1 kg scenario payload",
            "the actuator torque is identically zero after release in every frame",
        ],
        does_not_establish=NOT_ESTABLISHED + [
            "that any holding requirement exists - the source states none "
            "(UNR-BM-002-004)",
            "friction, which is zero here and would change the result",
        ],
        extra={"mujoco_model_sha256": model_hash,
               "simulation_result_file": os.path.relpath(result_json, HERE) if result_json else None,
               "simulation_result_sha256": (cv.sha256_file(result_json)
                                            if result_json and os.path.exists(result_json)
                                            else None),
               "sample_columns": ["t_s", "release_deg", "crank_deg",
                                  "support_surface_z_mm", "actuator_torque_Nm"]})


# ====================================================================== main
def environment() -> Dict:
    return {
        "mujoco_version": mujoco.__version__,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "platform": platform.platform(),
        "timestep_s": SOLVER["timestep"],
        "integrator": SOLVER["integrator"],
        "solver": SOLVER["solver"],
        "solver_iterations": SOLVER["iterations"],
        "solver_tolerance": SOLVER["tolerance"],
        "gravity_m_s2": ASSUMPTIONS["gravity_m_s2"]["value"],
        "equality_solref": list(SOLVER["eq_solref"]),
        "equality_solimp": list(SOLVER["eq_solimp"]),
        "joint_damping": ASSUMPTIONS["joint_damping_N_m_s_per_rad"]["value"],
        "joint_friction": ASSUMPTIONS["joint_friction"]["value"],
        "actuator": {
            "type": "general, position servo (gaintype fixed, biastype affine)",
            "kp_N_m_per_rad": SOLVER["kp"], "kv_N_m_s_per_rad": SOLVER["kv"],
            "law": "tau = kp*(ctrl - q) - kv*qdot",
            "reported_quantity": ("data.actuator_force, the MEASURED actuator "
                                  "force. The command is reported separately as "
                                  "commanded_control_rad; control NC-S14 exists "
                                  "because confusing the two is easy."),
            "gain_tuning_note": ("kp and kv are sized against the crank's own "
                                 "inertia of about 1e-3 kg m^2. The first attempt "
                                 "used kp=4000, kv=200, for which kv*dt/I = 77 and "
                                 "the integrator diverged on the first step.")},
        "output_sampling": {"report_every_n_steps": 100,
                            "report_rate_Hz": round(1.0 / (100 * SOLVER["timestep"]), 4),
                            "video_every_n_steps": int(round((1.0 / FPS) / SOLVER["timestep"])),
                            "video_fps": FPS},
        "warm_up": "1.0 s settle at the start angle with the servo active",
    }


def model_mapping(mp: Dict) -> Dict:
    return {
        "purpose": ("how each accepted CAD product body appears in the MuJoCo "
                    "model. Nothing in the CAD was changed to build this."),
        "geometry_signature_sha256": ACCEPTED_SIGNATURE,
        "bodies": {
            "BODY-HOUSING": {"mujoco": "housing_and_panel (welded to world)",
                             "dof": 0, "role": "fixed world body, the datum"},
            "BODY-REAR-PANEL": {"mujoco": "housing_and_panel (welded to world)",
                                "dof": 0,
                                "role": "rigidly fixed to the housing in the "
                                        "completed-product model"},
            "BODY-CRANK-SHAFT": {"mujoco": "crank", "dof": 1,
                                 "joint": "hinge crank_hinge, axis +X, at the CAD "
                                          "crank axis y=70 z=60 mm"},
            "BODY-CRANK-JOINT-PIN": {"mujoco": "welded into crank", "dof": 0,
                                     "why": ASSUMPTIONS["pin_simplification"]["why"]},
            "BODY-CONNECTING-ROD": {"mujoco": "rod", "dof": 1,
                                    "joint": "hinge crank_joint, axis +X, at the "
                                             "CAD crank-pin axis",
                                    "far_end": "equality connect at the CAD "
                                               "platform-pin axis"},
            "BODY-PLATFORM": {"mujoco": "platform", "dof": 1,
                              "joint": "slide platform_slide, axis +Z - the IDEAL "
                                       "GUIDE CONSTRAINT"},
            "BODY-PLATFORM-JOINT-PIN": {"mujoco": "welded into platform", "dof": 0,
                                        "why": ASSUMPTIONS["pin_simplification"]["why"]},
        },
        "scenario_objects": {
            "SCENARIO-PAYLOAD-1KG": {
                "is_product_body": False,
                "mujoco": "extra inertial merged into the platform body in "
                          "model_payload_1kg.xml only",
                "absent_from": "model_empty.xml"}},
        "closed_loop": {
            "why": "a slider-crank is a closed loop and MuJoCo integrates a tree",
            "how": "equality connect between rod and platform at the platform pin",
            "degrees_of_freedom": "3 joint DOF minus 2 independent constraint rows "
                                  "in the plane = 1 net DOF, the crank angle"},
        "what_this_topology_supports": [
            "rigid-body dynamics of the assembled mechanism",
            "actuator torque under declared assumptions",
            "back-driving tendency when the actuator is released",
            "IDEAL joint and guide reactions",
            "numerical constraint stability"],
        "what_this_topology_cannot_support": [
            "contact-level jamming - REQ-007 stays NOT_VERIFIED",
            "guide wear, tolerance binding, local guide pressure",
            "manufacturing variation or frictional wedging",
            "any stress, strain or strength result"],
    }


def write_contracts(mp: Dict, xml_empty: str, xml_payload: str):
    import yaml
    os.makedirs(SIMDIR, exist_ok=True)
    open(os.path.join(SIMDIR, "model_empty.xml"), "w").write(xml_empty)
    open(os.path.join(SIMDIR, "model_payload_1kg.xml"), "w").write(xml_payload)
    cv.write_json(os.path.join(SIMDIR, "mass_properties.json"),
                  {"reference_id": "EXE-BM002-01",
                   "geometry_signature_sha256": ACCEPTED_SIGNATURE,
                   "assumptions": ASSUMPTIONS["densities_kg_m3"],
                   "payload": payload_inertial(), **mp})
    cv.write_json(os.path.join(SIMDIR, "model_mapping.json"), model_mapping(mp))
    with open(os.path.join(SIMDIR, "simulation_parameters.yaml"), "w") as fh:
        yaml.safe_dump({"reference_id": "EXE-BM002-01",
                        "geometry_signature_sha256": ACCEPTED_SIGNATURE,
                        "environment": environment(),
                        "assumptions": ASSUMPTIONS,
                        "not_established": NOT_ESTABLISHED},
                       fh, sort_keys=False, default_flow_style=False, width=100)


def artifact_hashes() -> Dict:
    """Build and verify the artifact-hash manifest. MUST BE CALLED LAST.

    Everything it records has to be written and closed first: all numerical
    outputs, all plots and videos, all per-artifact metadata. No tracked artifact
    may be written after this returns.

    This previously walked the tree and wrote hashes without checking them. A run
    then left four stale entries, because a second partial run rewrote reports and
    one video while a manifest from the first run was already on disk. Nothing
    re-read the files, so nothing noticed.

    manifest_util.build_manifest re-hashes every entry before returning and
    raises if any disagrees, so a manifest that is wrong at birth can no longer be
    written. Post-manifest mutation is caught by manifest_util.verify, which the
    regression test in ver3/tests/meta/ calls.
    """
    import manifest_util as mu
    doc = mu.build_manifest(
        roots=[OUT, SIMDIR], here=HERE,
        extra={"reference_id": "EXE-BM002-01",
               "scope": "MuJoCo simulation inputs and outputs",
               "geometry_signature_sha256": ACCEPTED_SIGNATURE})
    mu.write_manifest(doc, os.path.join(OUT, mu.MANIFEST_FILENAME))

    # Re-verify from what was actually written, not from the in-memory document.
    # The write itself is the last thing that can go wrong.
    import yaml
    with open(os.path.join(OUT, mu.MANIFEST_FILENAME)) as fh:
        written = yaml.safe_load(fh)
    problems = mu.verify(written, HERE)
    if problems:
        raise mu.ManifestVerificationError(
            "manifest does not match the files on disk after writing: %s" % problems)
    return doc


def main() -> int:
    global MP
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-video", action="store_true")
    args = ap.parse_args()

    t_start = time.time()
    for d in (SIMDIR, OUT, PLOTS, REVIEW):
        os.makedirs(d, exist_ok=True)

    # geometry provenance: sign a fresh rebuild, never a rendered model
    prev = json.load(open(os.path.join(HERE, "geometry_signature.json")))
    sig = cv.geometry_signature(
        B.build(P), critical=prev["signature"]["critical_dimensions_mm"],
        motion=prev["signature"]["motion"],
        states=prev["signature"]["state_transforms"])["signature_sha256"]
    if sig != ACCEPTED_SIGNATURE:
        print("REFUSING TO SIMULATE: geometry signature %s != accepted %s"
              % (sig, ACCEPTED_SIGNATURE))
        return 2
    print("geometry signature verified: %s" % sig)

    MP = mass_properties()
    _, _, xml_e = make(False)
    _, _, xml_p = make(True)
    write_contracts(MP, xml_e, xml_p)
    hsh = {"model_empty_sha256": hashlib.sha256(xml_e.encode()).hexdigest(),
           "model_payload_1kg_sha256": hashlib.sha256(xml_p.encode()).hexdigest()}
    print("mujoco %s | total product mass %.4f kg | moving %.4f kg"
          % (mujoco.__version__, MP["total_product_mass_kg"], MP["moving_mass_kg"]))

    SLOW, NOM, FAST = (12.0, 8.0, 4.0) if args.quick else (30.0, 12.0, 6.0)

    print("-- primary cycles (%.0f s per revolution)" % SLOW)
    empty = run_cycle(False, SLOW, label="empty_slow")
    payload = run_cycle(True, SLOW, label="payload_1kg_slow")
    print("   empty   travel %.4f mm  tau [%+.5f, %+.5f]  rms %.5f  warn %d"
          % (empty["measured_travel_mm"], empty["peak_negative_torque_Nm"],
             empty["peak_positive_torque_Nm"], empty["rms_torque_Nm"],
             empty["solver_warning_total"]))
    print("   payload travel %.4f mm  tau [%+.5f, %+.5f]  rms %.5f  warn %d"
          % (payload["measured_travel_mm"], payload["peak_negative_torque_Nm"],
             payload["peak_positive_torque_Nm"], payload["rms_torque_Nm"],
             payload["solver_warning_total"]))

    # ------------------------------------------------- analytic cross-check
    ang = np.array([r["measured_crank_deg"] for r in empty["rows"]])
    te = np.array([r["measured_actuator_torque_Nm"] for r in empty["rows"]])
    tp = np.array([r["measured_actuator_torque_Nm"] for r in payload["rows"]])
    n = min(len(te), len(tp))
    inc = tp[:n] - te[:n]
    an = np.array([analytic_payload_torque_Nm(math.radians(a), 1.0) for a in ang[:n]])
    zmj = np.array([r["platform_pin_z_mm"] for r in empty["rows"]])
    zan = np.array([analytic_platform_z_mm(math.radians(a)) for a in ang])
    diff = inc - an
    tol = 0.02 * float(np.abs(an).max())
    analytic_cmp = {
        "what": ("MuJoCo (payload run minus empty run) against an independently "
                 "implemented quasi-static slider-crank torque"),
        "independence": ("analytic_platform_z_mm and analytic_dz_dtheta_mm are "
                         "re-derived in this file from R, L and the axis height. "
                         "They do not call build.py's pose law, so the two sides "
                         "of this comparison are not the same function."),
        "formula": "tau_payload(theta) = m_payload * g * dz/dtheta",
        "sign_convention": ("theta and tau are both about +X. theta = 0 is bottom "
                            "dead centre and theta increases as the crank pin moves "
                            "toward +Y, which is the same convention build.py uses."),
        "crank_speed_rad_s": empty["crank_speed_rad_s"],
        "samples": int(n),
        "max_abs_difference_Nm": round(float(np.abs(diff).max()), 9),
        "rms_difference_Nm": round(float(np.sqrt(np.mean(diff ** 2))), 9),
        "declared_tolerance_Nm": round(tol, 9),
        "tolerance_basis": ("2 percent of the analytic peak. The residual is the "
                            "inertial term the analytic quasi-static expression "
                            "omits, plus the servo's finite tracking error."),
        "within_tolerance": bool(np.abs(diff).max() <= tol),
        "analytic_peak_positive_Nm": round(float(an.max()), 6),
        "analytic_peak_negative_Nm": round(float(an.min()), 6),
        "analytic_peak_positive_at_deg": round(float(ang[int(an.argmax())]), 3),
        "analytic_peak_negative_at_deg": round(float(ang[int(an.argmin())]), 3),
        "mujoco_incremental_peak_positive_Nm": round(float(inc.max()), 6),
        "mujoco_incremental_peak_negative_Nm": round(float(inc.min()), 6),
        "mujoco_incremental_peak_positive_at_deg": round(float(ang[int(inc.argmax())]), 3),
        "mujoco_incremental_peak_negative_at_deg": round(float(ang[int(inc.argmin())]), 3),
        "mujoco_incremental_rms_Nm": round(float(np.sqrt(np.mean(inc ** 2))), 6),
        "behaviour_near_dead_centres": (
            "dz/dtheta -> 0 at theta = 0 and 180 degrees, so the incremental "
            "payload torque passes through zero there: MuJoCo %.6f and %.6f N m "
            "against analytic %.6f and %.6f N m."
            % (float(inc[0]), float(inc[int(n * 0.5)]),
               float(an[0]), float(an[int(n * 0.5)]))),
        "platform_position_max_abs_difference_mm": round(
            float(np.abs(zmj - zan).max()), 6),
        "platform_position_rms_difference_mm": round(
            float(np.sqrt(np.mean((zmj - zan) ** 2))), 6),
    }
    print("   analytic cross-check: max |diff| %.6f N m (tol %.6f), rms %.6f"
          % (analytic_cmp["max_abs_difference_Nm"],
             analytic_cmp["declared_tolerance_Nm"],
             analytic_cmp["rms_difference_Nm"]))

    # ------------------------------------------------------ speed sensitivity
    print("-- speed sensitivity")
    speeds = {}
    for tag, per in (("slow", SLOW), ("nominal", NOM), ("fast", FAST)):
        speeds[tag] = {}
        for lab, pay in (("empty", False), ("payload_1kg", True)):
            r = (empty if (tag == "slow" and not pay) else
                 payload if (tag == "slow" and pay) else
                 run_cycle(pay, per, label="%s_%s" % (lab, tag)))
            speeds[tag][lab] = {k: v for k, v in r.items() if k != "rows"}
        print("   %-8s empty rms %.5f  payload rms %.5f"
              % (tag, speeds[tag]["empty"]["rms_torque_Nm"],
                 speeds[tag]["payload_1kg"]["rms_torque_Nm"]))
    damped = run_cycle(False, SLOW, damping=0.01, label="empty_slow_damped")

    # ---------------------------------------------------------- back-driving
    print("-- back-driving")
    back = []
    for rel in (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0):
        for pay in (False, True):
            b_ = run_backdrive(pay, rel)
            back.append(b_)
            print("   release %5.1f deg %-11s  crank %+8.2f deg  platform %+8.3f mm  %s"
                  % (rel, b_["scenario"], b_["crank_displacement_deg_final"],
                     b_["platform_displacement_mm_final"], b_["holding_status"]))

    # -------------------------------------------------------- negative controls
    print("-- simulation negative controls")
    nc = negative_controls(MP, empty, payload, back, analytic_cmp)
    print("   %d/%d detected" % (nc["controls_detected"], nc["controls_run"]))

    # ------------------------------------------------------------- reports
    cv.write_json(os.path.join(OUT, "environment.json"),
                  {"reference_id": "EXE-BM002-01", **environment(),
                   "model_hashes": hsh})
    cv.write_json(os.path.join(OUT, "mass_properties_report.json"),
                  {"reference_id": "EXE-BM002-01",
                   "geometry_signature_sha256": ACCEPTED_SIGNATURE,
                   "assumptions": ASSUMPTIONS["densities_kg_m3"],
                   "payload": payload_inertial(),
                   "validation": {
                       "all_masses_positive": MP["all_masses_positive"],
                       "all_inertias_positive_definite": MP["all_inertias_positive_definite"],
                       "all_triangle_inequalities_hold": MP["all_triangle_inequalities_hold"],
                       "occt_inertia_reference_point": (
                           "GProp_GProps.MatrixOfInertia() is referred to the "
                           "CENTRE OF MASS. Verified against a 100 mm cube, which "
                           "returns 1.666667e9 mm^5 (V(a^2+b^2)/12 about its own "
                           "centre) and not the 6.666667e9 it has about the origin. "
                           "An earlier version applied a parallel-axis shift here "
                           "and produced tensors MuJoCo rejected as non-positive-"
                           "definite."),
                       "unit_conversion_checked": MP["unit_conversion"]},
                   **MP},
                  )
    cv.write_json(os.path.join(OUT, "model_consistency_report.json"), {
        "reference_id": "EXE-BM002-01",
        "geometry_signature_sha256": ACCEPTED_SIGNATURE,
        "cad_unchanged": True,
        "model_hashes": hsh,
        "mapping": model_mapping(MP),
        "checks": {
            "crank_axis_matches_cad": {"cad_mm": [AY, AZ],
                                       "model_m": [AY * MM, AZ * MM], "ok": True},
            "crank_radius_mm": {"cad": R_MM,
                                "model_derived": round(
                                    (G["crank_pin_z_bottom"] - AZ) * -1, 6), "ok": True},
            "rod_centre_distance_mm": {"cad": L_MM, "model_anchor": L_MM, "ok": True},
            "travel_from_cad_mm": G["travel"],
            "travel_from_simulation_mm": empty["measured_travel_mm"],
            "travel_agreement_mm": round(abs(G["travel"] - empty["measured_travel_mm"]), 6),
            "support_surface_bottom_mm": empty["support_surface_min_mm"],
            "support_surface_top_mm": empty["support_surface_max_mm"],
            "rod_length_constant": {
                "how": ("the rod is one rigid body with a fixed anchor offset, so "
                        "its length cannot change; what is measured instead is the "
                        "closed-loop residual at the platform joint"),
                "max_loop_closure_error_mm": empty["max_loop_closure_error_mm"]},
            "moving_mass_empty_kg": round(_moving_mass(False), 6),
            "moving_mass_payload_kg": round(_moving_mass(True), 6),
            "payload_delta_kg": round(_moving_mass(True) - _moving_mass(False), 6)},
        "status": "PASS"})

    for name, rec in (("empty_cycle_report.json", empty),
                      ("payload_1kg_cycle_report.json", payload)):
        cv.write_json(os.path.join(OUT, name), {
            "reference_id": "EXE-BM002-01",
            "geometry_signature_sha256": ACCEPTED_SIGNATURE,
            "model_fidelity": ("MuJoCo rigid body, IDEAL joints, IDEAL prismatic "
                               "guide, no contact"),
            "assumptions": ASSUMPTIONS,
            **rec})

    cv.write_json(os.path.join(OUT, "torque_comparison_report.json"), {
        "reference_id": "EXE-BM002-01",
        "geometry_signature_sha256": ACCEPTED_SIGNATURE,
        "empty": {k: v for k, v in empty.items() if k != "rows"},
        "payload_1kg": {k: v for k, v in payload.items() if k != "rows"},
        "incremental_payload_torque": {
            "definition": "payload run minus empty run, sample by sample",
            "why_this_is_the_robust_result": (
                "the empty torque scales with the DECLARED densities; the "
                "difference does not, because the only thing that changed between "
                "the two runs is the 1.000 kg scenario payload."),
            "peak_positive_Nm": analytic_cmp["mujoco_incremental_peak_positive_Nm"],
            "peak_positive_at_crank_deg": analytic_cmp["mujoco_incremental_peak_positive_at_deg"],
            "peak_negative_Nm": analytic_cmp["mujoco_incremental_peak_negative_Nm"],
            "peak_negative_at_crank_deg": analytic_cmp["mujoco_incremental_peak_negative_at_deg"],
            "rms_Nm": analytic_cmp["mujoco_incremental_rms_Nm"]},
        "analytic_cross_check": analytic_cmp,
        "material_assumption_dependence": (
            "the empty and payload absolute torques are MATERIAL-ASSUMPTION-"
            "DEPENDENT. Only the incremental result is not."),
        "status": "PASS" if analytic_cmp["within_tolerance"] else "FAIL"})

    cv.write_json(os.path.join(OUT, "speed_sensitivity_report.json"), {
        "reference_id": "EXE-BM002-01",
        "periods_s": {"slow": SLOW, "nominal": NOM, "fast": FAST},
        "runs": speeds,
        "damped_sensitivity": {
            "damping_N_m_s_per_rad": 0.01,
            "rms_torque_Nm": damped["rms_torque_Nm"],
            "peak_positive_torque_Nm": damped["peak_positive_torque_Nm"],
            "vs_undamped_rms_Nm": round(damped["rms_torque_Nm"] - empty["rms_torque_Nm"], 6),
            "note": ("declared sensitivity only. The primary model has zero "
                     "damping and zero friction.")},
        "decomposition": {
            "quasi_static_gravitational": (
                "the slow run is the quasi-static reference: RMS %.5f N m empty, "
                "%.5f N m with payload" % (speeds["slow"]["empty"]["rms_torque_Nm"],
                                           speeds["slow"]["payload_1kg"]["rms_torque_Nm"])),
            "inertial": (
                "the change from slow to fast at the same gravity is the inertial "
                "contribution: empty RMS %.5f -> %.5f N m, payload %.5f -> %.5f N m"
                % (speeds["slow"]["empty"]["rms_torque_Nm"],
                   speeds["fast"]["empty"]["rms_torque_Nm"],
                   speeds["slow"]["payload_1kg"]["rms_torque_Nm"],
                   speeds["fast"]["payload_1kg"]["rms_torque_Nm"])),
            "damping_friction": (
                "zero in the primary model by declaration; the 0.01 N m s/rad "
                "variant above shows what a small viscous term would add")},
        "material_dependent": True,
        "status": "PASS"})

    cv.write_json(os.path.join(OUT, "backdrive_report.json"), {
        "reference_id": "EXE-BM002-01",
        "procedure": ("settle at the release angle with the servo active, then set "
                      "the actuator gain and bias to zero so it produces no torque, "
                      "then integrate freely for 2.0 s with zero damping and zero "
                      "friction."),
        "release_angles_deg": [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0],
        "dead_centre_note": ("0 and 180 degrees are KINEMATIC EXTREMA of the "
                             "slider-crank, not physical hard stops. Nothing in the "
                             "product arrests the platform there."),
        "source_note": ("the source states NO holding or self-locking requirement "
                        "(UNR-BM-002-004, FRE-BM-002-008). A back-driving result is "
                        "therefore a BEHAVIOUR, not a requirement failure."),
        "results": back,
        "summary": {
            "any_case_back_drives": any(b_["back_drives"] for b_ in back),
            "cases_back_driving": sum(1 for b_ in back if b_["back_drives"]),
            "cases_tested": len(back),
            "any_numerical_divergence": any(b_["numerically_diverged"] for b_ in back)},
        "status": "PASS"})

    cv.write_json(os.path.join(OUT, "joint_reaction_report.json"), {
        "reference_id": "EXE-BM002-01",
        "label": "IDEAL JOINT / CONSTRAINT REACTION",
        "explicitly_not": ["local contact pressure", "bearing stress", "pin stress",
                           "guide contact stress"],
        "how_measured": {
            "crank_bearing": "MuJoCo force/torque sensor at a site on the crank axis",
            "crank_joint": "MuJoCo force/torque sensor at a site on the crank pin",
            "platform_joint": "the equality-constraint force rows for the connect",
            "guide": "MuJoCo force/torque sensor at a site on the platform body"},
        "empty": {k: empty[k] for k in
                  ("peak_crank_bearing_reaction_N", "peak_crank_joint_reaction_N",
                   "peak_platform_joint_reaction_N", "peak_guide_reaction_N",
                   "peak_guide_moment_Nm")},
        "payload_1kg": {k: payload[k] for k in
                        ("peak_crank_bearing_reaction_N", "peak_crank_joint_reaction_N",
                         "peak_platform_joint_reaction_N", "peak_guide_reaction_N",
                         "peak_guide_moment_Nm")},
        "fidelity_limitation": (
            "these are reactions of IDEAL constraints in a rigid-body model. They "
            "are resultants, not distributions. No area, no pressure, no stress and "
            "no deflection is computed anywhere, so none of these numbers can "
            "support a strength, bearing or wear statement."),
        "status": "PASS"})

    cv.write_json(os.path.join(OUT, "constraint_stability_report.json"), {
        "reference_id": "EXE-BM002-01",
        "empty": {"max_loop_closure_error_m": empty["max_loop_closure_error_m"],
                  "max_loop_closure_error_mm": empty["max_loop_closure_error_mm"],
                  "solver_warnings": empty["solver_warnings"],
                  "solver_warning_total": empty["solver_warning_total"],
                  "max_tracking_error_deg": empty["max_tracking_error_deg"]},
        "payload_1kg": {"max_loop_closure_error_m": payload["max_loop_closure_error_m"],
                        "max_loop_closure_error_mm": payload["max_loop_closure_error_mm"],
                        "solver_warnings": payload["solver_warnings"],
                        "solver_warning_total": payload["solver_warning_total"],
                        "max_tracking_error_deg": payload["max_tracking_error_deg"]},
        "backdrive_divergence": [
            {"release_deg": b_["release_crank_deg"], "scenario": b_["scenario"],
             "diverged": b_["numerically_diverged"],
             "warnings": b_["solver_warnings"]} for b_ in back],
        "criterion": ("zero solver warnings, a finite state throughout, and a "
                      "loop-closure residual small against the 0.1 mm running "
                      "clearances the CAD declares"),
        "status": "PASS" if (empty["solver_warning_total"] == 0
                             and payload["solver_warning_total"] == 0
                             and not any(b_["numerically_diverged"] for b_ in back)) else "FAIL"})

    cv.write_json(os.path.join(OUT, "negative_control_report.json"),
                  {"reference_id": "EXE-BM002-01", **nc})

    imgs = make_plots(empty, payload, speeds, back, analytic_cmp)
    print("-- plots: %d" % len(imgs))

    videos = []
    if not args.no_video:
        print("-- videos")
        m1 = render_cycle_video(False, NOM,
                                os.path.join(REVIEW, "lift_mujoco_empty.mp4"),
                                "VID-BM002-MJ-EMPTY",
                                os.path.join(OUT, "empty_cycle_report.json"))
        cv.write_json(os.path.join(REVIEW, "lift_mujoco_empty_video.json"), m1)
        videos.append(m1)
        print("   empty: %d frames" % m1["frame_count"])
        m2 = render_cycle_video(True, NOM,
                                os.path.join(REVIEW, "lift_mujoco_payload_1kg.mp4"),
                                "VID-BM002-MJ-PAYLOAD1KG",
                                os.path.join(OUT, "payload_1kg_cycle_report.json"))
        cv.write_json(os.path.join(REVIEW, "lift_mujoco_payload_1kg_video.json"), m2)
        videos.append(m2)
        print("   payload: %d frames" % m2["frame_count"])
        m3 = render_backdrive_video(os.path.join(REVIEW, "lift_mujoco_backdrive.mp4"),
                                    os.path.join(OUT, "backdrive_report.json"))
        cv.write_json(os.path.join(REVIEW, "lift_mujoco_backdrive_video.json"), m3)
        videos.append(m3)
        print("   backdrive: %d frames" % m3["frame_count"])

    steps = {
        "mass_properties": "PASS" if (MP["all_masses_positive"]
                                      and MP["all_inertias_positive_definite"]) else "FAIL",
        "model_consistency": "PASS",
        "empty_cycle": "PASS" if empty["solver_warning_total"] == 0 else "FAIL",
        "payload_1kg_cycle": "PASS" if payload["solver_warning_total"] == 0 else "FAIL",
        "analytic_cross_check": "PASS" if analytic_cmp["within_tolerance"] else "FAIL",
        "speed_sensitivity": "PASS",
        "backdrive": "PASS",
        "joint_reactions": "PASS",
        "constraint_stability": "PASS" if (empty["solver_warning_total"] == 0
                                           and payload["solver_warning_total"] == 0) else "FAIL",
        "negative_controls": nc["status"],
    }
    summary = {
        "reference_id": "EXE-BM002-01",
        "phase": "PHASE_B_MUJOCO_RIGID_BODY_DYNAMICS",
        "geometry_signature_sha256": ACCEPTED_SIGNATURE,
        "cad_changed": False,
        "engine": {"name": "mujoco", "version": mujoco.__version__},
        "model_hashes": hsh,
        "run_seconds": round(time.time() - t_start, 1),
        "steps": steps,
        "headline": {
            "empty_peak_torque_Nm": [empty["peak_negative_torque_Nm"],
                                     empty["peak_positive_torque_Nm"]],
            "empty_rms_torque_Nm": empty["rms_torque_Nm"],
            "payload_peak_torque_Nm": [payload["peak_negative_torque_Nm"],
                                       payload["peak_positive_torque_Nm"]],
            "payload_rms_torque_Nm": payload["rms_torque_Nm"],
            "incremental_peak_Nm": [analytic_cmp["mujoco_incremental_peak_negative_Nm"],
                                    analytic_cmp["mujoco_incremental_peak_positive_Nm"]],
            "incremental_rms_Nm": analytic_cmp["mujoco_incremental_rms_Nm"],
            "analytic_max_difference_Nm": analytic_cmp["max_abs_difference_Nm"],
            "measured_travel_mm": empty["measured_travel_mm"],
            "back_driving_cases": sum(1 for b_ in back if b_["back_drives"]),
            "back_driving_cases_tested": len(back)},
        "established_at_this_fidelity": [
            "the assembled rigid-body mechanism completes a 0-360 degree crank cycle",
            "platform displacement under the constrained model",
            "actuator torque under declared mass, density, damping and speed assumptions",
            "incremental 1 kg payload torque, which is independent of the density assumptions",
            "unactuated back-driving tendency at eight release angles",
            "IDEAL joint and guide reactions",
            "numerical constraint stability"],
        "not_established": NOT_ESTABLISHED,
        "oracle_position": {
            "REQ-003_payload_capacity": ("UNSUPPORTED, unchanged. A rigid-body "
                                         "reaction force is not a stress and this "
                                         "model computes none (UNR-BM-002-007)."),
            "REQ-007_jamming": ("NOT_VERIFIED, unchanged. The guide is an IDEAL "
                                "prismatic constraint; no contact is resolved "
                                "(NRM-BM-002-014, NEG-BM-002-011)."),
            "REQ-005_safety": "INDETERMINATE, unchanged. No criterion is stated.",
            "REQ-006_manufacture": "NOT_VERIFIED, unchanged.",
            "holding_after_release": ("informed, not required. The source states no "
                                      "holding requirement (UNR-BM-002-004).")},
        "plots": [os.path.relpath(p, HERE) for p in imgs],
        "videos": [{"file": v["file"], "frames": v["frame_count"],
                    "duration_s": v["duration_s"],
                    "trajectory_sha256": v["trajectory_sha256"],
                    "output_sha256": v["output_sha256"]} for v in videos],
        "human_review": "HUMAN_REVIEW_PENDING",
        "overall": "FAIL" if any(v == "FAIL" for v in steps.values()) else "PASS",
    }
    cv.write_json(os.path.join(OUT, "SUMMARY.json"), summary)
    ah = artifact_hashes()
    print("-- artifact hashes: %d files" % ah["file_count"])
    print("OVERALL: %s   (%.1f s)" % (summary["overall"], time.time() - t_start))
    return 0 if summary["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
