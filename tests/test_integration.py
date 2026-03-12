"""End-to-end integration tests for CarbonSight.

Tests full 10-year simulation with fleet dynamics, emissions, interventions,
UQ, comparison, attribution, and provenance.
"""

import numpy as np
import pytest

from carbonsight.core.engine import ExecutionMode, SimulationConfig, SimulationEngine
from carbonsight.core.graph import SimulationGraph
from carbonsight.core.scenario import Scenario, ScenarioStore
from carbonsight.data.loaders import (
    load_fleet_inventory,
    load_survival_curves,
    load_vmt_by_age,
)
from carbonsight.domain.emissions import (
    aggregate_emissions,
    compute_disposal_emissions,
    compute_production_emissions,
    compute_usage_emissions,
)
from carbonsight.domain.fleet_dynamics import step_fleet_one_year
from carbonsight.domain.fleet_nodes import create_fleet_dynamics_nodes
from carbonsight.domain.emissions_nodes import create_emissions_nodes
from carbonsight.analysis.explainability import (
    generate_provenance_report,
    trace_provenance_backward,
)


class TestFullSimulation:
    """End-to-end: 10-year deterministic simulation with real data."""

    def test_ten_year_fleet_dynamics(self):
        fleet = load_fleet_inventory()
        survival = load_survival_curves()
        vmt = load_vmt_by_age()
        proportions = {"icev": 0.82, "hev": 0.09, "phev": 0.02, "bev": 0.07}

        compositions = []
        for year in range(10):
            fleet, scrapped, comp = step_fleet_one_year(
                fleet, survival, vmt, proportions
            )
            compositions.append(comp)

        # Fleet size should remain roughly stable (scrappage ≈ new entry)
        initial_total = compositions[0]["total_vehicles"]
        final_total = compositions[-1]["total_vehicles"]
        assert abs(final_total - initial_total) / initial_total < 0.15

        # BEV share should increase over time with 7% BEV entry rate
        initial_bev_share = compositions[0]["by_powertrain"].get("bev", 0) / compositions[0]["total_vehicles"]
        final_bev_share = compositions[-1]["by_powertrain"].get("bev", 0) / compositions[-1]["total_vehicles"]
        assert final_bev_share > initial_bev_share

    def test_ten_year_emissions_trajectory(self):
        fleet = load_fleet_inventory()
        survival = load_survival_curves()
        vmt = load_vmt_by_age()
        proportions = {"icev": 0.82, "hev": 0.09, "phev": 0.02, "bev": 0.07}

        annual_emissions = []
        for year in range(10):
            fleet, scrapped, comp = step_fleet_one_year(
                fleet, survival, vmt, proportions
            )
            fleet_e = compute_production_emissions(fleet)
            fleet_e = compute_usage_emissions(fleet_e)
            scrapped_e = compute_disposal_emissions(scrapped)
            agg = aggregate_emissions(fleet_e, scrapped_e)
            annual_emissions.append(agg)

        # Total emissions should be positive each year
        for agg in annual_emissions:
            assert agg["total_ghg"] > 0
            assert agg["production_ghg"] >= 0
            assert agg["usage_ghg_total"] > 0

        # Cumulative emissions
        cumulative = sum(a["total_ghg"] for a in annual_emissions)
        assert cumulative > 0

    def test_dag_based_execution(self):
        """Test the full DAG executes with fleet + emissions nodes."""
        fleet = load_fleet_inventory()
        survival = load_survival_curves()
        vmt = load_vmt_by_age()

        graph = SimulationGraph()
        for n in create_fleet_dynamics_nodes(fleet, survival, vmt):
            graph.add_node(n)
        for n in create_emissions_nodes():
            graph.add_node(n)

        graph.validate()
        outputs, provenance = graph.execute()

        # Check key outputs exist
        assert "fleet_snapshot" in outputs
        assert "total_emissions" in outputs
        assert outputs["total_emissions"]["total_ghg"] > 0

        # Check provenance was recorded
        assert len(provenance) > 0
        node_names = [p.node_name for p in provenance]
        assert "total_emissions" in node_names

    def test_provenance_traceability(self):
        """Test provenance chain from total_emissions back to inputs."""
        fleet = load_fleet_inventory()
        survival = load_survival_curves()
        vmt = load_vmt_by_age()

        graph = SimulationGraph()
        for n in create_fleet_dynamics_nodes(fleet, survival, vmt):
            graph.add_node(n)
        for n in create_emissions_nodes():
            graph.add_node(n)

        graph.validate()
        outputs, provenance = graph.execute()

        chain = trace_provenance_backward(graph, "total_emissions", provenance)
        assert len(chain.chain) > 0
        assert len(chain.data_sources) > 0

        # Generate report
        report = generate_provenance_report(graph, provenance, "total_emissions", year=2024)
        assert "Provenance Report" in report
        assert "Greene & Leard" in report or "NHTS" in report


