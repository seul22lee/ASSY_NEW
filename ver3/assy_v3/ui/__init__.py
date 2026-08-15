"""Screens. ADAPTERS ONLY.

A module in here may render what a backend assembled and may pass what a person
typed back to a backend function. It may not decide anything: no eligibility, no
comparison, no commitment, and no operation on authoritative state that a
deterministic writer did not produce.

The rule is structural rather than a convention. Everything a screen shows comes
from one immutable object it is handed, and the only thing it can cause to be
written is what the human controlled.
"""
