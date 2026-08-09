"""Consumer Sufficiency (U-3 / M-3). The one semantic boundary between
accumulated DesignState and a consuming stage."""
from .consumer_view import (ConsumerView, RequiredMinimum, Requirement, Source,
                            Sufficiency, ViewStatus, build_consumer_view,
                            committed_branch, derive_required_minimum,
                            derive_source_a, derive_source_b, render,
                            select_instances)

__all__ = ["ConsumerView", "RequiredMinimum", "Requirement", "Source",
           "Sufficiency", "ViewStatus", "build_consumer_view", "committed_branch",
           "derive_required_minimum", "derive_source_a", "derive_source_b",
           "render", "select_instances"]
