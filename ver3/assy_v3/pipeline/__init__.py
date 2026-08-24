"""The canonical stage progression: one implementation, two response sources.

Before S-9 the S01->S02 progression existed three times - once in the replay
runner, once in the live runner, once inside Window 2's seeding function - and no
runner reached S04 from a live S01 at all. Three copies of a progression are three
opportunities for one of them to drift, and one of them already had: the live S01
path called the stage's inner driver directly and so never built a ConsumerView.

This package owns the progression. A runner chooses a response source and a case;
it does not decide stage order, patch acceptance, view construction or failure
classification, because those are semantics rather than harness concerns.
"""
from .progression import (LIVE, PRODUCING_RESPONSIBILITIES, REPLAY, UNDECLARED,
                          CHECK_FINDING, CONTRACT_CONDITION, INTERFACE_FINDING,
                          PARSER_DEFECT, PROVIDER_CONDITION, RESPONSE_CONDITION,
                          VIEW_INSUFFICIENT,
                          Progression, StageExecution, execute_s01_to_s04,
                          execute_stage, full_live_qualification, note_seeded,
                          response_source_of, s03_passes, s04_passes, window1)
from .repair import RepairOutcome, RepairRound, s04_repair_rounds

__all__ = ["LIVE", "REPLAY", "UNDECLARED", "PRODUCING_RESPONSIBILITIES",
           "PROVIDER_CONDITION", "RESPONSE_CONDITION", "PARSER_DEFECT",
           "CONTRACT_CONDITION", "CHECK_FINDING", "INTERFACE_FINDING",
           "VIEW_INSUFFICIENT",
           "Progression", "StageExecution", "execute_stage", "note_seeded",
           "window1", "s03_passes", "s04_passes", "s04_repair_rounds",
           "RepairOutcome", "RepairRound", "execute_s01_to_s04",
           "full_live_qualification", "response_source_of"]
