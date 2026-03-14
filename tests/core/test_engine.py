"""Tests for the simulation engine: time stepping, temporal edges, and feedback loops."""

import pytest

from carbonsight.core.engine import SimulationConfig, SimulationEngine
from carbonsight.core.graph import MissingInitialValueError, SimulationGraph
from carbonsight.core.node import Node, NodeType


def _make_input(name, value=1.0):
    return Node(name=name, node_type=NodeType.SCALAR, value=value)


class TestTimeSteppingBasics:
    def test_ten_year_horizon_default(self):
        g = SimulationGraph()
        g.add_node(_make_input("x", 42.0))

        engine = SimulationEngine(g)
        result = engine.run()

        assert len(result.year_results) == 10
        assert result.years == list(range(2024, 2034))

    def test_each_year_labeled_correctly(self):
        g = SimulationGraph()
        g.add_node(_make_input("x", 1.0))

        engine = SimulationEngine(g)
        result = engine.run()

        for i, yr in enumerate(result.year_results):
            assert yr.year == 2024 + i

    def test_configurable_horizon(self):
        g = SimulationGraph()
        g.add_node(_make_input("x", 1.0))

        config = SimulationConfig(start_year=2020, num_years=5, renewal_rate=0.03)
        engine = SimulationEngine(g, config)
        result = engine.run()

        assert result.years == [2020, 2021, 2022, 2023, 2024]
        assert result.config.renewal_rate == 0.03

    def test_outputs_for_year(self):
        g = SimulationGraph()
        g.add_node(_make_input("x", 7.0))

        result = SimulationEngine(g).run()
        assert result.outputs_for_year(2024)["x"] == 7.0

        with pytest.raises(KeyError):
            result.outputs_for_year(9999)

    def test_output_timeseries(self):
        g = SimulationGraph()
        g.add_node(_make_input("x", 7.0))

        result = SimulationEngine(g).run()
        ts = result.output_timeseries("x")
        assert len(ts) == 10
        assert all(v == 7.0 for v in ts.values())

    def test_wall_clock_recorded(self):
        g = SimulationGraph()
        g.add_node(_make_input("x", 1.0))

        result = SimulationEngine(g).run()
        assert result.wall_clock_seconds > 0
        assert result.performance_warning is None  # trivial graph, should be fast


class TestOutputChaining:
    def test_year_n_outputs_available_as_year_n_plus_1_temporal_inputs(self):
        """A node with a temporal edge should see prior year's outputs."""
        g = SimulationGraph()
        # counter starts at 0, increments by 1 each year via temporal edge
        g.add_node(Node(
            name="counter",
            node_type=NodeType.SCALAR,
            compute_fn=lambda prev_counter: prev_counter + 1,
            initial_value=0,
        ))

        config = SimulationConfig(num_years=5)
        result = SimulationEngine(g, config).run()

        ts = result.output_timeseries("counter")
        # Year 0: prev=0 -> 1, Year 1: prev=1 -> 2, ...
        assert ts[2024] == 1
        assert ts[2025] == 2
        assert ts[2026] == 3
        assert ts[2027] == 4
        assert ts[2028] == 5

    def test_overrides_applied_every_year(self):
        g = SimulationGraph()
        g.add_node(_make_input("rate", 0.05))
        g.add_node(Node(
            name="result",
            node_type=NodeType.SCALAR,
            compute_fn=lambda rate: rate * 100,
        ))

        result = SimulationEngine(g).run(overrides={"rate": 0.10})
        for yr in result.year_results:
            assert yr.outputs["result"] == 10.0


class TestTemporalEdgeResolution:
    def test_year_0_uses_initial_value(self):
        g = SimulationGraph()
        g.add_node(Node(
            name="stock",
            node_type=NodeType.SCALAR,
            value=100.0,
            initial_value=100.0,
        ))
        g.add_node(Node(
            name="growth",
            node_type=NodeType.SCALAR,
            compute_fn=lambda prev_stock: prev_stock * 1.1,
        ))

        result = SimulationEngine(g, SimulationConfig(num_years=3)).run()
        # Year 0: prev_stock = initial(100) -> 110
        assert result.outputs_for_year(2024)["growth"] == pytest.approx(110.0)
        # Year 1: prev_stock = 100 (stock is input, doesn't change) -> 110
        assert result.outputs_for_year(2025)["growth"] == pytest.approx(110.0)

    def test_missing_initial_value_rejected(self):
        g = SimulationGraph()
        g.add_node(Node(
            name="computed",
            node_type=NodeType.SCALAR,
            compute_fn=lambda prev_computed: prev_computed + 1,
            # No initial_value provided for self-referencing temporal edge
        ))
        with pytest.raises(MissingInitialValueError):
            SimulationEngine(g).run()

    def test_provenance_distinguishes_temporal_edges(self):
        g = SimulationGraph()
        g.add_node(Node(
            name="x",
            node_type=NodeType.SCALAR,
            value=5.0,
            initial_value=5.0,
        ))
        g.add_node(Node(
            name="y",
            node_type=NodeType.SCALAR,
            compute_fn=lambda prev_x: prev_x + 1,
        ))

        result = SimulationEngine(g, SimulationConfig(num_years=2)).run()

        # Year 0 provenance
        prov0 = result.year_results[0].provenance
        y_prov0 = [p for p in prov0 if p.node_name == "y"][0]
        assert "x" in y_prov0.temporal_inputs
        assert y_prov0.temporal_inputs["x"]["source_year"] == "initial"

        # Year 1 provenance
        prov1 = result.year_results[1].provenance
        y_prov1 = [p for p in prov1 if p.node_name == "y"][0]
        assert y_prov1.temporal_inputs["x"]["source_year"] == "prior"


