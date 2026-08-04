"""MuJoCo operating simulation for the EXE-BM001-01 lid.

WHAT THIS IS
    A rigid-body simulation of the lid swinging on its hinge, used to obtain an
    operating-effort curve: how much torque the hinge must supply to hold or move
    the lid at each opening angle. The mass and the hinge geometry come from the
    CAD; nothing here is fitted to a desired answer.

WHAT THIS IS NOT
    It is not evidence about the snap-fit. The barb's strain, insertion force,
    pull-out force and fatigue life are untouched by this and remain
    NOT_VERIFIED. It is not a verification of REQ-003 either: the source states
    no effort ceiling, so there is nothing to compare a torque against.

    Every number below rests on ASSUMPTIONS that no source supplies - density,
    joint friction, actuation profile. They are declared in ASSUMPTIONS and
    written into the output so no reader can mistake them for Oracle truth.

    python simulate_lid.py
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools")))

import build as B          # noqa: E402
import cadval as cv        # noqa: E402

OUT = os.path.join(HERE, "validation", "simulation")

# --------------------------------------------------------------- assumptions
ASSUMPTIONS = {
    "density_kg_m3": {
        "value": 1200.0,
        "why": ("a generic rigid polymer. UNR-BM-001-004 leaves material and process "
                "open, so this is a stated assumption and not a source value."),
        "affects": "lid mass, and therefore every torque below, linearly"},
    "hinge_friction_Nm_per_rad_s": {
        "value": 0.0,
        "why": ("no friction is modelled. A friction torque would ADD to the effort "
                "computed here, so these curves are a lower bound on the effort a "
                "real hinge would need, not a prediction of it."),
        "affects": "reported torque is optimistic"},
    "gravity_m_s2": {"value": 9.81, "why": "standard, lid opening upward against it"},
    "actuation_profile": {
        "value": "minimum-jerk sweep over 2.0 s, closed to open and back",
        "why": ("a smooth user-like motion. A different profile changes the inertial "
                "part of the torque but not the gravity part.")},
    "orientation": {
        "value": "enclosure sitting upright on a desk, hinge axis horizontal",
        "why": "the only orientation in which the source's desktop use makes sense"},
}

NOT_ESTABLISHED = [
    "snap-arm strain, stress or insertion force",
    "pull-out force of the retained pin",
    "fatigue, creep or repeated-use life",
    "whether any user finds the effort acceptable (no effort ceiling is stated)",
    "friction, wear or lubrication behaviour",
    "manufacturing tolerance robustness",
]


def lid_inertial(P):
    """Lid mass and inertia about the hinge axis, taken from the CAD solid."""
    closure = [b for b in B.build(P) if b.id == "BODY-CLOSURE"][0].shape
    vol_mm3 = cv._gprops_volume(closure)
    com = cv._com(closure)
    rho = ASSUMPTIONS["density_kg_m3"]["value"]
    mass = vol_mm3 * 1e-9 * rho                       # mm^3 -> m^3 -> kg
    # distance from the hinge axis to the centre of mass, in the plane normal to it
    dy = (com[1] - P["axis_y"]) * 1e-3
    dz = (com[2] - P["axis_z"]) * 1e-3
    r = math.hypot(dy, dz)
    # I about the axis: use the solid's own second moment via a slab approximation
    # bounded by its bounding box, then shift to the axis (parallel axis).
    bb = cv.bbox_of(closure)
    a, b_ = bb["dy"] * 1e-3, bb["dz"] * 1e-3
    i_com = mass * (a * a + b_ * b_) / 12.0
    return {"volume_mm3": round(vol_mm3, 4), "mass_kg": round(mass, 6),
            "com_mm": [round(c, 4) for c in com],
            "com_offset_from_axis_m": round(r, 6),
            "I_about_com_kgm2": round(i_com, 9),
            "I_about_hinge_kgm2": round(i_com + mass * r * r, 9),
            "inertia_note": ("I about the centre of mass uses the bounding-box slab "
                             "formula, which OVERSTATES it for a plate with cut-outs. "
                             "The inertial term is therefore conservative; the gravity "
                             "term, which dominates a quasi-static open, is exact.")}


def mjcf(P, inert):
    """Single hinge body. The lid is rigid here; only the joint matters."""
    ay, az = P["axis_y"] * 1e-3, P["axis_z"] * 1e-3
    m = inert["mass_kg"]
    i = inert["I_about_com_kgm2"]
    com = inert["com_mm"]
    cy, cz = com[1] * 1e-3 - ay, com[2] * 1e-3 - az
    cx = com[0] * 1e-3
    # The joint is deliberately UNLIMITED. A range limit would inject a
    # constraint force at the stop that dwarfs the physics and would be read as
    # operating effort - it is not. The terminal open pose is a CAD result
    # (INT-09), established by geometry, and nothing here is asked to reproduce it.
    return f"""<mujoco model="EXE-BM001-01-lid">\n  <compiler autolimits="true"/>
  <option gravity="0 0 -{ASSUMPTIONS['gravity_m_s2']['value']}" integrator="RK4" timestep="0.0005"/>
  <worldbody>
    <body name="lid" pos="0 {ay} {az}">
      <joint name="hinge" type="hinge" axis="1 0 0" pos="0 0 0" damping="0" limited="false"/>
      <inertial pos="{cx:.6f} {cy:.6f} {cz:.6f}" mass="{m:.6f}"
                diaginertia="{i:.9f} {i:.9f} {i:.9f}"/>
      <geom type="box" size="0.001 0.001 0.001" pos="{cx:.6f} {cy:.6f} {cz:.6f}"
            contype="0" conaffinity="0" density="0"/>
    </body>
  </worldbody>
  <actuator>
    <motor joint="hinge" name="operator" gear="1" ctrlrange="-100 100"/>
  </actuator>
