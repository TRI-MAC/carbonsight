"""Tests for scenario CRUD, serialization, comparison, and distribution comparison."""

import numpy as np
import pytest

from carbonsight.core.engine import SimulationConfig, SimulationEngine
from carbonsight.core.graph import SimulationGraph
from carbonsight.core.node import Node, NodeType
from carbonsight.core.scenario import (
    Scenario,
    ScenarioStore,
    compare_distribution_results,
    compare_scenarios,
    summarize_samples,
)


class TestScenarioCRUD:
    def test_create_and_retrieve(self):
        store = ScenarioStore()
        s = Scenario(name="ev_subsidy", overrides={"subsidy_amount": 7500})
        store.create(s)
        retrieved = store.get("ev_subsidy")
        assert retrieved.overrides["subsidy_amount"] == 7500

    def test_reject_duplicate_name(self):
        store = ScenarioStore()
        store.create(Scenario(name="test"))
        with pytest.raises(ValueError, match="already exists"):
            store.create(Scenario(name="test"))

    def test_update_scenario(self):
        store = ScenarioStore()
        store.create(Scenario(name="ev_subsidy", overrides={"subsidy_amount": 7500}))
        store.update("ev_subsidy", overrides={"subsidy_amount": 10000})
        assert store.get("ev_subsidy").overrides["subsidy_amount"] == 10000

    def test_delete_scenario(self):
        store = ScenarioStore()
        store.create(Scenario(name="temp"))
        store.delete("temp")
        with pytest.raises(KeyError):
            store.get("temp")

    def test_delete_nonexistent_raises(self):
        store = ScenarioStore()
        with pytest.raises(KeyError):
            store.delete("nope")

    def test_list_scenarios(self):
        store = ScenarioStore()
        store.create(Scenario(name="a"))
        store.create(Scenario(name="b"))
        assert set(store.list()) == {"a", "b"}


class TestScenarioSerialization:
    def test_to_dict_and_back(self):
        s = Scenario(name="test", overrides={"rate": 0.05}, metadata={"author": "taber"})
        d = s.to_dict()
        s2 = Scenario.from_dict(d)
        assert s2.name == "test"
        assert s2.overrides["rate"] == 0.05
        assert s2.metadata["author"] == "taber"

    def test_yaml_round_trip(self):
        s = Scenario(name="carbon_tax", overrides={"carbon_price": 50, "start_year": 2026})
        yaml_str = s.to_yaml()
        s2 = Scenario.from_yaml(yaml_str)
        assert s2.name == "carbon_tax"
        assert s2.overrides["carbon_price"] == 50

    def test_numpy_values_serialize(self):
        s = Scenario(
            name="np_test",
            overrides={
                "int_val": np.int64(42),
                "float_val": np.float64(3.14),
                "array_val": np.array([1.0, 2.0, 3.0]),
            },
        )
        d = s.to_dict()
        assert isinstance(d["overrides"]["int_val"], int)
        assert isinstance(d["overrides"]["float_val"], float)
        assert isinstance(d["overrides"]["array_val"], list)


class TestScenarioComparison:
    def _run_scenario(self, rate_override=None):
        g = SimulationGraph()
        g.add_node(Node(name="rate", node_type=NodeType.SCALAR, value=0.05))
        g.add_node(
            Node(
                name="emissions",
                node_type=NodeType.SCALAR,
                compute_fn=lambda rate: rate * 1000,
            )
        )
        config = SimulationConfig(num_years=3)
        overrides = {"rate": rate_override} if rate_override is not None else None
        return SimulationEngine(g, config).run(overrides=overrides)

    def test_compare_baseline_and_intervention(self):
        baseline = self._run_scenario()
        intervention = self._run_scenario(rate_override=0.03)

        comp = compare_scenarios(baseline, intervention, "base", "low_rate")
        assert comp.baseline_name == "base"
        assert comp.intervention_name == "low_rate"

        emissions_deltas = comp.deltas_for_node("emissions")
        assert len(emissions_deltas) == 3  # 3 years
        for d in emissions_deltas:
            assert d.absolute_delta == pytest.approx(-20.0)  # 30 - 50
            assert d.percentage_delta == pytest.approx(-40.0)

    def test_compare_specific_nodes(self):
        baseline = self._run_scenario()
        intervention = self._run_scenario(rate_override=0.03)

        comp = compare_scenarios(baseline, intervention, nodes=["emissions"])
        # Should only have emissions deltas, not rate
        node_names = {d.node_name for d in comp.deltas}
        assert node_names == {"emissions"}

    def test_deltas_for_year(self):
        baseline = self._run_scenario()
        intervention = self._run_scenario(rate_override=0.03)

        comp = compare_scenarios(baseline, intervention)
        year_deltas = comp.deltas_for_year(2024)
        assert len(year_deltas) > 0
        assert all(d.year == 2024 for d in year_deltas)

    def test_zero_baseline_gives_none_percentage(self):
        g = SimulationGraph()
        g.add_node(Node(name="x", node_type=NodeType.SCALAR, value=0.0))
        config = SimulationConfig(num_years=1)
        baseline = SimulationEngine(g, config).run()

        g2 = SimulationGraph()
        g2.add_node(Node(name="x", node_type=NodeType.SCALAR, value=5.0))
        intervention = SimulationEngine(g2, config).run()

        comp = compare_scenarios(baseline, intervention)
        x_deltas = comp.deltas_for_node("x")
        assert x_deltas[0].percentage_delta is None