class TestFeedbackLoop:
    def test_fleet_composition_powertrain_preference_feedback(self):
        """Simulate a simplified feedback loop:
        - fleet_comp depends on pref (within-step)
        - pref depends on prev_fleet_comp (temporal)

        This models: last year's fleet comp influences this year's
        preference which influences this year's fleet comp.
        """
        g = SimulationGraph()
        g.add_node(Node(
            name="pref",
            node_type=NodeType.SCALAR,
            compute_fn=lambda prev_fleet_comp: prev_fleet_comp * 0.8 + 0.2,
        ))
        g.add_node(Node(
            name="fleet_comp",
            node_type=NodeType.SCALAR,
            compute_fn=lambda pref: pref * 1.5,
            initial_value=0.5,  # for pref's temporal edge
        ))
        g.get_node("fleet_comp").initial_value = 0.5

        result = SimulationEngine(g, SimulationConfig(num_years=5)).run()

        # Year 0: pref = 0.5*0.8+0.2 = 0.6, fleet = 0.6*1.5 = 0.9
        assert result.outputs_for_year(2024)["pref"] == pytest.approx(0.6)
        assert result.outputs_for_year(2024)["fleet_comp"] == pytest.approx(0.9)

        # Year 1: pref = 0.9*0.8+0.2 = 0.92, fleet = 0.92*1.5 = 1.38
        assert result.outputs_for_year(2025)["pref"] == pytest.approx(0.92)
        assert result.outputs_for_year(2025)["fleet_comp"] == pytest.approx(1.38)

        # Values should evolve year over year (not be static)
        ts = result.output_timeseries("fleet_comp")
        values = list(ts.values())
        assert values[0] != values[1] != values[2]


class TestYearSpecificOverrides:
    def test_year_specific_override_applied(self):
        g = SimulationGraph()
        g.add_node(_make_input("rate", 0.05))
        g.add_node(Node(
            name="result",
            node_type=NodeType.SCALAR,
            compute_fn=lambda rate: rate * 100,
        ))

        config = SimulationConfig(start_year=2024, num_years=3)
        result = SimulationEngine(g, config).run(
            year_overrides={2025: {"rate": 0.10}},
        )
        assert result.outputs_for_year(2024)["result"] == pytest.approx(5.0)
        assert result.outputs_for_year(2025)["result"] == pytest.approx(10.0)
        assert result.outputs_for_year(2026)["result"] == pytest.approx(5.0)

    def test_year_specific_takes_precedence_over_base(self):
        g = SimulationGraph()
        g.add_node(_make_input("rate", 0.05))
        g.add_node(Node(
            name="result",
            node_type=NodeType.SCALAR,
            compute_fn=lambda rate: rate * 100,
        ))

        config = SimulationConfig(start_year=2024, num_years=3)
        result = SimulationEngine(g, config).run(
            overrides={"rate": 0.10},
            year_overrides={2025: {"rate": 0.20}},
        )
        # Base override: rate=0.10 every year, but 2025 overrides to 0.20
        assert result.outputs_for_year(2024)["result"] == pytest.approx(10.0)
        assert result.outputs_for_year(2025)["result"] == pytest.approx(20.0)
        assert result.outputs_for_year(2026)["result"] == pytest.approx(10.0)

    def test_year_overrides_in_uq_mode(self):
        from carbonsight.core.engine import ExecutionMode

        g = SimulationGraph()
        g.add_node(_make_input("rate", 0.05))
        g.add_node(Node(
            name="result",
            node_type=NodeType.SCALAR,
            compute_fn=lambda rate: rate * 100,
        ))

        config = SimulationConfig(start_year=2024, num_years=2, uq_samples=5)
        result = SimulationEngine(g, config).run(
            mode=ExecutionMode.UQ,
            year_overrides={2025: {"rate": 0.50}},
        )
        # UQ aggregates, but with no distributions, all samples are identical
        y2024 = result.outputs_for_year(2024)["result"]
        y2025 = result.outputs_for_year(2025)["result"]
        assert y2024["mean"] == pytest.approx(5.0)
        assert y2025["mean"] == pytest.approx(50.0)
