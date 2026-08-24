"""Run Window 2 (S03, then S04) on one case and report what happened.

A TOOL, not production code: it takes case identifiers, and a case identifier
inside assy_v3 is FP-02.

EVIDENCE DISCIPLINE
    Window 1 is frozen, so S01 and S02 are REPLAYED from their recorded
    responses. That is fixture evidence and is labelled as such. S03 and S04 are
    the stages under test and are run against the live provider. Mixing the two
    labels would let a frozen stage's quality be read as evidence about a new one.

    A candidate must be chosen before S03 can embody one, and INV-007 forbids
    choosing on quality before the s04a gate. So S03 is run ONCE PER CANDIDATE
    -- embodying is not selecting, and running every candidate is what keeps the
    design space open until the gate has evidence.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

from ver3.assy_v3.pipeline import (CHECK_FINDING, INTERFACE_FINDING,      # noqa: E402
                                   PARSER_DEFECT, Progression,
                                   full_live_qualification,
                                   s03_passes, s04_passes, window1)
from ver3.assy_v3.view import InvocationContext                            # noqa: E402
import yaml as _yaml                                                        # noqa: E402
_RESPONSIBILITY = _yaml.safe_load(open(os.path.join(
    REPO, "ver3", "contracts", "STAGE_RESPONSIBILITY_CONTRACT.yaml")))
from ver3.assy_v3.providers.offline import OfflineReplayProvider            # noqa: E402
from ver3.assy_v3.stages.s03_topology_and_mobility import (                 # noqa: E402
    assembly_acyclic_check,
    current_mobility_cells,
    disposition_completeness,
    legacy_shapes_in_recording,
    compliance_check, dof_totality_check, functional_region_check,
    interface_classification_check, joint_dof_consistency_check, load_path_check,
    no_magnitude_check, no_selection_check_s03, obligation_ownership_check,
    retention_check, simulation_completeness_check)
from ver3.assy_v3.stages.s04_envelope_and_motion import (                   # noqa: E402
    S04AEnvelopeAndReach, assembly_path_check,
    configuration_interference_check,
    envelope_coverage_check, joint_frame_check,
    spatial_commitment_check,
    load_path_reaction_check, motion_evidence_check, region_occupancy_check,
    swept_clearance_check)
from ver3.assy_v3.stages.feasibility import (                              # noqa: E402
    evaluate_candidate_feasibility)
from ver3.assy_v3.stages.selection import (                                 # noqa: E402
    ELIGIBILITY_NOT_ESTABLISHED, NO_ELIGIBLE_CANDIDATES,
    NO_SELECTION_PREFERENCES, PROFILE_MISSING,
    evaluate_candidate_comparison, materialize_selection_profile)
from ver3.assy_v3.stages.selection_advisory import (                        # noqa: E402
    ADVISORY_NOT_APPLICABLE, COMPARISON_AMBIGUOUS, SelectionEngineeringReview)
from ver3.assy_v3.stages.selection_decision import (                        # noqa: E402
    build_human_review_snapshot)
from ver3.assy_v3.assurance import run_assurance                            # noqa: E402
from ver3.assy_v3.assurance.status import report as assurance_report        # noqa: E402
from ver3.assy_v3.lifecycle.s7_reconcile import (                           # noqa: E402
    CURRENT_COMMITMENT, UNSPECIFIED, current_commitment, reconcile_s7)
from ver3.assy_v3.state import DesignState                                  # noqa: E402
from ver3.live_providers import env as env_loader                           # noqa: E402
from ver3.live_providers.deepseek import DeepSeekProvider                   # noqa: E402

FIXTURES = os.path.join(REPO, "ver3", "assy_v3", "fixtures", "responses")
PROBES = os.path.join(REPO, "ver3", "assy_v3", "probes")
BENCHMARKS = os.path.join(REPO, "ver3", "benchmarks")
ENV_FILE = os.path.join(REPO, "ver3", ".env")
OUT_ROOT = os.path.join(REPO, "ver3", "live_runs", "window2")

S03_CHECKS = (
    ("dof_totality", dof_totality_check),
    ("assembly_acyclic", assembly_acyclic_check),
    ("load_path", load_path_check),
    ("interface_classification", interface_classification_check),
    ("retention", retention_check),
    ("no_magnitude", no_magnitude_check),
    ("obligation_ownership", obligation_ownership_check),
    ("functional_region", functional_region_check),
    ("compliance", compliance_check),
    ("joint_dof_consistency", joint_dof_consistency_check),
    ("simulation_completeness", simulation_completeness_check),
    ("no_selection", no_selection_check_s03),
)


#: The ONLY families s04 may see. s04's engineering question is about the
#: mechanism, and if it cannot be answered from the mechanism then that is an
#: interface failure to record - not a licence to reach back to s01 or s02.
# U-3: RETIRED. `S03_OWNED` was a hand-written family tuple that decided what
# later stages could see. It could not express "the arrangement of the selected
# candidate", and it could not notice that a needed class was absent - which is
# how the quantities and the S04A arrangement were lost. Consumer context is now
# derived from the canonical contracts by assy_v3.view; nothing here names a
# family.
_RETIRED_S03_OWNED = "replaced by ConsumerView derivation (U-3)"

S04_CHECKS = (
    ("envelope_coverage", envelope_coverage_check),
    ("configuration_interference", configuration_interference_check),
    ("region_occupancy", region_occupancy_check),
    ("spatial_commitment", spatial_commitment_check),
    ("joint_frame", joint_frame_check),
    ("motion_evidence", motion_evidence_check),
    ("swept_clearance", swept_clearance_check),
    ("assembly_path", assembly_path_check),
    ("load_path_reaction", load_path_reaction_check),
)


def mechanism_projection(state):
    """The payload a stage prompt receives: a rendering of the ConsumerView."""
    return S04AEnvelopeAndReach().consumer_view(state).payload()


def interface_gaps(mech: Dict[str, Any]) -> List[str]:
    """What s04 needs and s03 did not supply. Recorded, never reconstructed."""
    gaps = []
    if not mech.get("Body"):
        gaps.append("s04a needs bodies to size; s03 produced none")
    if not mech.get("Configuration"):
        gaps.append("s04b needs configurations to place; s03 produced none")
    # s04a needs actor reach. s03 now carries it on the FunctionalRegion that
    # exists BECAUSE of the actor, so the gap is checked rather than assumed: it
    # is a gap only when no region declares an actor that needs it.
    access = [r for r in mech.get("FunctionalRegion", [])
              if r.get("role") in ("ACCESS", "APERTURE")]
    if access and not any(r.get("required_by_actors") for r in access):
        gaps.append("s04a requires actor_reach_requirements: s03 declared %d "
                    "ACCESS/APERTURE region(s) and none names the actor that "
                    "needs it, so reach cannot be evaluated from s03 output alone"
                    % len(access))
    elif not access:
        gaps.append("s04a requires actor_reach_requirements: s03 declared no "
                    "ACCESS or APERTURE region, so no reach requirement reached s04")
    return gaps


def recording_root(case_id: str) -> Optional[str]:
    for root in (FIXTURES, PROBES):
        if os.path.isfile(os.path.join(root, case_id, "s01.json")):
            return root
    return None


def request_text(case_id: str) -> Optional[str]:
    for p in (os.path.join(BENCHMARKS, case_id, "source", "request.txt"),
              os.path.join(PROBES, case_id, "request.txt")):
        if os.path.isfile(p):
            with open(p) as fh:
                return fh.read()
    return None


def discover_cases() -> List[str]:
    out = []
    for root in (FIXTURES, PROBES):
        if os.path.isdir(root):
            out += [d for d in os.listdir(root)
                    if os.path.isfile(os.path.join(root, d, "s02.json"))]
    return sorted(set(out))


def design_profile(case_id: str) -> Optional[Dict[str, Any]]:
    """The user's structured profile, beside the request it accompanies.

    Optional and read verbatim. A design that ships no profile states no hard
    requirement THROUGH THIS CHANNEL, which is a different fact from stating
    none at all - and the honest consequence is that no DesignConstraint exists
    to evaluate, not that one is inferred from the prose.
    """
    for name in ("design_profile.json", "design_profile.yaml"):
        for base in (os.path.join(BENCHMARKS, case_id, "source"),
                     os.path.join(PROBES, case_id)):
            path = os.path.join(base, name)
            if os.path.isfile(path):
                with open(path) as fh:
                    return _yaml.safe_load(fh)
    return None


def selection_preferences(profile: Optional[Dict[str, Any]]):
    """The stated preferences, or None when no source stated any.

    PRESENCE AND VALUE ARE DIFFERENT QUESTIONS, and truthiness cannot tell them
    apart. `{}` is falsy, so `profile.get("selection_preferences") or None`
    turned an explicit "I have preferences, and none of them is ranked" into "no
    preference source exists" - and the design lost a snapshot the user had
    actually supplied. The materialiser already distinguishes the two; the
    orchestration was collapsing them before it got there.

    Read by key presence, which is the only thing that answers "did the user
    supply this section".
    """
    if not isinstance(profile, dict):
        return None
    if "selection_preferences" not in profile:
        return None
    return profile["selection_preferences"]


def seed_window1(case_id: str, progression=None):
    """Replay S01 and S02 through the canonical progression.

    Returns (state, problems, progression). The progression is returned so the
    replayed response source travels with the run: a later live S03/S04 cannot
    make this chain full-live, and the record is what says so.
    """
    root = recording_root(case_id)
    text = request_text(case_id)
    if root is None or text is None:
        return None, ["no recording or request for %s" % case_id], progression or Progression()
    progression = progression or Progression()
    provider = OfflineReplayProvider(root, case_id)
    state = DesignState(run_id="w2-%s" % case_id)
    # THE PROFILE IS NOT REPLAYED, because it was never a model response. It is
    # structured user input, ingested deterministically beside the recording -
    # and now on the live path too, which previously ingested none.
    out1, out2 = window1(provider, state, text, progression,
                         design_profile=design_profile(case_id))
    if out1 is None or out1.patch is None:
        return None, ["s01 replay failed: %s" % (out1.problems if out1 else "raised")], progression
    if out2 is None or out2.patch is None:
        return None, ["s02 replay failed: %s" % (out2.problems if out2 else "raised")], progression
    return state, [], progression


def run_s03(case_id: str, candidate: Dict[str, Any], base_state,
            provider, trial: int, progression=None) -> Dict[str, Any]:
    """Embody ONE candidate INTO THE ACCUMULATED DESIGN. Never raises.

    THE PASSES THEMSELVES ARE THE PIPELINE'S. This function chooses the
    candidate, names the branch and reports; it no longer decides invocation
    order, patch acceptance or failure layer, because a runner that decided
    those was a second stage semantics.

    THE DEEP COPY IS GONE. Each candidate used to be embodied into a private
    `copy.deepcopy(base_state)`, so the run ended with N design states each
    holding one alternative and no state holding the design. Isolation between
    candidates is the ConsumerView's job - it is branch-scoped by construction -
    and copying the state to get it destroyed the design-wide question selection
    has to ask.
    """
    state = base_state
    progression = progression or Progression()
    rec: Dict[str, Any] = {"case": case_id, "candidate": candidate.get("entity_id"),
                           "trial": trial, "failures": [], "counts": {},
                           "s03a_status": None, "s03a_response": None}

    started = time.time()
    # The candidate is the explicit invocation identity: it anchors the branch,
    # it is what the stage records as a premise, and it is NOT engineering context.
    invocation = InvocationContext(branch=candidate.get("entity_id"))
    out_a, out_b = s03_passes(provider, state, progression, candidate,
                              invocation=invocation)

    rec["s03a_seconds"] = round(time.time() - started, 2)
    e_a = progression.by_responsibility("s03a")
    rec["s03a_status"] = e_a.execution_status if e_a else None
    rec["s03a_response"] = out_a.raw_response if out_a else None
    rec["s03a_consumer_view"] = out_a.consumer_view if out_a else None
    rec["s03a_declared_incomplete"] = out_a.declared_incompleteness if out_a else None
    rec["s03a_response_source"] = e_a.response_source if e_a else None

    if e_a is None or not e_a.patch_applied:
        rec["failures"] = progression.failures
        rec["_state"] = state
        return rec

    e_b = progression.by_responsibility("s03b")
    rec["s03b_status"] = e_b.execution_status if e_b else None
    rec["s03b_response"] = out_b.raw_response if out_b else None
    rec["s03b_consumer_view"] = out_b.consumer_view if out_b else None

    if e_b is not None and e_b.patch_applied and out_b is not None:
        try:
            parsed = json.loads(out_b.raw_response or "{}")
        except Exception:                                           # noqa: BLE001
            parsed = {}
        rec["constraint_relations_authored"] = len(
            parsed.get("constraint_relations") or [])
        cells = [d for op in out_b.patch.operations
                 if op.entity_type == "MobilityExpectation"
                 for d in (op.fields.get("dispositions") or [])]
        rec["dof_entries_derived"] = len(cells)
        # The CURRENT quantity, over standing grids, not only what this call
        # emitted. A run that withdrew topology has less current mobility than it
        # produced, and the record should say the smaller number.
        cells = current_mobility_cells(state)
        # THE ENGINEERING QUANTITY, reported and not checked. Domain totality is
        # guaranteed by the enumerator and says nothing; this says how much of the
        # domain rests on evidence and names the cells that do not.
        rec["disposition_completeness"] = disposition_completeness(cells)
        # S-9 CORPUS INFORMATION. What this recording holds of the shapes the
        # pipeline no longer speaks. It feeds no derivation, no check and no state.
        rec["legacy_shapes_in_recording"] = legacy_shapes_in_recording(parsed)

    for name, fn in S03_CHECKS:
        try:
            for p in fn(state):
                progression.fail(CHECK_FINDING, "s03", name, p)
        except Exception as exc:                                    # noqa: BLE001
            progression.fail(PARSER_DEFECT, "s03",
                             "check %s raised: %s" % (name, exc))
    rec["failures"] = progression.failures
    rec["counts"] = state.counts()
    # handed to s04 so the consumer works from the producer's actual state
    rec["_state"] = state
    return rec


def run_s04(case_id: str, state, provider, trial: int,
            invocation=None, progression=None, repair_rounds: int = 0,
            repair_provider=None, owner_revision_rounds: int = 0) -> Dict[str, Any]:
    """s04a then s04b, from the mechanism projection ONLY. Never raises.

    The refresh-on-refinement loop, the acceptance rule and the bounded repair
    loop live in the pipeline; what remains here is the interface report and
    the record. `repair_rounds` is OPT-IN for this runner: a replay campaign
    has recordings for the passes it asked and none for a repair it never
    asked, so the loop runs only when a caller says so, with the provider it
    names (None: derivation repairs only, and what remains stays open).
    `owner_revision_rounds` is opt-in the same way: the owner-revision loop
    (Unit C) runs after the repair loop, with the same `repair_provider`, and
    with None it identifies and routes what it would revise and stops.
    """
    progression = progression or Progression()
    rec: Dict[str, Any] = {"case": case_id, "trial": trial, "failures": [],
                           "s04a_status": None, "s04b_status": None,
                           "s04a_response": None, "s04b_response": None}

    mech = mechanism_projection(state)
    rec["projection_families"] = sorted(k for k, v in mech.items() if v)
    for gap in interface_gaps(mech):
        progression.fail(INTERFACE_FINDING, "s03->s04", gap)

    outcomes = s04_passes(provider, state, progression, invocation=invocation)
    last = outcomes[-1] if outcomes else None
    if repair_rounds > 0 and invocation is not None and last is not None \
            and last.patch is not None and not last.problems:
        from ver3.assy_v3.pipeline.repair import s04_repair_rounds
        rec["s04_repair"] = s04_repair_rounds(
            repair_provider, state, progression, invocation,
            rounds=repair_rounds).as_record()
    if owner_revision_rounds > 0 and invocation is not None and last is not None \
            and last.patch is not None and not last.problems:
        from ver3.assy_v3.pipeline.owner_revision import s03_owner_revision_rounds
        rec["s03_owner_revision"] = s03_owner_revision_rounds(
            repair_provider, state, progression, invocation,
            rounds=owner_revision_rounds,
            repair_rounds=max(repair_rounds, 2)).as_record()

    for key, out in zip(("s04a", "s04b"), list(outcomes) + [None, None]):
        execution = progression.by_responsibility(key)
        rec["%s_status" % key] = execution.execution_status if execution else None
        rec["%s_response" % key] = out.raw_response if out else None
        rec["%s_consumer_view" % key] = out.consumer_view if out else None
        rec["%s_response_source" % key] = execution.response_source if execution else None
        # THE REFINEMENTS THIS PASS ASKED FOR, read back from the progression
        # rather than counted by the loop that performed them. The refresh moved
        # into the pipeline at S9-C and this record did not follow it, so a run in
        # which s04b revised twice reported no refinement at all - the runner had
        # stopped being able to say the thing the barrier exists to make visible.
        refinements = [list(e.declared_incompleteness)
                       for e in progression.all_by_responsibility(key)
                       if e.refinement_only]
        if refinements:
            rec["%s_refinements" % key] = refinements
        if out is not None and out.patch is not None:
            rec["%s_families" % key] = sorted(
                {op.entity_type for op in out.patch.operations})

    for name, fn in S04_CHECKS:
        try:
            for p in fn(state):
                progression.fail(CHECK_FINDING, "s04", name, p)
        except Exception as exc:                                    # noqa: BLE001
            progression.fail(PARSER_DEFECT, "s04",
                             "check %s raised: %s" % (name, exc))
    rec["failures"] = progression.failures
    rec["counts"] = state.counts()
    return rec


def run_feasibility(case_id: str, state, trial: int,
                    invocation=None) -> Dict[str, Any]:
    """Ask whether ONE candidate is mechanically eligible. NO PROVIDER.

    The signature has no `provider` because there is nothing here to ask a model:
    a model may not declare a mechanism feasible, so the responsibility is a
    deterministic reading of what s01-s04 established.

    The runner APPLIES AND RECORDS. It does not read a domain verdict, does not
    aggregate one, and does not decide what an INFEASIBLE means for the run - a
    runner interpreting an engineering result is the second semantic authority
    U-7 removed from s04, and it would be the same defect here.
    """
    candidate = getattr(invocation, "branch", None)
    rec: Dict[str, Any] = {"case": case_id, "trial": trial, "candidate": candidate,
                           "failures": [], "feasibility_status": None}

    def fail(kind: str, what: str, detail: Any = None) -> None:
        rec["failures"].append({"kind": kind, "stage": "feasibility",
                                "what": what, "detail": detail})

    started = time.time()
    try:
        outcome = evaluate_candidate_feasibility(state, candidate)
    except Exception as exc:                                        # noqa: BLE001
        fail("PARSER_DEFECT", "%s: %s" % (type(exc).__name__, exc),
             traceback.format_exc(limit=5))
        rec["feasibility_status"] = "RAISED"
        return rec
    rec["feasibility_seconds"] = round(time.time() - started, 2)
    rec["feasibility_consumer_view"] = outcome.consumer_view
    if outcome.patch is None:
        # A REFUSAL IS A RESULT. An unready view means the design has not
        # established what a feasibility statement would have to be read from,
        # and producing one anyway is exactly what "missing evidence is not
        # feasibility" forbids.
        fail("CONTRACT_CONDITION", "no assessment was produced", outcome.problems)
        rec["feasibility_status"] = "NOT_PRODUCED"
        return rec
    state.apply(outcome.patch)
    rec["feasibility_status"] = outcome.status
    rec["feasibility_domains"] = {v.domain: v.status for v in outcome.verdicts}
    rec["feasibility_families"] = sorted({op.entity_type
                                          for op in outcome.patch.operations})
    rec["hard_requirements"] = {c.get("entity_id"): s
                                for c, s, _codes, _used, _why in outcome.compliance}
    rec["counts"] = state.counts()
    return rec


def run_selection(case_id: str, state, trial: int,
                  selection_preferences=None) -> Dict[str, Any]:
    """Materialise the preferences, then compare. NO PROVIDER, NO BRANCH.

    DESIGN-WIDE, and called ONCE for the whole case rather than once per
    candidate: comparison is the one question no single alternative can answer,
    and it is asked of the accumulated state every candidate was embodied into.

    The runner APPLIES AND RECORDS. It derives no eligibility, computes no
    metric, performs no dominance and names no winner - a runner doing any of
    those would be a second selection authority, and the outcome it printed would
    be the one nobody could trace to a patch.
    """
    rec: Dict[str, Any] = {"case": case_id, "trial": trial, "failures": [],
                           "profile_status": None, "comparison_status": None}

    def fail(kind: str, what: str, detail: Any = None) -> None:
        rec["failures"].append({"kind": kind, "stage": "selection",
                                "what": what, "detail": detail})

    started = time.time()
    try:
        profile = materialize_selection_profile(state, selection_preferences)
    except Exception as exc:                                        # noqa: BLE001
        fail("PARSER_DEFECT", "%s: %s" % (type(exc).__name__, exc),
             traceback.format_exc(limit=5))
        rec["profile_status"] = "RAISED"
        return rec
    rec["profile_status"] = profile.status
    rec["profile"] = profile.profile_id
    if profile.problems:
        fail("CONTRACT_CONDITION", "the stated preferences were not materialised",
             profile.problems)
    if profile.patch is not None:
        state.apply(profile.patch)

    try:
        comparison = evaluate_candidate_comparison(state)
    except Exception as exc:                                        # noqa: BLE001
        fail("PARSER_DEFECT", "%s: %s" % (type(exc).__name__, exc),
             traceback.format_exc(limit=5))
        rec["comparison_status"] = "RAISED"
        return rec
    rec["selection_seconds"] = round(time.time() - started, 2)
    rec["comparison_status"] = comparison.status
    rec["selection_consumer_view"] = comparison.consumer_view
    rec["eligible"] = list(comparison.eligible)
    rec["population"] = {k: v[0] for k, v in comparison.population.items()}
    if comparison.patch is None:
        # A RESULT IS NOT A FAILURE, and the runner has to know which is which.
        # A user who stated no preference, a population that is not established
        # and a design with no eligible candidate all leave nothing to compare -
        # and saying so IS the answer. It was recording each of them as a
        # contract failure because each carries problems explaining itself, which
        # made "the design has nothing to choose between" indistinguishable from
        # "the pipeline is broken".
        #
        # A missing profile is a result only when no preference was stated. If
        # one WAS stated and the comparison still cannot see it, that is a real
        # condition.
        results = [ELIGIBILITY_NOT_ESTABLISHED, NO_ELIGIBLE_CANDIDATES]
        if profile.status == NO_SELECTION_PREFERENCES:
            results.append(PROFILE_MISSING)
        if comparison.status not in results:
            fail("CONTRACT_CONDITION", comparison.status, comparison.problems)
        return rec
    state.apply(comparison.patch)
    # RECORDED, NOT INTERPRETED. `outcome` and `frontier` are copied out of the
    # entity the evaluator wrote; nothing here reads a metric or ranks anything.
    rec["outcome"] = comparison.outcome
    rec["frontier"] = list(comparison.frontier)
    rec["stopping_priority"] = comparison.stopping_priority
    rec["counts"] = state.counts()
    return rec


def run_selection_advisory(case_id: str, state, provider, trial: int) -> Dict[str, Any]:
    """Ask a reviewer what the deterministic comparison does not represent.

    ORCHESTRATION ONLY. The runner does not build the reasoning, does not check a
    supporting reference, does not downgrade an evidence status, does not compute
    whether the review agrees with the frontier and does not read the model's
    JSON. All of that is the producer's, behind the ordinary Stage boundary -
    which is also what guarantees the provider is not called on an unready view.

    NO COMPARISON, NO CALL. A design with nothing to compare has nothing to
    review, and that is a result rather than a failure: an advisory produced
    without a comparison would be a reviewer's opinion about a population nobody
    established.
    """
    rec: Dict[str, Any] = {"case": case_id, "trial": trial, "failures": [],
                           "advisory_status": None}

    def fail(kind: str, what: str, detail: Any = None) -> None:
        rec["failures"].append({"kind": kind, "stage": "selection_advisory",
                                "what": what, "detail": detail})

    comparisons = state.standing("CandidateComparison")
    if len(comparisons) != 1:
        # Asked of state rather than of the view so that "the provider was not
        # called" is recorded even before a view is built. The Stage boundary
        # would refuse it too; this says why in the run record.
        rec["advisory_status"] = (ADVISORY_NOT_APPLICABLE if not comparisons
                                  else COMPARISON_AMBIGUOUS)
        rec["comparisons"] = sorted(c["entity_id"] for c in comparisons)
        return rec

    started = time.time()
    try:
        out = SelectionEngineeringReview().invoke(provider, state, state.run_id)
    except Exception as exc:                                        # noqa: BLE001
        fail("PARSER_DEFECT", "%s: %s" % (type(exc).__name__, exc),
             traceback.format_exc(limit=5))
        rec["advisory_status"] = "RAISED"
        return rec
    rec["advisory_seconds"] = round(time.time() - started, 2)
    rec["advisory_status"] = out.execution_status.value
    rec["advisory_consumer_view"] = out.consumer_view
    rec["advisory_response"] = out.raw_response
    if out.patch is None:
        # A PROVIDER FAILURE IS NOT "NO CONCERN EXISTS". The comparison stands
        # untouched and the run records that the reviewer was asked and did not
        # answer - which is a different fact from being asked and finding nothing.
        fail("RESPONSE_CONDITION", out.execution_status.value, out.problems)
        return rec
    state.apply(out.patch)
    rec["advisory"] = [op.entity_id for op in out.patch.operations
                       if op.entity_type == "SelectionAdvisory"]
    rec["concerns"] = [op.entity_id for op in out.patch.operations
                       if op.entity_type == "SelectionConcern"]
    rec["counts"] = state.counts()
    return rec


AWAITING_HUMAN_DECISION = "AWAITING_HUMAN_DECISION"


def run_assurance_pass(case_id: str, state, trial: int,
                       attempts=()) -> Dict[str, Any]:
    """Ask the independent layer what the committed design establishes.

    AFTER THE STATE IS COMMITTED, and never before: assurance reads what the
    pipeline actually wrote, not what a stage was about to write. It authors
    nothing, calls no provider, and cannot change a verdict it is judging.

    The four constructs come back side by side. An engineering finding here does
    NOT touch the execution statuses recorded above it - a design whose geometry
    is wrong and a run whose provider timed out are two different situations, and
    one symbol that can mean both eventually means neither.
    """
    rec: Dict[str, Any] = {"case": case_id, "trial": trial, "failures": []}
    snapshot = run_assurance(state)
    rec["assurance"] = snapshot.as_dict()
    rec["status_constructs"] = assurance_report(snapshot, execution=list(attempts))
    rec["established_properties"] = snapshot.established()
    rec["engineering_findings"] = [f.as_dict() for f in snapshot.findings("FAIL")]
    return rec


def run_selection_checkpoint(case_id: str, state, trial: int) -> Dict[str, Any]:
    """Report whether a human could now be asked to decide. IT DOES NOT DECIDE.

    THE RUN STOPS HERE BY DESIGN. A batch process cannot answer the question this
    checkpoint asks, and the three ways it could pretend to - take the frontier,
    take the advisory's recommendation, take the sole eligible candidate - are the
    three things S7-E exists to prevent. Recording AWAITING_HUMAN_DECISION is the
    honest end of an unattended run: a design with one eligible candidate is still
    a design nobody has chosen.

    No submission is fabricated, so nothing here writes to state at all. What it
    produces is the readiness fact and the digest of the review a person would be
    shown, which is what makes it possible to tell later whether they were shown
    the same design this run produced.
    """
    rec: Dict[str, Any] = {"case": case_id, "trial": trial, "failures": [],
                           "checkpoint_status": None}
    review = build_human_review_snapshot(state)
    rec["review_status"] = review.status
    if not review.ready:
        rec["checkpoint_status"] = review.status
        rec["review_problems"] = review.problems
        return rec
    snapshot = review.snapshot
    rec["checkpoint_status"] = AWAITING_HUMAN_DECISION
    # WHAT IS ACTUALLY COMMITTED, and never what merely once was. A decision
    # whose premises moved is history: reporting it as the current commitment is
    # how a run tells a reader the design is settled when it has reopened.
    committed = current_commitment(state)
    rec["current_commitment"] = committed["entity_id"] if committed else None
    rec["historical_decisions"] = sorted(
        d["entity_id"] for d in state.family("SelectionDecision")
        if d.get("_validity") != "STANDING")
    if committed:
        rec["checkpoint_status"] = CURRENT_COMMITMENT
    rec["premise_digest"] = snapshot.digest
    rec["comparison"] = snapshot.comparison["entity_id"]
    rec["profile"] = snapshot.profile["entity_id"]
    rec["eligible_candidates"] = list(snapshot.eligible_candidates)
    rec["reviewed_advisories"] = snapshot.advisory_ids()
    rec["reviewed_concerns"] = snapshot.concern_ids()
    rec["counts"] = state.counts()
    return rec


def run_s7_reconcile(case_id: str, state, trial: int,
                     selection_preferences=UNSPECIFIED) -> Dict[str, Any]:
    """Re-establish what S-7 says after the design moved. IT STILL CANNOT CHOOSE.

    Orchestration only: the coordinator asks each owner to answer again over the
    current state, and this records what it reported. No provider is handed over,
    so no review is refreshed here - asking for an opinion is a person's decision.
    A run that reopens a commitment ends where the first one did, waiting for a
    human, because that is the only thing that can close it.
    """
    rec: Dict[str, Any] = {"case": case_id, "trial": trial, "failures": [],
                           "reconcile": None}
    out = reconcile_s7(state, selection_preferences=selection_preferences)
    rec["reconcile"] = out.as_dict()
    rec["checkpoint_status"] = out.human_state
    committed = current_commitment(state)
    rec["current_commitment"] = committed["entity_id"] if committed else None
    if out.problems:
        rec["failures"].append({"kind": "LIFECYCLE_CONDITION",
                                "stage": "s7_reconcile",
                                "what": "reconciliation reported problems",
                                "detail": out.problems})
    rec["counts"] = state.counts()
    return rec


#: RETIRED at S-6 / U-7. `_commit_s04` read the raw s04 response and wrote the
#: engineering facts the stages did not: the reference scale, reach results, the
#: elimination record, region volumes, insertion directions and joint origins. It
#: was a second semantic authority for one stage's output, and a caller that did
#: not know to run it got a DesignState missing all of them with nothing saying
#: so. Every one of those writes now happens inside the stage that concluded it,
#: through `to_operations` and `refinement_operations`, in the stage's own patch.
_RETIRED_COMMIT_S04 = "s04 commits its own conclusions (U-7)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", nargs="*", default=None)
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--candidates", type=int, default=1,
                    help="how many of each case's candidates to embody")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--label", default=None)
    args = ap.parse_args()

    names = env_loader.load(ENV_FILE)
    if names:
        print("loaded env: %s" % env_loader.describe(names))
    cases = args.cases or discover_cases()
    label = args.label or time.strftime("%Y%m%dT%H%M%S")
    out_dir = os.path.join(OUT_ROOT, label)
    os.makedirs(os.path.join(out_dir, "responses"), exist_ok=True)

    provider = DeepSeekProvider(temperature=args.temperature)
    print("s01+s02 REPLAYED (fixture evidence) | s03 LIVE (%s, T=%.1f)"
          % (provider.capabilities().model_id, args.temperature))

    trials: List[Dict[str, Any]] = []
    for trial in range(1, args.trials + 1):
        for case_id in cases:
            progression = Progression()
            base, problems, progression = seed_window1(case_id, progression)
            if base is None:
                print("  %-8s SEED FAILED: %s" % (case_id, problems))
                continue
            candidates = base.family("Candidate")[:args.candidates]
            accumulated = base
            for cand in candidates:
                t0 = time.time()
                rec = run_s03(case_id, cand, base, provider, trial,
                              progression=progression)
                for _k in ("s03a", "s03b"):
                    _raw = rec.pop("%s_response" % _k, None)
                    if _raw:
                        _d = os.path.join(out_dir, "responses", case_id,
                                          "t%d_%s" % (trial, rec["candidate"]))
                        os.makedirs(_d, exist_ok=True)
                        with open(os.path.join(_d, "%s.json" % _k), "w") as _fh:
                            _fh.write(_raw)
                raw = None
                if raw:
                    d = os.path.join(out_dir, "responses", case_id,
                                     "t%d_%s" % (trial, rec["candidate"]))
                    os.makedirs(d, exist_ok=True)
                    with open(os.path.join(d, "s03.json"), "w") as fh:
                        fh.write(raw)
                # CONTRACT_INCOMPLETE still yields an applied patch and a real
                # mechanism; refusing to consume it would hide whether s04 can
                # work from a declared-incomplete producer, which is exactly the
                # producer-consumer question this window is asking.
                _st = rec.pop("_state", None)
                if _st is not None:
                    # THE SAME OBJECT s03 EMBODIED INTO, and the same one every
                    # other candidate is embodied into. Selection needs one
                    # accumulated design, not N private ones.
                    accumulated = _st
                if _st is not None and rec.get("s03a_status") in ("SUCCESS", "CONTRACT_INCOMPLETE"):
                    # THE BRANCH IS NAMED BY THE CALLER. s04 embodies the same
                    # candidate s03 did, and before the S-7 gate there is no
                    # committed branch to read it from - so it is stated, not
                    # inferred from declaration order.
                    s4 = run_s04(case_id, _st, provider, trial,
                                 invocation=InvocationContext(
                                     branch=rec.get("candidate")),
                                 progression=progression)
                    rec["s04a_status"] = s4["s04a_status"]
                    rec["s04a_response_source"] = s4.get("s04a_response_source")
                    rec["s04b_response_source"] = s4.get("s04b_response_source")
                    rec["s04b_status"] = s4["s04b_status"]
                    rec["failures"] += s4["failures"]
                    rec["s04_counts"] = s4.get("counts")
                    for k in ("s04a", "s04b"):
                        raw = s4.get("%s_response" % k)
                        if raw:
                            d = os.path.join(out_dir, "responses", case_id,
                                             "t%d_%s" % (trial, rec["candidate"]))
                            os.makedirs(d, exist_ok=True)
                            with open(os.path.join(d, "%s.json" % k), "w") as fh:
                                fh.write(raw)
                    # UNCONDITIONAL ON THE CHECK FINDINGS. s04's checks report
                    # what they found; whether any of it stops the candidate is
                    # this responsibility's question, and skipping it when a
                    # check fired would answer that question in the runner.
                    fz = run_feasibility(case_id, _st, trial,
                                         invocation=InvocationContext(
                                             branch=rec.get("candidate")))
                    rec["feasibility_status"] = fz["feasibility_status"]
                    rec["feasibility_domains"] = fz.get("feasibility_domains")
                    rec["hard_requirements"] = fz.get("hard_requirements")
                    rec["failures"] += fz["failures"]
                # THE QUALIFICATION, from the recorded response sources. This
                # window replays S01 and S02, so it is always False here - and
                # saying so in the record is the point: a live S03/S04 must never
                # let a replayed upstream be read as end-to-end evidence.
                qualified, reasons = full_live_qualification(progression)
                rec["full_live"] = {"qualified": qualified, "reasons": reasons}
                rec["progression"] = progression.as_record()
                trials.append(rec)
                kinds: Dict[str, int] = {}
                for f in rec["failures"]:
                    kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
                print("  t%d %-8s %-9s s03=%-14s s04a=%-10s s04b=%-10s "
                      "feas=%-22s %5.1fs %s"
                      % (trial, case_id, rec["candidate"], rec["s03a_status"],
                         str(rec.get("s04a_status")), str(rec.get("s04b_status")),
                         str(rec.get("feasibility_status")),
                         time.time() - t0,
                         ", ".join("%s:%d" % kv for kv in sorted(kinds.items())) or "CLEAN"))
                with open(os.path.join(out_dir, "trials.json"), "w") as fh:
                    json.dump(trials, fh, indent=1, sort_keys=True)
                with open(os.path.join(out_dir, "model_run_records.json"), "w") as fh:
                    json.dump(provider.records, fh, indent=1, sort_keys=True)
            # ONCE PER CASE, after every candidate has been embodied into the one
            # accumulated design. Comparison is not a per-candidate act and there
            # is nothing to compare until the last alternative is in.
            sel = run_selection(case_id, accumulated, trial,
                                selection_preferences(design_profile(case_id)))
            print("  t%d %-8s SELECTION profile=%-24s comparison=%-26s %s"
                  % (trial, case_id, str(sel.get("profile_status")),
                     str(sel.get("comparison_status")),
                     "%s %s" % (sel.get("outcome") or "",
                                sel.get("frontier") or "")))
            trials.append(sel)
            # AFTER the comparison is applied, because reviewing what the metrics
            # do not say requires them to have said it.
            adv = run_selection_advisory(case_id, accumulated, provider, trial)
            print("  t%d %-8s ADVISORY %-28s %s"
                  % (trial, case_id, str(adv.get("advisory_status")),
                     "%s concern(s)" % len(adv.get("concerns") or [])))
            trials.append(adv)
            # THE END OF WHAT A BATCH RUN MAY DO. What comes next is a person's,
            # and the run records that it is waiting rather than inventing one.
            checkpoint = run_selection_checkpoint(case_id, accumulated, trial)
            print("  t%d %-8s CHECKPOINT %-26s %s"
                  % (trial, case_id, str(checkpoint.get("checkpoint_status")),
                     "digest=%s" % str(checkpoint.get("premise_digest"))[:12]))
            trials.append(checkpoint)
            # THE INDEPENDENT LAYER, LAST. Everything above it wrote; this only
            # reads, and what it reports is a separate axis rather than a
            # downgrade of anything already recorded.
            assured = run_assurance_pass(case_id, accumulated, trial,
                                         attempts=trials)
            print("  t%d %-8s ASSURANCE established=%-3d finding(s)=%d"
                  % (trial, case_id, len(assured["established_properties"]),
                     len(assured["engineering_findings"])))
            trials.append(assured)
            with open(os.path.join(out_dir, "trials.json"), "w") as fh:
                json.dump(trials, fh, indent=1, sort_keys=True)

    by_kind: Dict[str, int] = {}
    for t in trials:
        for f in t["failures"]:
            by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    print("\nfailures by kind: %s" % (by_kind or "none"))
    print("wrote %s" % os.path.relpath(out_dir, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
