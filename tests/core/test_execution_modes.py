"""Tests for deterministic vs UQ execution modes."""

import numpy as np
import pytest

from carbonsight.core.distributions import Distribution
from carbonsight.core.engine import ExecutionMode, SimulationConfig, SimulationEngine
from carbonsight.core.graph import SimulationGraph
from carbonsight.core.node import Node, NodeType


def _build_simple_graph_with_distribution():
    """Graph with a distribution input and a computed output."""
    g = SimulationGraph()
    g.add_node(Node(
        name="grid_intensity",
        node_type=NodeType.DISTRIBUTION,
        value=Distribution.normal(mean=369, std=20),
    ))
    g.add_node(Node(
        name="emissions",
        node_type=NodeType.SCALAR,
        compute_fn=lambda grid_intensity: grid_intensity * 10,
    ))
    return g


class TestDeterministicMode:
    def test_deterministic_collapses_distributions(self):
        g = _build_simple_graph_with_distribution()
        config = SimulationConfig(num_years=3, execution_mode=ExecutionMode.DETERMINISTIC)
        result = SimulationEngine(g, config).run()

        assert result.execution_mode == ExecutionMode.DETERMINISTIC
        # Should use mean (369) as point estimate
        for yr in result.year_results:
            assert yr.outputs["emissions"] == pytest.approx(3690.0)

    def test_deterministic_returns_single_values(self):
        g = _build_simple_graph_with_distribution()
        config = SimulationConfig(num_years=1)
        result = SimulationEngine(g, config).run(mode=ExecutionMode.DETERMINISTIC)

        # Output should be a plain numeric value, not a dict of stats
        assert isinstance(result.year_results[0].outputs["emissions"], (int, float))


class TestUQMode:
    def test_uq_produces_distribution_outputs(self):
        g = _build_simple_graph_with_distribution()
        config = SimulationConfig(
            num_years=2,
            execution_mode=ExecutionMode.UQ,
            uq_samples=100,
        )
        result = SimulationEngine(g, config).run()

        assert result.execution_mode == ExecutionMode.UQ
        emissions = result.year_results[0].outputs["emissions"]
        assert isinstance(emissions, dict)
        assert "mean" in emissions
        assert "median" in emissions
        assert "p5" in emissions
        assert "p95" in emissions
        assert "std" in emissions
        assert "samples" in emissions

    def test_uq_mean_close_to_deterministic(self):
        g = _build_simple_graph_with_distribution()
        config_det = SimulationConfig(num_years=1)
        config_uq = SimulationConfig(num_years=1, uq_samples=500)

        det_result = SimulationEngine(g, config_det).run(mode=ExecutionMode.DETERMINISTIC)
        uq_result = SimulationEngine(g, config_uq).run(mode=ExecutionMode.UQ)

        det_val = det_result.year_results[0].outputs["emissions"]
        uq_mean = uq_result.year_results[0].outputs["emissions"]["mean"]

        # UQ mean should be within 5% of deterministic (spec requirement)
        assert abs(uq_mean - det_val) / det_val < 0.05

    def test_uq_confidence_intervals_ordered(self):
        g = _build_simple_graph_with_distribution()
        config = SimulationConfig(num_years=1, uq_samples=200)
        result = SimulationEngine(g, config).run(mode=ExecutionMode.UQ)

        e = result.year_results[0].outputs["emissions"]
        assert e["p5"] < e["p25"] < e["median"] < e["p75"] < e["p95"]

    def test_uq_produces_nonzero_std(self):
        g = _build_simple_graph_with_distribution()
        config = SimulationConfig(num_years=1, uq_samples=100)
        result = SimulationEngine(g, config).run(mode=ExecutionMode.UQ)

        assert result.year_results[0].outputs["emissions"]["std"] > 0


class TestModeImmutability:
    def test_mode_specified_at_launch(self):
        g = SimulationGraph()
        g.add_node(Node(name="x", node_type=NodeType.SCALAR, value=1.0))

        config = SimulationConfig(execution_mode=ExecutionMode.DETERMINISTIC)
        result = SimulationEngine(g, config).run()
        assert result.execution_mode == ExecutionMode.DETERMINISTIC

    def test_mode_override_at_run_call(self):
        g = SimulationGraph()
        g.add_node(Node(name="x", node_type=NodeType.SCALAR, value=1.0))

        config = SimulationConfig(execution_mode=ExecutionMode.DETERMINISTIC)
        engine = SimulationEngine(g, config)
        # Override to UQ at run time
        result = engine.run(mode=ExecutionMode.UQ)
        assert result.execution_mode == ExecutionMode.UQ


class TestPerformance:
    def test_wall_clock_recorded(self):
        g = SimulationGraph()
        g.add_node(Node(name="x", node_type=NodeType.SCALAR, value=1.0))
        result = SimulationEngine(g).run()
        assert result.wall_clock_seconds > 0
        assert result.performance_warning is None
