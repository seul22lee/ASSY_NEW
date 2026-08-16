"""What each producing responsibility can actually CREATE, read from its code.

Test infrastructure, not production code. Nothing here is Stage logic.

WHY THIS EXISTS

`STAGE_RESPONSIBILITY_CONTRACT.permitted_output_semantics` is a DECLARATION of
what a responsibility may put into DesignState. Nothing checked it against the
code, so the two could disagree indefinitely and the disagreement would only
surface when an independent model was asked the question - which is exactly how
S9-E found s02 authoring `Assumption` while its own contract said it authored no
such thing.

An assertion naming the family would not be a guard. It would be the same hand
maintenance that produced the drift, written once more. So this DERIVES the
answer from the source: every `Op("CREATE", "<Family>", ...)` reachable from a
responsibility's own class, including the module-level helpers that class calls.

WHY AST AND NOT IMPORT-AND-INSPECT

The families a stage creates are decided by branches over a parsed response, so
no import-time inspection can enumerate them - you would have to run the stage
against every possible response. The literal is right there in the source, and
reading it is exact for every producer written in the one shape the package uses.

A producer that built the family name dynamically would be invisible here. That
is reported rather than ignored: `dynamic_creates` carries every CREATE whose
family is not a literal, so "the scan found nothing" can never be confused with
"the scan could not look".
"""

import ast
import os
from typing import Dict, List, Set, Tuple

from . import _paths

STAGES_DIR = os.path.join(_paths.ASSY_V3, "stages")

#: The op kind that puts a NEW entity id into the namespace. EXTEND, SUPERSEDE
#: and INVALIDATE act on an entity that already exists, so they neither declare
#: an output family nor occupy an id.
CREATE = "CREATE"


def _is_op_call(node: ast.AST) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "Op")


def _literal(node: ast.AST):
    return node.value if isinstance(node, ast.Constant) else None


def _scan_body(node: ast.AST) -> Tuple[Set[str], Set[str], Set[str]]:
    """(families created, calls made, dynamic-create sites) inside one node."""
    families: Set[str] = set()
    calls: Set[str] = set()
    dynamic: Set[str] = set()
    for sub in ast.walk(node):
        if _is_op_call(sub):
            args = sub.args
            if len(args) >= 2 and _literal(args[0]) == CREATE:
                fam = _literal(args[1])
                if isinstance(fam, str):
                    families.add(fam)
                else:
                    dynamic.add("line %d" % getattr(sub, "lineno", 0))
        elif isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Name):
                calls.add(sub.func.id)
            elif isinstance(sub.func, ast.Attribute):
                calls.add(sub.func.attr)
    return families, calls, dynamic


def _module_helpers(tree: ast.Module) -> Dict[str, Tuple[Set[str], Set[str], Set[str]]]:
    """Every module-level function, and what it creates directly."""
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = _scan_body(node)
    return out


def _closure(direct: Set[str], calls: Set[str],
             helpers: Dict[str, Tuple[Set[str], Set[str], Set[str]]],
             dynamic: Set[str]) -> Tuple[Set[str], Set[str]]:
    """Follow calls into module-level helpers until nothing new appears.

    A stage that hands its DesignConstraint authorship to a module function still
    creates DesignConstraint. Charging it only for what its own method body spells
    out would let any producer disappear behind one indirection.
    """
    families = set(direct)
    seen: Set[str] = set()
    frontier = set(calls)
    while frontier:
        name = frontier.pop()
        if name in seen or name not in helpers:
            continue
        seen.add(name)
        fams, more, dyn = helpers[name]
        families |= fams
        dynamic |= dyn
        frontier |= more
    return families, dynamic


def creates_by_class() -> Dict[str, Dict[str, object]]:
    """Per Stage subclass: the families it can CREATE, and where it was found.

    Keyed by CLASS NAME. Mapping a class to the responsibility it answers for is
    the caller's job and is asked of the class itself, so this file holds no table
    of which pass belongs to which contract.
    """
    out: Dict[str, Dict[str, object]] = {}
    for fn in sorted(os.listdir(STAGES_DIR)):
        if not fn.endswith(".py"):
            continue
        path = os.path.join(STAGES_DIR, fn)
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        helpers = _module_helpers(tree)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            direct, calls, dynamic = _scan_body(node)
            families, dynamic = _closure(direct, calls, helpers, dynamic)
            out[node.name] = {"module": fn, "creates": families,
                              "dynamic_creates": sorted(dynamic)}
    return out


def responsibility_creates(stage_classes) -> Dict[str, Set[str]]:
    """(responsibility id -> creatable families) for the given Stage classes.

    The caller supplies the classes so this stays a pure reader: it imports no
    stage module and decides no membership. `responsibility_id()` is the class's
    own answer, and it is the same one `Stage.invoke` uses to choose a contract.
    """
    scanned = creates_by_class()
    out: Dict[str, Set[str]] = {}
    for cls in stage_classes:
        found = scanned.get(cls.__name__)
        if found is None:
            raise AssertionError(
                "%s is a producing stage class and no source scan found it; the "
                "scan looks in %s" % (cls.__name__, STAGES_DIR))
        out[cls.responsibility_id()] = set(found["creates"])
    return out


