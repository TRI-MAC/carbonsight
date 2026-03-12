"""Core node system for CarbonSight's DAG-based simulation engine.

Provides typed nodes (scalar, timeseries, distribution, dataframe) with
distribution-native values and compute function auto-wiring.
"""

from __future__ import annotations

import enum
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd

from carbonsight.core.distributions import Distribution


class NodeType(enum.Enum):
    SCALAR = "scalar"
    TIMESERIES = "timeseries"
    DISTRIBUTION = "distribution"
    DATAFRAME = "dataframe"


VALID_NODE_TYPES = {t.value for t in NodeType}

# Prefix used to declare temporal (lagged) dependencies in compute functions.
TEMPORAL_PREFIX = "prev_"


@dataclass
class DataSource:
    """Metadata about the origin of a node's value."""

    name: str
    publication_date: str | None = None
    version: str | None = None
    url: str | None = None
    transformations: str | None = None


@dataclass
class Assumption:
    """A documented modeling assumption for a node."""

    description: str
    rationale: str
    confidence: str = "medium"  # high, medium, low


@dataclass
class Node:
    """A typed node in the CarbonSight simulation DAG.

    Nodes hold values (or distributions over values) and optionally a compute
    function that derives the value from upstream nodes.
    """

    name: str
    node_type: NodeType
    compute_fn: Callable | None = None
    value: Any = None
    initial_value: Any = None  # Used for temporal edge resolution at year 0
    data_source: DataSource | None = None
    assumptions: list[Assumption] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Resolved by the graph at construction time
    upstream_edges: list[str] = field(default_factory=list)
    temporal_edges: list[str] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.node_type, str):
            if self.node_type not in VALID_NODE_TYPES:
                raise ValueError(
                    f"Invalid node type '{self.node_type}'. "
                    f"Must be one of: {', '.join(sorted(VALID_NODE_TYPES))}"
                )
            self.node_type = NodeType(self.node_type)

        if self.compute_fn is not None:
            self._resolve_edges()

    def _resolve_edges(self):
        """Auto-wire compute function parameters to upstream node names."""
        sig = inspect.signature(self.compute_fn)
        self.upstream_edges = []
        self.temporal_edges = []

        for param_name in sig.parameters:
            if param_name == "self":
                continue
            if param_name.startswith(TEMPORAL_PREFIX):
                # Temporal edge: prev_foo -> references node "foo" from prior year
                source_node = param_name[len(TEMPORAL_PREFIX):]
                self.temporal_edges.append(source_node)
            else:
                self.upstream_edges.append(param_name)

    @property
    def is_input(self) -> bool:
        """True if this node has no compute function (leaf/input node)."""
        return self.compute_fn is None

    @property
    def all_dependencies(self) -> list[str]:
        """All node names this node depends on (within-step + temporal source names)."""
        return self.upstream_edges + self.temporal_edges

    def set_value(self, value: Any):
        """Set the node's value, coercing to distribution if appropriate."""
        if self.node_type == NodeType.DISTRIBUTION and isinstance(value, (int, float)):
            # Degenerate (point) distribution
            self.value = Distribution.point(float(value))
        else:
            self.value = value

    def get_point_estimate(self) -> Any:
        """Return the point estimate of the node's value.

        For distribution-typed nodes, returns the mean. For others, returns the value as-is.
        """
        if self.node_type == NodeType.DISTRIBUTION and isinstance(self.value, Distribution):
            return self.value.mean()
        return self.value

    def sample(self, n: int, rng: np.random.Generator | None = None) -> np.ndarray:
        """Draw n samples from the node's distribution.

        Only valid for distribution-typed nodes.
        """
        if not isinstance(self.value, Distribution):
            raise TypeError(f"Node '{self.name}' does not hold a Distribution, cannot sample.")
        return self.value.sample(n, rng=rng)


def _to_snake_case(name: str) -> str:
    """Convert a display name to snake_case for parameter matching."""
    import re

    s = re.sub(r"[^a-zA-Z0-9]", "_", name)
    s = re.sub(r"_+", "_", s).strip("_").lower()
    return s
