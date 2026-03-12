"""DAG construction, validation, and execution for CarbonSight.

Builds a directed acyclic graph from Node definitions, validates for cycles
(within-step edges only), checks type compatibility, and executes in
topological order.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from carbonsight.core.node import Node, NodeType


class GraphValidationError(Exception):
    """Raised when the graph fails structural validation."""


class CycleError(GraphValidationError):
    """Raised when within-step edges form a cycle."""


class TypeMismatchError(GraphValidationError):
    """Raised when connected nodes have incompatible types."""


class MissingNodeError(GraphValidationError):
    """Raised when a compute function references a node that doesn't exist."""


class MissingInitialValueError(GraphValidationError):
    """Raised when a temporal edge has no initial value for year 0."""


@dataclass
class ProvenanceRecord:
    """Records how a single node was computed in a single execution."""

    node_name: str
    timestamp: float | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    temporal_inputs: dict[str, dict] = field(default_factory=dict)  # name -> {value, source_year}
    compute_fn_name: str | None = None


class SimulationGraph:
    """A directed acyclic graph of typed nodes for fleet carbon simulation.

    The graph supports two edge types:
    - Within-step edges: standard dependencies resolved in the current time step
    - Temporal edges: dependencies on a node's value from the previous time step

    Cycle detection applies only to within-step edges.
    """

    def __init__(self):
        self._nodes: dict[str, Node] = {}
        self._dag = nx.DiGraph()  # Within-step edges only (for cycle detection + topo sort)
        self._validated = False

    def add_node(self, node: Node):
        """Register a node in the graph."""
        self._nodes[node.name] = node
        self._dag.add_node(node.name)
        self._validated = False

    def get_node(self, name: str) -> Node:
        """Retrieve a node by name."""
        if name not in self._nodes:
            raise MissingNodeError(f"Node '{name}' not found in graph")
        return self._nodes[name]

    @property
    def nodes(self) -> dict[str, Node]:
        return dict(self._nodes)

    def validate(self):
        """Validate the graph structure.

        Checks:
        1. All upstream references resolve to existing nodes
        2. All temporal references resolve to existing nodes with initial values
        3. No cycles among within-step edges
        4. Type compatibility on edges
        """
        # Check that all referenced nodes exist
        for node in self._nodes.values():
            for upstream in node.upstream_edges:
                if upstream not in self._nodes:
                    raise MissingNodeError(
                        f"Node '{node.name}' references upstream node '{upstream}' "
                        f"which does not exist"
                    )
            for temporal_src in node.temporal_edges:
                if temporal_src not in self._nodes:
                    raise MissingNodeError(
                        f"Node '{node.name}' references temporal node '{temporal_src}' "
                        f"which does not exist"
                    )
                src_node = self._nodes[temporal_src]
                if src_node.initial_value is None and src_node.value is None and src_node.compute_fn is not None:
                    raise MissingInitialValueError(
                        f"Node '{node.name}' has temporal dependency on '{temporal_src}' "
                        f"but no initial value is provided for '{temporal_src}'"
                    )

        # Build within-step edge graph and check for cycles
        self._dag = nx.DiGraph()
        for name in self._nodes:
            self._dag.add_node(name)
        for node in self._nodes.values():
            for upstream in node.upstream_edges:
                self._dag.add_edge(upstream, node.name)

        if not nx.is_directed_acyclic_graph(self._dag):
            cycles = list(nx.simple_cycles(self._dag))
            cycle_nodes = cycles[0] if cycles else []
            raise CycleError(
                f"Cycle detected among within-step edges involving nodes: "
                f"{', '.join(cycle_nodes)}"
            )

        self._validated = True

    def topological_order(self) -> list[str]:
        """Return nodes in topological execution order (within-step edges)."""
        if not self._validated:
            self.validate()
        return list(nx.topological_sort(self._dag))

    def execute(
        self,
        overrides: dict[str, Any] | None = None,
        prior_year_outputs: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], list[ProvenanceRecord]]:
        """Execute the graph once, returning outputs and provenance.

        Args:
            overrides: Optional dict of node_name -> value to override input nodes.
            prior_year_outputs: Optional dict of node_name -> value from previous year,
                used to resolve temporal edges. If None, uses initial_value or current value.

        Returns:
            Tuple of (outputs dict, provenance records list).
        """
        import time

        if not self._validated:
            self.validate()

        outputs: dict[str, Any] = {}
        provenance: list[ProvenanceRecord] = []
        overrides = overrides or {}

        for node_name in self.topological_order():
            node = self._nodes[node_name]
            record = ProvenanceRecord(
                node_name=node_name,
                timestamp=time.time(),
                compute_fn_name=node.compute_fn.__name__ if node.compute_fn else None,
            )

            if node_name in overrides:
                outputs[node_name] = overrides[node_name]
                record.inputs = {"__override__": True}
            elif node.is_input:
                outputs[node_name] = node.value
            else:
                # Gather within-step inputs
                kwargs = {}
                for upstream in node.upstream_edges:
                    kwargs[upstream] = outputs[upstream]
                    record.inputs[upstream] = outputs[upstream]

                # Gather temporal inputs
                for temporal_src in node.temporal_edges:
                    param_name = f"prev_{temporal_src}"
                    if prior_year_outputs and temporal_src in prior_year_outputs:
                        val = prior_year_outputs[temporal_src]
                        source_year = "prior"
                    else:
                        # Year 0: use initial_value or current value
                        src_node = self._nodes[temporal_src]
                        val = src_node.initial_value if src_node.initial_value is not None else src_node.value
                        source_year = "initial"
                    kwargs[param_name] = val
                    record.temporal_inputs[temporal_src] = {
                        "value": val,
                        "source_year": source_year,
                    }

                outputs[node_name] = node.compute_fn(**kwargs)

            provenance.append(record)

        return outputs, provenance