def dynamic_create_sites(stage_classes) -> Dict[str, List[str]]:
    """Where a CREATE names its family with something other than a literal.

    Empty is the claim that the scan above is COMPLETE for these classes. A
    non-empty result means a producer exists that this file cannot read, and the
    comparison it feeds must not be reported as exhaustive.
    """
    scanned = creates_by_class()
    return {cls.__name__: list(scanned[cls.__name__]["dynamic_creates"])
            for cls in stage_classes
            if scanned.get(cls.__name__) and scanned[cls.__name__]["dynamic_creates"]}


def declared_families(responsibility: dict, responsibility_id: str) -> Set[str]:
    """The FAMILY-level entries of a responsibility's permitted output semantics.

    `permitted_output_semantics` mixes two kinds of entry, and they are different
    claims. `Envelope` is a family this responsibility may bring into existence.
    `Joint.frame_origin` is a FIELD it may author onto a Joint that another
    responsibility created - an EXTEND, which occupies no id and creates no
    family. Only the first kind is comparable with a CREATE.
    """
    stage = (responsibility.get("stages") or {}).get(responsibility_id) or {}
    return {s.split(".", 1)[0] for s in stage.get("permitted_output_semantics", [])
            if "." not in s}


def declared_fields(responsibility: dict, responsibility_id: str) -> Set[str]:
    """The FIELD-level entries - what this responsibility may write onto others."""
    stage = (responsibility.get("stages") or {}).get(responsibility_id) or {}
    return {s for s in stage.get("permitted_output_semantics", []) if "." in s}


def owner_of(responsibility_id: str) -> str:
    """The stage whose write authority a responsibility acts under.

    `s03a` and `s03b` are two responsibilities of one owner; the split is a
    trailing pass letter and nothing else. Read back rather than tabulated, which
    is how `assy_v3.view.consumer_view` does it too.
    """
    import re
    return (responsibility_id[:-1] if re.match(r"^s\d+[a-z]$", responsibility_id)
            else responsibility_id)


def may_create(ownership: dict, stage_id: str) -> Set[str]:
    """Every family the WRITE BOUNDARY would let this stage create.

    The union of what the stage owns and what any stage may own. This is the
    enforced authority - `DesignState.validate` refuses a CREATE outside it - so
    it is the ceiling a declaration may not exceed.
    """
    owns = set((ownership.get("stages") or {}).get(stage_id, {}).get("owns") or [])
    return owns | universally_ownable(ownership)


def drift_problems(responsibility_id: str, actual: Set[str], declared: Set[str],
                   authorized: Set[str], universal: Set[str]) -> List[str]:
    """Everything that makes a declaration and its implementation disagree.

    A PURE FUNCTION of four sets, so the guard can be run against a MUTATED
    contract and shown to reject it. A guard only ever exercised on a passing
    repository is a guard nobody has seen fail.

    THREE RULES, and they are not one rule stated three ways.

    1. UNDECLARED PRODUCTION. The code creates a family the declaration omits.
       This is the S9-E defect: `permitted_output_semantics` is what
       `derive_source_a` reads to decide what a consumer co-produces, so an
       omission does not merely mis-document - it changes what the view carries.

    2. DECLARED BEYOND AUTHORITY. The declaration claims a family the write
       boundary would refuse. Harmless in the sense that nothing can be written,
       and dangerous in that the contract promises an output that cannot exist.

    3. DECLARED AND NOT PRODUCED, where the family is not universally ownable.
       Exact equality is NOT the rule, because it would be false: a
       `universally_ownable` family is a standing permission every stage holds
       whether or not it exercises it, and s01 declares `UnresolvedDecision`
       without producing one. But a STAGE-SPECIFIC family in the list that
       nothing produces is a claim about this responsibility that is not true,
       and that is the case this rule keeps.
    """
    problems: List[str] = []
    for family in sorted(actual - declared):
        problems.append(
            "%s creates %s and does not declare it in permitted_output_semantics"
            % (responsibility_id, family))
    for family in sorted(declared - authorized):
        problems.append(
            "%s declares output %s that STAGE_OWNERSHIP_MATRIX would refuse"
            % (responsibility_id, family))
    for family in sorted((declared - actual) - universal):
        problems.append(
            "%s declares %s and no code path creates it; it is not universally "
            "ownable, so this is a claim about this responsibility rather than a "
            "standing permission" % (responsibility_id, family))
    return problems


def universally_ownable(ownership: dict) -> Set[str]:
    """Families any stage may create, read from the matrix's own declaration.

    Entries are a list of mappings; some carry `family`, and one carries only a
    `constraint` note. Reading the note as a family name would invent one.
    """
    return {row["family"] for row in (ownership.get("universally_ownable") or [])
            if isinstance(row, dict) and row.get("family")}
