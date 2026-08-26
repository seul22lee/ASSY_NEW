"""SCRATCH TRANSLATOR - the pilot design plan into the existing canonical S05.

EXPERIMENT INFRASTRUCTURE, not an architecture. It does the bookkeeping the
model was previously forced to do: entity ids, construction steps, parameters,
constraints, canonical references and the KinematicRealization rows. Geometry
comes only from the design plan; nothing here edits the pilot's shapes.

WHAT IT DERIVES, AND FROM WHAT
  a feature            <- one `add`/`subtract` element
  Feature.interfaces   <- the relationships that name that element
  KRL for a relation   <- the relation's own `provider_site` interface
  KRL for a joint      <- a PhysicalInteraction with effect PERMIT_MOTION at an
                          interface, whose geometry therefore permits the motion
  KRL, external site   <- the retained body's own material (the one place a
                          choice is made; recorded in the report)
  Parameter            <- one named dimension
  Constraint           <- `== value` for a chosen value, or the stated relation
"""
import json, os, re, sys
REPO = "/home/ftk3187/github/ASSY_Ver3.0"
sys.path.insert(0, REPO); os.chdir(REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from rebuild_cnd1 import build
from harness import synthetic_selection
from ver3.assy_v3.downstream import ir
from ver3.assy_v3.state.patch import Op, StagePatch

OUT = os.environ.get("PILOT_OUT", os.path.join(
    REPO, "scratchpad", "unitG_live", "BM-001", "s05_fresh_authoring_pilot"))
CID = os.environ.get("PILOT_CID", "CND-0004")
MM = ir.KERNEL_LENGTH_UNIT


# ----------------------------------------------------------------- expressions
def const(v, unit=MM):
    return {"const": float(v), "unit": unit}


def ref(pid):
    return {"ref": pid}


def half_negative(expr):
    """-(expr)/2 - centring a corner-built primitive on its stated centre."""
    return {"op": "/", "args": [{"op": "-", "args": [expr]}, const(2, "1")]}


_TOKEN = re.compile(r"\s*([A-Za-z_][A-Za-z_0-9]*|\d+\.?\d*|[()+\-*/\[\]])")


def parse_relation(text, params):
    """A small linear expression over declared names, to the canonical AST."""
    tokens, pos = [], 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ValueError("cannot read %r at %d" % (text, pos))
        tokens.append(m.group(1)); pos = m.end()
    i = [0]

    def peek():
        return tokens[i[0]] if i[0] < len(tokens) else None

    def atom():
        # UNARY MINUS. A position on the far side of the origin is written
        # "-channel_width/2", which is ordinary arithmetic and not a defect in
        # the design; the parser simply had no rule for it.
        if peek() == "-":
            i[0] += 1
            return {"neg": atom()}
        if peek() == "+":
            i[0] += 1
            return atom()
        t = tokens[i[0]]; i[0] += 1
        if t == "(":
            e = expr(); i[0] += 1; return e
        if re.match(r"^\d", t):
            return {"number": float(t)}
        if peek() == "[":
            # A COMPONENT OF A VECTOR-VALUED DIMENSION, e.g. lid_plate_size[2].
            # Part of the same translator fix as expand_triple: the design gave
            # that dimension three numbers, so one of its components is just a
            # number. Nothing is computed, chosen or altered here.
            i[0] += 1
            index = int(float(tokens[i[0]])); i[0] += 1
            if peek() == "]":
                i[0] += 1
            if t not in VECTOR_DIMS:
                raise ValueError("%r is indexed but is not a vector dimension" % t)
            return {"number": float(VECTOR_DIMS[t][index])}
        if t not in params:
            raise ValueError("relation names %r, which is not a declared dimension" % t)
        return {"param": params[t]}

    def term():
        node = atom()
        while peek() in ("*", "/"):
            op = tokens[i[0]]; i[0] += 1
            node = {"op": op, "l": node, "r": atom()}
        return node

    def expr():
        node = term()
        while peek() in ("+", "-"):
            op = tokens[i[0]]; i[0] += 1
            node = {"op": op, "l": node, "r": term()}
        return node

    tree = expr()

    def _is_number(node):
        return "number" in node or ("neg" in node and _is_number(node["neg"]))

    def lower(node, dimensionless=False):
        if "neg" in node:
            return {"op": "-", "args": [lower(node["neg"], dimensionless)]}
        if "param" in node:
            return ref(node["param"])
        if "number" in node:
            return const(node["number"], "1" if dimensionless else MM)
        left, right = node["l"], node["r"]
        if node["op"] in ("*", "/"):
            # a plain number beside a length is a scale factor, not a length
            # A PLAIN NUMBER BESIDE A LENGTH IS A SCALE FACTOR, not a length:
            # `2*drawer_clearance` doubles a gap, `(...)/2` halves a span.
            lo = lower(left, dimensionless=_is_number(left))
            ro = lower(right, dimensionless=_is_number(right))
            return {"op": node["op"], "args": [lo, ro]}
        return {"op": node["op"], "args": [lower(left), lower(right)]}

    return lower(tree)


#: name -> [x, y, z] for a dimension the design gave a VECTOR value.
VECTOR_DIMS = {}


def expand_triple(entries, params):
    """A size/position triple, with a named VECTOR dimension expanded in place.

    TRANSLATOR FIX (recorded in translator_fixes.md). The pilot language says a
    dimension carries one number, and the round-1 design also declared one whose
    value is a triple and then used its NAME where a triple was expected. The
    meaning is unambiguous, so it is read as written: the name is replaced by
    its three components. No number, position or design decision is altered -
    this only lets the translator represent what the design already says.
    """
    out = []
    for entry in entries or []:
        if isinstance(entry, str) and entry.strip() in VECTOR_DIMS:
            out.extend(VECTOR_DIMS[entry.strip()])
        else:
            out.append(entry)
    return out


def value_expr(v, params):
    """A size/position entry: a number in mm, or the name of a dimension."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return const(v)
    text = str(v).strip()
    if text in params:
        return ref(params[text])
    return parse_relation(text, params)


# ----------------------------------------------------------------- kinds
def feature_kind(element, first_additive):
    """A kind from the closed vocabulary, chosen by POLARITY and SHAPE only.
    No element name is read: the model's names are prose, not a vocabulary."""
    if element.get("op") == "subtract":
        return "BORE" if element.get("shape") == "cylinder" else "CLEARANCE_POCKET"
    if first_additive:
        return "STOCK"
    return "BOSS" if element.get("shape") == "cylinder" else "RIB"


AXIS_OF = {"+X": "+X", "-X": "-X", "+Y": "+Y", "-Y": "-Y", "+Z": "+Z", "-Z": "-Z"}


def main():
    plan_file = os.environ.get("PILOT_PLAN", "parsed_design_plan.json")
    plan = json.load(open(os.path.join(OUT, plan_file)))
    state = build()
    decision, why = synthetic_selection(state, CID)
    assert decision, why

    def mine(fam):
        return [r for r in sorted(state.standing(fam), key=lambda x: x["entity_id"])
                if CID in (r.get("_premises") or [])]

    envelopes = {e["body"]: e for e in mine("Envelope")}
    regions = {r["entity_id"]: r for r in mine("FunctionalRegion")}
    interfaces = {i["entity_id"]: i for i in mine("Interface")}
    relations = mine("ConstraintRelation")
    joints = mine("Joint")
    phis = mine("PhysicalInteraction")
    groups = {g["entity_id"]: g.get("body") for g in mine("RigidGroup")}
    scale_mm = float(plan["scale_mm_per_unit"])

    ops, log = [], {"choices": [], "counts": {}}
    n = [0]

    def new(prefix):
        n[0] += 1
        return "%s-%04d" % (prefix, n[0])

    # ---- parameters and the constraints that fix them ------------------
    params, pnum, cnum = {}, [0], [0]

    def add_param(name, role=None):
        pnum[0] += 1
        pid = "PRM-%04d" % pnum[0]
        params[name] = pid
        fields = {"symbol": name, "unit": MM, "status": ir.DECLARED}
        if role:
            fields["role"] = role
        ops.append(Op("CREATE", "Parameter", pid, fields, "pilot:translator"))
        return pid

    def add_constraint(lhs, rhs, kind, basis):
        cnum[0] += 1
        cid = "CON-%04d" % cnum[0]
        expression = {"relation": "==", "lhs": lhs, "rhs": rhs}
        used = sorted(_refs(expression))
        ops.append(Op("CREATE", "Constraint", cid,
                      {"expression": expression, "parameters": used, "kind": kind,
                       "basis": basis}, "pilot:translator", premise_refs=used))
        return cid

    def _refs(node):
        if isinstance(node, dict):
            if isinstance(node.get("ref"), str):
                return {node["ref"]}
            return {r for v in node.values() for r in _refs(v)}
        if isinstance(node, list):
            return {r for v in node for r in _refs(v)}
        return set()

    scale_id = add_param("scale_mm_per_unit", role="SCALE")
    add_constraint(ref(scale_id), const(scale_mm), "DIMENSIONAL", "DESIGN_CHOICE")
    log["choices"].append("the SCALE parameter takes the model's own "
                          "scale_mm_per_unit = %s" % scale_mm)

    VECTOR_DIMS.clear()
    for d in plan.get("dimensions") or []:
        value = d.get("value")
        if isinstance(value, list) and len(value) == 3 and \
                all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in value):
            VECTOR_DIMS[d["name"]] = list(value)
    log["choices"].append("vector-valued dimensions read as triples: %s"
                          % (sorted(VECTOR_DIMS) or "none"))

    fixed, related = [], []
    for d in plan.get("dimensions") or []:
        if d.get("name") in VECTOR_DIMS:
            continue
        if d.get("value") is not None:
            add_param(d["name"]); fixed.append(d["name"])
        else:
            add_param(d["name"]); related.append(d)
    for d in plan.get("dimensions") or []:
        if d.get("name") in VECTOR_DIMS:
            continue
        if d.get("value") is not None:
            add_constraint(ref(params[d["name"]]), const(d["value"]),
                           "DIMENSIONAL", "DESIGN_CHOICE")
    for d in related:
        add_constraint(ref(params[d["name"]]), parse_relation(d["relation"], params),
                       "DIMENSIONAL", "GEOMETRIC_RELATION")
    log["counts"]["parameters"] = pnum[0]
    log["counts"]["fixed_by_choice"] = len(fixed)
    log["counts"]["fixed_by_relation"] = len(related)

    # ---- features ------------------------------------------------------
    element_feature = {}          # "BOD/name" -> feature id
    body_first_additive = {}
    # WHAT EACH ELEMENT REALIZES, read from the design's own mating sets. A
    # mating set names ALL the participants of one engagement together, so the
    # attribution is taken whole rather than inferred pair by pair. Older plans
    # used `intended_physical_relationships`; both are read, neither is guessed.
    interfaces_of = {}
    set_targets = {}          # "BOD/name" -> upstream Joint / ConstraintRelation ids
    for mating in plan.get("mating_sets") or []:
        upstream = [u for u in (mating.get("upstream_relationships") or [])
                    if isinstance(u, str)]
        handles = ["%s/%s" % (q.get("body"), q.get("element"))
                   for q in (mating.get("participants") or [])
                   if q.get("body") and q.get("element")]
        for handle in handles:
            for uid in upstream:
                if uid in interfaces:
                    interfaces_of.setdefault(handle, [])
                    if uid not in interfaces_of[handle]:
                        interfaces_of[handle].append(uid)
                elif uid.startswith(("JNT-", "CRL-")):
                    set_targets.setdefault(handle, [])
                    if uid not in set_targets[handle]:
                        set_targets[handle].append(uid)
    for rel in plan.get("intended_physical_relationships") or []:
        for side in ("a", "b"):
            handle = str(rel.get(side) or "")
            if rel.get("upstream") in interfaces and "/" in handle:
                interfaces_of.setdefault(handle, [])
                if rel["upstream"] not in interfaces_of[handle]:
                    interfaces_of[handle].append(rel["upstream"])

    for body in plan.get("bodies") or []:
        bid = body["upstream_body"]
        env = envelopes.get(bid)
        centre = (env.get("extent") or {}).get("centre") or [0, 0, 0]
        for element in body.get("elements") or []:
            handle = "%s/%s" % (bid, element.get("name"))
            first = element.get("op") == "add" and bid not in body_first_additive
            if first:
                body_first_additive[bid] = True
            kind = feature_kind(element, first)
            fid = new("FEA")
            element_feature[handle] = fid
            at = [value_expr(c, params)
                  for c in expand_triple(element.get("at") or [0, 0, 0], params)]
            # THE DATUM. A cleared region where the element says so, otherwise
            # the body's own envelope. The offset is the model's own millimetre
            # position taken relative to that datum's committed point.
            cleared = element.get("clears")
            if cleared in regions:
                datum = cleared
                base = (regions[cleared].get("volume") or {}).get("centre") or [0, 0, 0]
            else:
                datum = env["entity_id"]
                base = centre
            offset = [{"op": "-", "args": [at[i], const(float(base[i]) * scale_mm)]}
                      for i in range(3)]
            steps = []
            if element.get("shape") == "wedge":
                # A GENERIC RIGHT TRIANGULAR PRISM, lowered with the EXISTING
                # opcodes: the box, minus a copy of itself rotated 45 degrees
                # about the sloped axis and pushed clear, leaves the ramp. No
                # new IR opcode and no new compiler capability; it is a general
                # CAD shape, not a hook or a latch.
                size = [value_expr(c, params)
                        for c in expand_triple(element.get("size"), params)]
                slope = str(element.get("slope") or "+X").strip().upper()
                axis_letter = slope[-1]
                rot_axis = {"X": "Y", "Y": "X", "Z": "Y"}[axis_letter]
                sign = -1.0 if slope.startswith("-") else 1.0
                diag = {"X": size[0], "Y": size[1], "Z": size[2]}[axis_letter]
                steps.append({"id": "S1", "operation": "BOX",
                              "parameters": {"dx": size[0], "dy": size[1], "dz": size[2]}})
                steps.append({"id": "S2", "operation": "TRANSLATE", "operands": ["S1"],
                              "parameters": {"dx": half_negative(size[0]),
                                             "dy": half_negative(size[1]),
                                             "dz": half_negative(size[2])}})
                # the cutter: the same block, turned and offset so its corner
                # sweeps the diagonal
                steps.append({"id": "S3", "operation": "BOX",
                              "parameters": {"dx": {"op": "*", "args": [size[0], const(2, "1")]},
                                             "dy": {"op": "*", "args": [size[1], const(2, "1")]},
                                             "dz": {"op": "*", "args": [size[2], const(2, "1")]}}})
                steps.append({"id": "S4", "operation": "ROTATE", "operands": ["S3"],
                              "axis": rot_axis,
                              "parameters": {"angle": const(45.0 * sign, "deg")}})
                steps.append({"id": "S5", "operation": "TRANSLATE", "operands": ["S4"],
                              "parameters": {"dx": const(0), "dy": const(0),
                                             "dz": {"op": "/", "args": [diag, const(1.0, "1")]}}})
                steps.append({"id": "S6", "operation": "CUT", "operands": ["S2", "S5"]})
            elif element.get("shape") == "box":
                size = [value_expr(c, params)
                        for c in expand_triple(element.get("size"), params)]
                steps.append({"id": "S1", "operation": "BOX",
                              "parameters": {"dx": size[0], "dy": size[1], "dz": size[2]}})
                steps.append({"id": "S2", "operation": "TRANSLATE", "operands": ["S1"],
                              "parameters": {"dx": half_negative(size[0]),
                                             "dy": half_negative(size[1]),
                                             "dz": half_negative(size[2])}})
            else:
                radius = value_expr(element.get("radius"), params)
                height = value_expr(element.get("height"), params)
                steps.append({"id": "S1", "operation": "CYLINDER",
                              "parameters": {"radius": radius, "height": height}})
                steps.append({"id": "S2", "operation": "TRANSLATE", "operands": ["S1"],
                              "parameters": {"dx": const(0), "dy": const(0),
                                             "dz": half_negative(height)}})
            fields = {"body": bid, "feature_kind": kind,
                      "geometry": "%s (%s)" % (element.get("name"),
                                               element.get("why") or element.get("op")),
                      "placement": {"datum": datum,
                                    "axis": AXIS_OF.get(element.get("axis"), "+Z"),
                                    "offset": offset},
                      "construction": steps}
            named = interfaces_of.get(handle) or []
            if named:
                fields["interfaces"] = named
            premises = [bid, datum] + sorted(_refs(fields)) + named
            ops.append(Op("CREATE", "Feature", fid, fields, "pilot:translator",
                          premise_refs=[p for p in premises if p]))
    log["counts"]["features"] = n[0]

    # ---- KinematicRealizations, derived from upstream links ------------
    by_interface = {}
    for handle, named in interfaces_of.items():
        for iid in named:
            by_interface.setdefault(iid, []).append(element_feature[handle])
    krl = {}
    for handle, targets in sorted(set_targets.items()):
        fid = element_feature.get(handle)
        if not fid:
            continue
        for target in targets:
            krl.setdefault(target, [])
            if fid not in krl[target]:
                krl[target].append(fid)
                log["choices"].append("KRL for %s includes %s because the design's mating "
                                      "set names it" % (target, handle))
    for rel in relations:
        rid = rel["entity_id"]
        if krl.get(rid):
            continue
        site = rel.get("provider_site")
        if site and by_interface.get(site):
            krl[rid] = list(by_interface[site])
            log["choices"].append("KRL for %s from its own provider_site %s" % (rid, site))
        elif rel.get("provider_reaction_site"):
            body = groups.get(rel.get("retained_group"))
            material = [element_feature[h] for h in sorted(element_feature)
                        if h.startswith(body + "/")]
            krl[rid] = material[:1]
            log["choices"].append(
                "KRL for %s (external reaction site %s) uses the retained body's own "
                "material; upstream names no interface for it"
                % (rid, rel.get("provider_reaction_site")))
    for joint in joints:
        jid = joint["entity_id"]
        if krl.get(jid):
            continue
        permitting = [p.get("at_interface") for p in phis
                      if str(p.get("effect")).upper() == "PERMIT_MOTION" and p.get("at_interface")]
        features = [f for iid in permitting for f in by_interface.get(iid, [])]
        if features:
            krl[jid] = features
            log["choices"].append("KRL for %s from PERMIT_MOTION at %s"
                                  % (jid, ", ".join(sorted(set(permitting)))))
    knum = 0
    for target, features in sorted(krl.items()):
        knum += 1
        ops.append(Op("CREATE", "KinematicRealization", "KRL-%04d" % knum,
                      {"realizes": target, "participating_features": features},
                      "pilot:translator", premise_refs=[target]))
    log["counts"]["kinematic_realizations"] = knum
    log["counts"]["constraints"] = cnum[0]
    log["assembly_sequence"] = plan.get("assembly_sequence") or []
    log["mating_sets"] = [{"name": m.get("name"),
                           "upstream": m.get("upstream_relationships"),
                           "participants": m.get("participants"),
                           "fit": m.get("fit")}
                          for m in (plan.get("mating_sets") or [])]

    # EVERY RECORD BELONGS TO THE BRANCH IT EMBODIES. Production carries the
    # candidate and the decision onto each op; without them the rows are
    # written but read as belonging to no branch, and every downstream reader
    # sees an empty embodiment.
    from ver3.assy_v3.stages.base import carry_invocation_premises
    ops = carry_invocation_premises(ops, [CID, decision])

    patch = StagePatch(patch_id="pilot-s05", run_id=state.run_id, stage_id="s05",
                       stage_attempt=1, parent_state_hash=state.state_hash(),
                       operations=ops, execution_status="SUCCESS",
                       provenance={"purpose": "pilot translation", "provider": "translator"})
    problems = state.validate(patch)
    log["write_boundary_problems"] = problems
    log["accepted"] = not problems
    if not problems:
        state.apply(patch)
    json.dump(log, open(os.path.join(OUT, os.environ.get("PILOT_LOG",
                                                        "translation_log.json")), "w"), indent=1,
              sort_keys=True, default=str)
    print("operations:", len(ops), "| accepted:", not problems)
    for p in problems[:12]:
        print("  REFUSED:", p[:190])
    return state, log


if __name__ == "__main__":
    st, lg = main()
    print(json.dumps(lg["counts"], indent=1))
