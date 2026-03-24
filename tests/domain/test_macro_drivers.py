"""Tests for macro-economic drivers."""

from carbonsight.core.graph import SimulationGraph
from carbonsight.data.models import EnergyPriceTrajectory, MacroDriverDefaults
from carbonsight.domain.macro_drivers import (
    apply_elasticity,
    compute_powertrain_preference_shift,
    compute_vmt_adjustment,
    create_macro_driver_nodes,
    get_causal_links,
    get_year_value,
    query_causal_links,
)


class TestElasticity:
    def test_no_change(self):
        result = apply_elasticity(100, 75, 75, -0.2)
        assert result == 100

    def test_price_increase_reduces_vmt(self):
        result = apply_elasticity(1.0, 75, 100, -0.2)
        assert result < 1.0

    def test_price_decrease_increases_vmt(self):
        result = apply_elasticity(1.0, 75, 50, -0.2)
        assert result > 1.0

    def test_zero_baseline_returns_original(self):
        result = apply_elasticity(100, 0, 50, -0.2)
        assert result == 100


class TestVmtAdjustment:
    def test_baseline_returns_one(self):
        assert compute_vmt_adjustment(75.0) == 1.0

    def test_high_oil_reduces_vmt(self):
        result = compute_vmt_adjustment(100.0)
        assert result < 1.0

    def test_low_oil_increases_vmt(self):
        result = compute_vmt_adjustment(50.0)
        assert result > 1.0


class TestPowertrainPreference:
    def test_baseline_returns_one(self):
        assert compute_powertrain_preference_shift(75.0) == 1.0

    def test_high_oil_favors_evs(self):
        result = compute_powertrain_preference_shift(100.0)
        assert result > 1.0

    def test_low_oil_disfavors_evs(self):
        result = compute_powertrain_preference_shift(50.0)
        assert result < 1.0


class TestTrajectory:
    def test_get_year_value(self):
        traj = EnergyPriceTrajectory(name="test", unit="$/barrel", values=[70, 75, 80, 85, 90])
        assert get_year_value(traj, 0) == 70
        assert get_year_value(traj, 2) == 80

    def test_clamp_to_last(self):
        traj = EnergyPriceTrajectory(name="test", unit="$/barrel", values=[70, 75, 80])
        assert get_year_value(traj, 10) == 80

    def test_negative_year_clamps_to_first(self):
        traj = EnergyPriceTrajectory(name="test", unit="$/barrel", values=[70, 75, 80])
        assert get_year_value(traj, -1) == 70


class TestCausalLinks:
    def test_get_all_links(self):
        links = get_causal_links()
        assert len(links) >= 3

    def test_query_by_driver(self):
        links = query_causal_links(driver="oil_price")
        assert len(links) >= 2
        assert all(link.driver_node == "oil_price" for link in links)

    def test_query_by_target(self):
        links = query_causal_links(target="vmt_adjustment")
        assert len(links) >= 1
        assert all(link.target_node == "vmt_adjustment" for link in links)

    def test_query_returns_empty_for_unknown(self):
        links = query_causal_links(driver="nonexistent")
        assert len(links) == 0


class TestMacroDriverNodes:
    def test_creates_expected_nodes(self):
        nodes = create_macro_driver_nodes()
        names = {n.name for n in nodes}
        assert "oil_price_trajectory" in names
        assert "electricity_price_trajectory" in names
        assert "oil_price" in names
        assert "vmt_adjustment" in names
        assert "powertrain_preference_shift" in names

    def test_dag_validates(self):
        nodes = create_macro_driver_nodes()
        graph = SimulationGraph()
        for n in nodes:
            graph.add_node(n)
        graph.validate()

    def test_dag_executes(self):
        nodes = create_macro_driver_nodes()
        graph = SimulationGraph()
        for n in nodes:
            graph.add_node(n)
        graph.validate()
        outputs, _ = graph.execute()
        assert outputs["oil_price"] == 75.0
        assert outputs["vmt_adjustment"] == 1.0  # No change from baseline

    def test_custom_defaults(self):
        defaults = MacroDriverDefaults(
            oil_price_per_barrel=EnergyPriceTrajectory(
                name="High Oil", unit="$/barrel", values=[100.0] * 10
            )
        )
        nodes = create_macro_driver_nodes(defaults)
        graph = SimulationGraph()
        for n in nodes:
            graph.add_node(n)
        outputs, _ = graph.execute()
        assert outputs["oil_price"] == 100.0
        # High oil should reduce VMT
        assert outputs["vmt_adjustment"] < 1.0

    def test_eia_scenario_loading(self):
        # Reference scenario (default)
        defaults = MacroDriverDefaults()
        assert len(defaults.oil_price_per_barrel.values) == 10
        assert len(defaults.electricity_price_per_kwh.values) == 10
        assert defaults.oil_price_per_barrel.scenario == "reference"