</mujoco>"""


def minimum_jerk(t, T):
    s = min(max(t / T, 0.0), 1.0)
    return 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5


def run(P):
    import mujoco
    import numpy as np

    inert = lid_inertial(P)
    model = mujoco.MjModel.from_xml_string(mjcf(P, inert))
    data = mujoco.MjData(model)

    open_rad = math.radians(P["open_angle_deg"])
    T_open, T_hold, T_close = 2.0, 0.5, 2.0
    total = T_open + T_hold + T_close
    dt = model.opt.timestep
    n = int(total / dt)

    # Inverse dynamics along a prescribed trajectory: drive the joint exactly and
    # read the torque MuJoCo needs to produce it. This is the operating effort.
    rows = []
    for k in range(n + 1):
        t = k * dt
        if t <= T_open:
            s = minimum_jerk(t, T_open)
        elif t <= T_open + T_hold:
            s = 1.0
        else:
            s = 1.0 - minimum_jerk(t - T_open - T_hold, T_close)
        q = -open_rad * s
        # finite-difference the prescribed trajectory for velocity and acceleration
        h = dt
        def qs(tt):
            if tt <= T_open:
                u = minimum_jerk(tt, T_open)
            elif tt <= T_open + T_hold:
                u = 1.0
            else:
                u = 1.0 - minimum_jerk(min(tt - T_open - T_hold, T_close), T_close)
            return -open_rad * u
        qd = (qs(t + h) - qs(t - h)) / (2 * h)
        qdd = (qs(t + h) - 2 * qs(t) + qs(t - h)) / (h * h)

        data.qpos[0] = q
        data.qvel[0] = qd
        data.qacc[0] = qdd
        mujoco.mj_inverse(model, data)
        tau = float(data.qfrc_inverse[0])

        # gravity-only component: what the hinge must hold at rest at this angle
        data.qvel[0] = 0.0
        data.qacc[0] = 0.0
        mujoco.mj_inverse(model, data)
        tau_static = float(data.qfrc_inverse[0])

        rows.append({"t_s": round(t, 6), "angle_deg": round(-math.degrees(q), 6),
                     "omega_rad_s": round(-qd, 6), "alpha_rad_s2": round(-qdd, 6),
                     "torque_Nm": round(tau, 9), "torque_static_Nm": round(tau_static, 9)})

    # Where the static torque changes sign the centre of mass passes over the
    # hinge axis. Beyond it gravity tends to HOLD the lid open rather than shut
    # it - an operating property of this geometry, not an assumption.
    over_centre = None
    opening = [r for r in rows if r["t_s"] <= 2.0]
    for a, b_ in zip(opening, opening[1:]):
        if a["torque_static_Nm"] == 0 or a["torque_static_Nm"] * b_["torque_static_Nm"] < 0:
            over_centre = round((a["angle_deg"] + b_["angle_deg"]) / 2.0, 3)
            break

    peak = max(rows, key=lambda r: abs(r["torque_Nm"]))
    peak_static = max(rows, key=lambda r: abs(r["torque_static_Nm"]))
    return inert, rows, {
        "peak_total_torque_Nm": round(abs(peak["torque_Nm"]), 6),
        "peak_total_at_angle_deg": peak["angle_deg"],
        "peak_static_torque_Nm": round(abs(peak_static["torque_static_Nm"]), 6),
        "peak_static_at_angle_deg": peak_static["angle_deg"],
        "torque_at_closed_Nm": round(abs(rows[0]["torque_static_Nm"]), 6),
        "torque_at_full_open_Nm": round(abs(
            min(rows, key=lambda r: abs(r["angle_deg"] - P["open_angle_deg"]))["torque_static_Nm"]), 6),
        "sample_count": len(rows),
        "duration_s": total,
        "over_centre_angle_deg": over_centre,
        "over_centre_meaning": (
            "beyond this angle the centre of mass has passed the hinge axis, so "
            "gravity tends to hold the lid open instead of closing it. The lid "
            "therefore rests against the INT-09 stop under its own weight rather "
            "than falling shut. This is a consequence of the geometry; whether it "
            "is DESIRABLE is a design judgement nobody has made."),
    }


def plots(P, rows, summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = [r["t_s"] for r in rows]
    a = [r["angle_deg"] for r in rows]
    tau = [r["torque_Nm"] for r in rows]
    taus = [r["torque_static_Nm"] for r in rows]
    written = []

    fig, ax = plt.subplots(figsize=(9, 4.4), dpi=150)
    ax.plot(t, a, lw=2.0, color="#1f5f8b")
    ax.set_xlabel("time (s)"); ax.set_ylabel("opening angle (deg)")
    ax.set_title("EXE-BM001-01 lid trajectory\nprescribed minimum-jerk open, hold, close")
    ax.grid(True, alpha=0.3)
    ax.axhline(P["open_angle_deg"], color="#c0392b", ls="--", lw=1.0)
    ax.annotate("terminal open pose, %.0f deg (INT-09)" % P["open_angle_deg"],
                xy=(t[len(t) // 2], P["open_angle_deg"]), xytext=(0.35, 0.55),
                textcoords="axes fraction", fontsize=9, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b"))
    p1 = os.path.join(OUT, "plot_angle_vs_time.png")
    fig.tight_layout(); fig.savefig(p1); plt.close(fig); written.append(p1)

    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=150)
    ax.plot(a, [abs(x) for x in taus], lw=2.2, color="#0b6b3a",
            label="static (gravity only) - what the hinge holds at rest")
    ax.plot(a, [abs(x) for x in tau], lw=1.2, color="#8e44ad", alpha=0.85,
            label="total during the prescribed motion (adds inertia)")
    ax.set_xlabel("opening angle (deg)"); ax.set_ylabel("|hinge torque| (N m)")
    ax.set_title("EXE-BM001-01 operating effort vs opening angle\n"
                 "assumed density %.0f kg/m3, no friction - a LOWER BOUND on real effort"
                 % ASSUMPTIONS["density_kg_m3"]["value"])
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8.5, loc="best")
    p2 = os.path.join(OUT, "plot_torque_vs_angle.png")
    fig.tight_layout(); fig.savefig(p2); plt.close(fig); written.append(p2)

    fig, ax = plt.subplots(figsize=(9, 4.4), dpi=150)
    ax.plot(t, tau, lw=1.6, color="#8e44ad")
    ax.set_xlabel("time (s)"); ax.set_ylabel("hinge torque (N m)")
    ax.set_title("EXE-BM001-01 hinge torque vs time\n"
                 "sign change marks the reversal from opening to closing")
    ax.grid(True, alpha=0.3); ax.axhline(0, color="#555", lw=0.8)
    p3 = os.path.join(OUT, "plot_torque_vs_time.png")
    fig.tight_layout(); fig.savefig(p3); plt.close(fig); written.append(p3)
    return written


def main():
    os.makedirs(OUT, exist_ok=True)
    P = B.load_params()
    inert, rows, summary = run(P)
    imgs = plots(P, rows, summary)
    import mujoco
    rec = {
        "reference_id": "EXE-BM001-01",
        "what_this_is": ("a rigid-body operating simulation of the lid on its hinge, "
                         "producing an effort-vs-angle curve"),
        "what_this_is_not": ("evidence about the snap-fit, and not a verification of "
                             "any source requirement. No effort ceiling is stated in "
                             "the source, so no torque here can pass or fail anything."),
        "engine": {"name": "mujoco", "version": mujoco.__version__},
        "model": {"bodies": 1, "joint": "hinge, axis +X, unlimited (see mjcf comment)",
                  "trajectory_sweep_deg": P["open_angle_deg"],
                  "inertial_from_cad": inert},
        "assumptions": ASSUMPTIONS,
        "results": summary,
        "not_established": NOT_ESTABLISHED,
        "status": "COMPUTED_UNDER_DECLARED_ASSUMPTIONS",
        "oracle_status_if_cited": ("NOT_VERIFIED for REQ-003 user effort. This is a "
                                   "computed quantity at a declared fidelity, not "
                                   "evidence against a stated requirement."),
        "plots": [os.path.relpath(p, HERE) for p in imgs],
        "trajectory_samples": rows[::40],
    }
    cv.write_json(os.path.join(OUT, "lid_operation_simulation.json"), rec)
    print("mujoco %s  |  lid mass %.4f kg  |  I about hinge %.3e kg m2"
          % (mujoco.__version__, inert["mass_kg"], inert["I_about_hinge_kgm2"]))
    print("peak static torque %.4f N m at %.1f deg   peak total %.4f N m at %.1f deg"
          % (summary["peak_static_torque_Nm"], summary["peak_static_at_angle_deg"],
             summary["peak_total_torque_Nm"], summary["peak_total_at_angle_deg"]))
    print("closed %.4f N m   full open %.4f N m"
          % (summary["torque_at_closed_Nm"], summary["torque_at_full_open_Nm"]))
    for p in imgs:
        print("  plot:", os.path.relpath(p, HERE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
