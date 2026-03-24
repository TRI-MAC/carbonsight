"""Tests for DAG construction, validation, cycle detection, and execution."""

import pytest

from carbonsight.core.graph import (
    CycleError,
    MissingInitialValueError,
    MissingNodeError,
    SimulationGraph,
)
from carbonsight.core.node import Node, NodeType


def _make_input(name, value=1.0, node_type=NodeType.SCALAR):
    return Node(name=name, node_type=node_type, value=value)


def _make_computed(name, compute_fn, node_type=NodeType.SCALAR, **kwargs):
    return Node(name=name, node_type=node_type, compute_fn=compute_fn, **kwargs)


class TestDAGConstruction:
    def test_construct_valid_dag(self):
        g = SimulationGraph()
        g.add_node(_make_input("a", 2.0))
        g.add_node(_make_input("b", 3.0))
        g.add_node(_make_computed("c", lambda a, b: a + b))
        g.validate()
        assert set(g.nodes.keys()) == {"a", "b", "c"}

    def test_reject_within_step_cycle(self):
        """A depends on B and B depends on A via within-step edges -> cycle error."""
        g = SimulationGraph()
        g.add_node(_make_computed("a", lambda b: b + 1))
        g.add_node(_make_computed("b", lambda a: a + 1))
        with pytest.raises(CycleError, match="Cycle detected"):
            g.validate()

    def test_accept_temporal_edge_that_would_form_cycle(self):
        """A depends on B (within-step), B depends on prev_A (temporal) -> no cycle."""
        g = SimulationGraph()
        g.add_node(
            Node(
                name="a",
                node_type=NodeType.SCALAR,
                compute_fn=lambda b: b * 2,
            )
        )
        g.add_node(
            Node(
                name="b",
                node_type=NodeType.SCALAR,
                compute_fn=lambda prev_a: prev_a + 1,
                initial_value=0.0,  # so A has an initial for temporal resolution
            )
        )
        # A's initial_value needed for B's temporal edge
        g.get_node("a").initial_value = 1.0
        g.validate()  # Should not raise

    def test_missing_upstream_node_raises(self):
        g = SimulationGraph()
        g.add_node(_make_computed("c", lambda nonexistent: nonexistent))
        with pytest.raises(MissingNodeError, match="nonexistent"):
            g.validate()

    def test_missing_temporal_node_raises(self):
        g = SimulationGraph()
        g.add_node(_make_computed("c", lambda prev_nonexistent: 0))
        with pytest.raises(MissingNodeError, match="nonexistent"):
            g.validate()

    def test_missing_initial_value_for_temporal_edge_raises(self):
        g = SimulationGraph()
        # 'source' is a computed node with no initial_value
        g.add_node(_make_input("x", 1.0))
        g.add_node(_make_computed("source", lambda x: x * 2))
        g.add_node(_make_computed("consumer", lambda prev_source: prev_source + 1))
        with pytest.raises(MissingInitialValueError, match="source"):
            g.validate()


class TestTopologicalExecution:
    def test_execute_linear_chain(self):
        g = SimulationGraph()
        g.add_node(_make_input("a", 10.0))
        g.add_node(_make_computed("b", lambda a: a * 2))
        g.add_node(_make_computed("c", lambda b: b + 5))

        outputs, provenance = g.execute()
        assert outputs["a"] == 10.0
        assert outputs["b"] == 20.0
        assert outputs["c"] == 25.0
        assert len(provenance) == 3

    def test_execution_respects_dependency_order(self):
        g = SimulationGraph()
        g.add_node(_make_input("a", 1.0))
        g.add_node(_make_computed("b", lambda a: a + 1))
        g.add_node(_make_computed("c", lambda b: b + 1))

        _, provenance = g.execute()
        names = [p.node_name for p in provenance]
        assert names.index("a") < names.index("b") < names.index("c")

    def test_execute_diamond_dag(self):
        g = SimulationGraph()
        g.add_node(_make_input("x", 5.0))
        g.add_node(_make_computed("left", lambda x: x * 2))
        g.add_node(_make_computed("right", lambda x: x * 3))
        g.add_node(_make_computed("merge", lambda left, right: left + right))

        outputs, _ = g.execute()
        assert outputs["merge"] == 25.0  # 5*2 + 5*3

    def test_execute_with_overrides(self):
        g = SimulationGraph()
        g.add_node(_make_input("a", 10.0))
        g.add_node(_make_computed("b", lambda a: a * 2))

        outputs, _ = g.execute(overrides={"a": 99.0})
        assert outputs["a"] == 99.0
        assert outputs["b"] == 198.0

    def test_provenance_records_inputs(self):
        g = SimulationGraph()
        g.add_node(_make_input("a", 3.0))
        g.add_node(_make_computed("b", lambda a: a * 2))

        _, provenance = g.execute()
        b_record = [p for p in provenance if p.node_name == "b"][0]
        assert b_record.inputs["a"] == 3.0
        assert b_record.compute_fn_name == "<lambda>"


class TestTemporalExecution:
    def test_temporal_edge_uses_prior_year_outputs(self):
        g = SimulationGraph()
        g.add_node(Node(name="stock", node_type=NodeType.SCALAR, value=100.0, initial_value=100.0))
        g.add_node(
            _make_computed(
                "growth",
                lambda prev_stock: prev_stock * 1.05,
            )
        )

        # First execution with no prior year -> uses initial_value
        outputs1, _ = g.execute()
        assert outputs1["growth"] == 105.0

        # Second execution with prior year outputs
        outputs2, _ = g.execute(prior_year_outputs={"stock": 200.0})
        assert outputs2["growth"] == 210.0

    def test_temporal_provenance_records_source_year(self):
        g = SimulationGraph()
        g.add_node(Node(name="x", node_type=NodeType.SCALAR, value=5.0, initial_value=5.0))
        g.add_node(_make_computed("y", lambda prev_x: prev_x + 1))

        # Year 0 - uses initial
        _, prov = g.execute()
        y_record = [p for p in prov if p.node_name == "y"][0]
        assert y_record.temporal_inputs["x"]["source_year"] == "initial"

        # With prior year
        _, prov = g.execute(prior_year_outputs={"x": 10.0})
        y_record = [p for p in prov if p.node_name == "y"][0]
        assert y_record.temporal_inputs["x"]["source_year"] == "prior"
        assert y_record.temporal_inputs["x"]["value"] == 10.0

    def test_feedback_loop_via_temporal_edges(self):
        """A depends on B (within-step), B depends on prev_A (temporal).
        This should work and show year-over-year dynamics."""
        g = SimulationGraph()
        g.add_node(
            Node(
                name="a",
                node_type=NodeType.SCALAR,
                compute_fn=lambda b: b * 2,
            )
        )
        g.add_node(
            Node(
                name="b",
                node_type=NodeType.SCALAR,
                compute_fn=lambda prev_a: prev_a + 1,
            )
        )
        g.get_node("a").initial_value = 1.0

        # Year 0: b = prev_a(initial=1) + 1 = 2, a = b*2 = 4
        out0, _ = g.execute()
        assert out0["b"] == 2.0
        assert out0["a"] == 4.0

        # Year 1: b = prev_a(4) + 1 = 5, a = b*2 = 10
        out1, _ = g.execute(prior_year_outputs=out0)
        assert out1["b"] == 5.0
        assert out1["a"] == 10.0
