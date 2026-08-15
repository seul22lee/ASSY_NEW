"""The Streamlit human checkpoint. AN ENTRY POINT, and nothing more.

    streamlit run ver3/tools/selection_checkpoint.py

Everything this file does is hand `streamlit` to `assy_v3.ui.selection_checkpoint`
as the drawing surface and hand it a live DesignState. The page logic, what may be
shown, what a person may submit and what happens to it are all in the package,
because a tool that carried any of that would be a second decision path beside the
one the architecture declares.

ABOUT THE STATE THIS SCREEN IS GIVEN

There is no cross-process DesignState persistence in this window. This entry
point is therefore explicit about its boundary: it decides on a LIVE DesignState
handed to it in-process, and it does not attempt to reconstruct one. Rebuilding a
design from trial summaries or from stored model responses would be inventing the
premises a human is about to approve, which is precisely what the digest exists to
prevent. Wiring this page to a persisted design is orchestration work and is not
S7-E's to invent.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from ver3.assy_v3.ui import selection_checkpoint as checkpoint_ui  # noqa: E402

TITLE = "Selection checkpoint"
INTRO = ("You are being asked to choose. Nothing below has decided anything: the "
         "comparison says what the metrics could tell apart, the advisory is a "
         "reviewer's opinion, and neither is a selection until you make one.")

#: How a caller hands this page the design it is deciding about. Set by an
#: embedding process before the page runs; there is no fallback that invents one.
STATE_PROVIDER = None


def design_state() -> Optional[Any]:
    """The live DesignState this page decides about, or None.

    NO RECONSTRUCTION. If nothing supplied a state, the page says so and shows no
    controls - an empty screen is a truthful answer, and a design assembled here
    from whatever happened to be on disk would be a different design from the one
    anybody reviewed.
    """
    return STATE_PROVIDER() if callable(STATE_PROVIDER) else None


def main() -> None:                                              # pragma: no cover
    import streamlit as st

    st.set_page_config(page_title=TITLE)
    st.title(TITLE)
    st.markdown(INTRO)

    state = design_state()
    if state is None:
        st.warning(
            "No live design is attached to this checkpoint. Attach one by "
            "setting STATE_PROVIDER before the page runs; this screen does not "
            "reconstruct a design from run artefacts.")
        return

    outcome = checkpoint_ui.checkpoint(st, state)
    st.caption("Screen status: %s" % outcome.status)


if __name__ == "__main__":                                       # pragma: no cover
    main()