class TestScenarioComparison:
    """Test baseline vs intervention scenario comparison."""

    def test_high_bev_scenario_reduces_gas_emissions(self):
        survival = load_survival_curves()
        vmt = load_vmt_by_age()

        baseline_proportions = {"icev": 0.82, "hev": 0.09, "phev": 0.02, "bev": 0.07}
        high_bev_proportions = {"icev": 0.50, "hev": 0.10, "phev": 0.05, "bev": 0.35}

        baseline_gas = 0
        intervention_gas = 0

        fleet_b = load_fleet_inventory()
        fleet_i = load_fleet_inventory()

        for year in range(10):
            fleet_b, scrapped_b, _ = step_fleet_one_year(
                fleet_b, survival, vmt, baseline_proportions
            )
            fleet_b_e = compute_usage_emissions(fleet_b)
            baseline_gas += fleet_b_e["ghg_gas"].sum()

            fleet_i, scrapped_i, _ = step_fleet_one_year(
                fleet_i, survival, vmt, high_bev_proportions
            )
            fleet_i_e = compute_usage_emissions(fleet_i)
            intervention_gas += fleet_i_e["ghg_gas"].sum()

        # High BEV scenario should have lower cumulative gas emissions
        assert intervention_gas < baseline_gas


class TestEmissionsValidation:
    """Validate emissions are within reasonable ranges."""

    def test_production_emissions_per_vehicle(self):
        # ICEV: body (4200) + ICE (1400) = 5600 kg CO2
        fleet = load_fleet_inventory()
        new_icev = fleet[(fleet["age"] == 0) & (fleet["powertrain"] == "icev")].head(1).copy()
        new_icev["n"] = 1.0
        result = compute_production_emissions(new_icev)
        per_vehicle = result["production_ghg"].values[0]
        assert 5000 < per_vehicle < 6500  # ~5600 expected

    def test_bev_production_higher_than_icev(self):
        fleet = load_fleet_inventory()
        new_bev = fleet[(fleet["age"] == 0) & (fleet["powertrain"] == "bev")].head(1).copy()
        new_bev["n"] = 1.0
        new_icev = fleet[(fleet["age"] == 0) & (fleet["powertrain"] == "icev")].head(1).copy()
        new_icev["n"] = 1.0

        bev_result = compute_production_emissions(new_bev)
        icev_result = compute_production_emissions(new_icev)

        bev_prod = bev_result["production_ghg"].values[0]
        icev_prod = icev_result["production_ghg"].values[0]
        # BEV should have higher production due to battery
        assert bev_prod > icev_prod

    def test_usage_ghg_per_mile_reasonable(self):
        # For a 30 mpg ICEV: 8.89/30 ≈ 0.296 kg CO2/mile
        fleet = load_fleet_inventory()
        icev = fleet[(fleet["powertrain"] == "icev") & (fleet["age"] == 0)].head(1).copy()
        icev["n"] = 1.0
        result = compute_usage_emissions(icev)
        ghg_per_mile = result["ghg_gas"].values[0] / result["vmt"].values[0]
        # Should be between 0.15 and 0.5 kg/mile
        assert 0.15 < ghg_per_mile < 0.5

    def test_disposal_in_expected_range(self):
        scrapped = load_fleet_inventory().head(1).copy()
        scrapped["n"] = 1.0
        result = compute_disposal_emissions(scrapped)
        per_vehicle = result["disposal_ghg"].values[0]
        # Default 2800, should be 2000-3500 range
        assert 2000 <= per_vehicle <= 3500
