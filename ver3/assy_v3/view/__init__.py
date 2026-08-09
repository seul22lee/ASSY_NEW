"""Consumer Sufficiency (U-3 / M-3). The one semantic boundary between
accumulated DesignState and a consuming stage."""
from .consumer_view import (ConsumerView, InvocationContext, RequiredMinimum, Requirement, Source,
                            Sufficiency, ViewStatus, build_consumer_view,
                            committed_branch, derive_required_minimum,
                            derive_source_a, derive_source_b, render,
                            select_instances)
from .boundary import consumer_view_for, responsibility_contract

__all__ = ["ConsumerView", "InvocationContext", "RequiredMinimum", "Requirement", "Source",
           "Sufficiency", "ViewStatus", "build_consumer_view", "committed_branch",
           "derive_required_minimum", "derive_source_a", "derive_source_b",
           "render", "select_instances",
           "consumer_view_for", "responsibility_contract"]
