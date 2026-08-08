"""Engineering knowledge, kept out of the reasoning process.

The stages ask general engineering questions. What a revolute joint is, which
principle families can convert rotary motion to linear, and which analysis routes
this toolchain actually has are FACTS ABOUT MECHANISMS AND ABOUT THE TOOLCHAIN,
not facts about any product. They live here so that no stage prompt has to carry
them and no product-specific shortcut can hide in one.
"""
from .capability_registry import EVIDENCE_ROUTES, route_for_claim   # noqa: F401
from .principle_library import (                                    # noqa: F401
    PRINCIPLE_FAMILIES, families_for_function, FUNCTION_CLASSES)