class TestDistributionComparison:
    def test_summarize_samples(self):
        rng = np.random.default_rng(42)
        samples = rng.normal(100, 10, size=10000)
        summary = summarize_samples(samples)
        assert abs(summary.mean - 100) < 1
        assert abs(summary.median - 100) < 1
        assert summary.p5 < summary.p25 < summary.median < summary.p75 < summary.p95
        assert summary.std > 0

    def test_compare_distribution_results(self):
        rng = np.random.default_rng(42)
        baseline = {"ghg": {2024: rng.normal(500, 50, 1000)}}
        intervention = {"ghg": {2024: rng.normal(450, 40, 1000)}}

        result = compare_distribution_results(baseline, intervention)
        assert "ghg" in result
        assert 2024 in result["ghg"]
        assert result["ghg"][2024]["mean_delta"] < 0  # intervention lower


class TestInterventionResolution:
    def test_resolve_single_intervention(self):
        from carbonsight.core.scenario import InterventionSpec, resolve_interventions

        specs = [InterventionSpec(type="carbon_pricing", params={"price_per_tonne": 50})]
        interventions = resolve_interventions(specs)
        assert len(interventions) == 1
        assert interventions[0].name == "carbon_pricing_50"

    def test_resolve_multiple_interventions(self):
        from carbonsight.core.scenario import InterventionSpec, resolve_interventions

        specs = [
            InterventionSpec(type="carbon_pricing", params={"price_per_tonne": 100}),
            InterventionSpec(type="vmt_reduction", params={"factor": 0.9}),
        ]
        interventions = resolve_interventions(specs)
        assert len(interventions) == 2

    def test_resolve_unknown_type_raises(self):
        from carbonsight.core.scenario import InterventionSpec, resolve_interventions

        specs = [InterventionSpec(type="nonexistent", params={})]
        with pytest.raises(ValueError, match="Unknown intervention type"):
            resolve_interventions(specs)

    def test_resolve_year_overrides(self):
        from carbonsight.core.scenario import (
            InterventionSpec,
            resolve_interventions,
            resolve_year_overrides,
        )

        specs = [
            InterventionSpec(
                type="carbon_pricing", params={"price_per_tonne": 50, "start_year": 2024}
            )
        ]
        interventions = resolve_interventions(specs)
        year_overrides = resolve_year_overrides(interventions, list(range(2024, 2034)))
        # carbon_pricing sets year_overrides for years 2024-2033
        assert len(year_overrides) > 0
        assert 2024 in year_overrides

    def test_scenario_with_interventions_serialization(self):
        from carbonsight.core.scenario import InterventionSpec

        s = Scenario(
            name="test",
            interventions=[
                InterventionSpec(type="ev_subsidy", params={"proportion_shift": {"bev": 0.15}})
            ],
        )
        d = s.to_dict()
        assert len(d["interventions"]) == 1
        assert d["interventions"][0]["type"] == "ev_subsidy"

        restored = Scenario.from_dict(d)
        assert len(restored.interventions) == 1
        assert restored.interventions[0].type == "ev_subsidy"
