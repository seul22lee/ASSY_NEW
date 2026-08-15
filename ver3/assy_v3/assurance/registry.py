"""EVERY CHECK, DECLARED. The registry is the contract, not the code below it.

S-8 / U-9 §14. A capability that is not here is not assurance, however
deterministic it is - and a capability here declares, before it runs, how far it
stands from the writer and what a pass entitles it to say.

TWO THINGS ARE DELIBERATELY ABSENT

    DOF TOTALITY. Every rigid group has every DOF disposed, which is a count.
    It was reported as assurance and establishes nothing; it stays where it is
    as BOOKKEEPING.

    THE SAMPLING DECLARATION. Retired, and retired means no capability - a
    constant declaring how densely a sweep was sampled was never evidence about
    a design.

Both absences are asserted by the closure suite, because "we removed it" and
"nobody noticed it was gone" look identical in a diff a year later.
"""
from __future__ import annotations

from typing import Dict, Tuple

from . import checks
from .model import (BOOKKEEPING, Check, ENGINEERING_CONSEQUENCE, EXTERNAL,
                    FIDELITY, PREMISE, PROVENANCE_INTEGRITY, STRUCTURAL)

REGISTRY: Tuple[Check, ...] = (
    Check(
        check_id="consumer_sufficiency",
        independence=STRUCTURAL,
        claim_class=BOOKKEEPING,
        property_scope="one declared consumer's required minimum reached its view",
        inputs=("STAGE_RESPONSIBILITY_CONTRACT", "DESIGN_STATE_CONTRACT",
                "the rebuilt ConsumerView"),
        authors=("contracts",),
        fn=checks.consumer_sufficiency),
    Check(
        check_id="reference_integrity",
        independence=STRUCTURAL,
        claim_class=PROVENANCE_INTEGRITY,
        property_scope="one standing entity's typed references resolve",
        inputs=("every standing family", "DESIGN_STATE_CONTRACT.field_semantics"),
        authors=("contracts",),
        fn=checks.reference_integrity),
    Check(
        check_id="quantitative_continuity",
        independence=STRUCTURAL,
        claim_class=FIDELITY,
        property_scope="one load case's magnitude kept the hedge its requirement carried",
        inputs=("Requirement (s01)", "LoadCase (s02)"),
        authors=("s01", "s02"),
        fn=checks.quantitative_continuity),
    Check(
        check_id="mobility_disposition_completeness",
        independence=STRUCTURAL,
        claim_class=PROVENANCE_INTEGRITY,
        property_scope="one disposition cell traces to a resolvable premise",
        inputs=("MobilityExpectation (s03b)", "ConstraintRelation (s03)",
                "Body (s03)"),
        authors=("s03",),
        fn=checks.mobility_disposition_completeness),
    Check(
        check_id="physical_relation_closure",
        independence=PREMISE,
        claim_class=ENGINEERING_CONSEQUENCE,
        property_scope="one required physical effect is discharged or explicitly open",
        inputs=("PhysicalEffectObligation (s02)", "PhysicalInteraction (s03b)",
                "UnresolvedDecision"),
        authors=("s02", "s03"),
        fn=checks.physical_relation_closure),
    Check(
        check_id="mobility_cross_premise_consistency",
        independence=PREMISE,
        claim_class=ENGINEERING_CONSEQUENCE,
        property_scope="one DOF is not irrelevant under a load that acts on it",
        inputs=("LoadCase (s02)", "Scenario (s01)",
                "MobilityExpectation (s03b)"),
        authors=("s02", "s03"),
        fn=checks.mobility_cross_premise_consistency),
    Check(
        check_id="topology_to_spatial_fidelity",
        independence=PREMISE,
        claim_class=ENGINEERING_CONSEQUENCE,
        property_scope="one declared body incidence is realized in the arrangement",
        inputs=("Joint / Interface (s03a)", "Envelope (s04a)"),
        authors=("s03", "s04"),
        fn=checks.topology_to_spatial_fidelity),
    Check(
        check_id="required_distinctness_non_degeneracy",
        independence=PREMISE,
        claim_class=ENGINEERING_CONSEQUENCE,
        property_scope="one DECLARED distinctness premise survives realization",
        inputs=("Configuration.distinguishing_basis (s03)", "State (s04b)",
                "Joint (s03a)"),
        authors=("s03", "s04"),
        fn=checks.required_distinctness_non_degeneracy),
    Check(
        check_id="state_configuration_realization",
        independence=PREMISE,
        claim_class=ENGINEERING_CONSEQUENCE,
        property_scope="one declared configuration or transition is realized as declared",
        inputs=("Configuration (s03)", "Transition (s04b)", "State (s04b)"),
        authors=("s03", "s04"),
        fn=checks.state_configuration_realization),
    Check(
        check_id="reach_demand_realization",
        independence=PREMISE,
        claim_class=ENGINEERING_CONSEQUENCE,
        property_scope="one stated reach demand is answered by the arrangement",
        inputs=("Actor.must_reach (s01)", "ReachResult (s04a)"),
        authors=("s01", "s04"),
        fn=checks.reach_demand_realization),
    Check(
        check_id="commitment_validity",
        independence=EXTERNAL,
        claim_class=ENGINEERING_CONSEQUENCE,
        property_scope="one standing commitment's preconditions hold now",
        inputs=("SelectionDecision", "HumanDecisionInput",
                "MechanicalFeasibilityAssessment", "HardRequirementCompliance",
                "DesignConstraint"),
        authors=("selection", "feasibility"),
        fn=checks.commitment_validity),
)

#: Capabilities that were counted as assurance and are not. Named rather than
#: deleted quietly, because a removal nobody can see is a removal nobody can
#: check.
NOT_ASSURANCE: Dict[str, str] = {
    "dof_totality": "BOOKKEEPING. Every rigid group has every DOF disposed is a "
                    "count of cells, and a complete count of unexamined claims "
                    "is not evidence about a design.",
    "sampling_declaration": "RETIRED. A constant declaring how densely a sweep "
                            "was sampled describes the computation, never the "
                            "sufficiency of its evidence for any property.",
}


def validate() -> None:
    """Every declaration is complete and inside the closed vocabularies."""
    seen = set()
    for check in REGISTRY:
        check.validate()
        if check.check_id in seen:
            raise ValueError("duplicate check id %r" % check.check_id)
        seen.add(check.check_id)
    overlap = seen & set(NOT_ASSURANCE)
    if overlap:
        raise ValueError("registered as assurance and declared not assurance: %s"
                         % sorted(overlap))


validate()
