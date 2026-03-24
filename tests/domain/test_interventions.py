"""Tests for counterfactual intervention system."""

import pytest

from carbonsight.domain.interventions import (
    Intervention,
    InterventionCategory,
    attribute_interventions,
    battery_cost_reduction,
    carbon_pricing,
    combine_interventions,
    combine_interventions_for_year,
    compute_intervention_delta,
    ev_subsidy,
    grid_decarbonization,
    phev_charging_improvement,
    scrappage_program,
    vmt_reduction,
)


class TestInterventionCreation:
    def test_create_with_enum_category(self):
        i = Intervention(name="test", category=InterventionCategory.POLICY, overrides={"x": 1})
        assert i.category == InterventionCategory.POLICY

    def test_create_with_string_category(self):
        i = Intervention(name="test", category="technology", overrides={"x": 1})
        assert i.category == InterventionCategory.TECHNOLOGY

    def test_invalid_category_rejected(self):
        with pytest.raises(ValueError, match="Invalid intervention category"):
            Intervention(name="test", category="economic")

    def test_all_valid_categories(self):
        for cat in ["policy", "technology", "behavioral", "grid_energy"]:
            i = Intervention(name="test", category=cat)
            assert i.category.value == cat

    def test_year_overrides_precedence(self):
        i = Intervention(
            name="test",
            category="policy",
            overrides={"gas_ghg_per_gallon": 8.89},
            year_overrides={3: {"gas_ghg_per_gallon": 9.5}},
        )
        assert i.get_overrides_for_year(0) == {"gas_ghg_per_gallon": 8.89}
        assert i.get_overrides_for_year(3) == {"gas_ghg_per_gallon": 9.5}


class TestInterventionFactories:
    def test_carbon_pricing(self):
        i = carbon_pricing(50, start_year=2)
        assert i.category == InterventionCategory.POLICY
        assert len(i.year_overrides) > 0

    def test_ev_subsidy(self):
        props = {"icev": 0.60, "hev": 0.10, "phev": 0.05, "bev": 0.25}
        i = ev_subsidy(props)
        assert i.category == InterventionCategory.POLICY
        assert i.overrides["powertrain_proportions"] == props

    def test_vmt_reduction(self):
        i = vmt_reduction(0.9)
        assert i.category == InterventionCategory.BEHAVIORAL
        assert i.overrides["vmt_reduction_factor"] == 0.9

    def test_grid_decarbonization(self):
        traj = {0: 0.369, 5: 0.300, 9: 0.200}
        i = grid_decarbonization(traj)
        assert i.category == InterventionCategory.GRID_ENERGY
        assert i.year_overrides[5] == {"grid_ghg_per_kwh": 0.300}

    def test_battery_cost_reduction(self):
        traj = {0: 100, 5: 80, 9: 65}
        i = battery_cost_reduction(traj)
        assert i.category == InterventionCategory.TECHNOLOGY

    def test_scrappage_program(self):
        i = scrappage_program(age_threshold=15, acceleration_factor=2.0)
        assert i.category == InterventionCategory.POLICY
        assert i.overrides["scrappage_age_threshold"] == 15

    def test_phev_charging(self):
        i = phev_charging_improvement(0.85)
        assert i.category == InterventionCategory.BEHAVIORAL
        assert i.overrides["charging_factor"] == 0.85


class TestCombineInterventions:
    def test_combine_non_conflicting(self):
        i1 = Intervention(name="a", category="policy", overrides={"gas_ghg_per_gallon": 9.0})
        i2 = Intervention(
            name="b", category="technology", overrides={"production_battery_per_kwh": 80}
        )
        combined, warns = combine_interventions([i1, i2])
        assert combined["gas_ghg_per_gallon"] == 9.0
        assert combined["production_battery_per_kwh"] == 80
        assert len(warns) == 0

    def test_conflict_detection(self):
        i1 = Intervention(name="a", category="policy", overrides={"grid_ghg_per_kwh": 0.3})
        i2 = Intervention(name="b", category="grid_energy", overrides={"grid_ghg_per_kwh": 0.2})
        combined, warns = combine_interventions([i1, i2])
        assert len(warns) == 1
        assert "Conflict" in warns[0]
        # Later category wins (grid_energy applied after policy)
        assert combined["grid_ghg_per_kwh"] == 0.2

    def test_application_order(self):
        # Verify category order is respected
        interventions = [
            Intervention(name="grid", category="grid_energy", overrides={"x": 4}),
            Intervention(name="policy", category="policy", overrides={"x": 1}),
            Intervention(name="tech", category="technology", overrides={"x": 2}),
            Intervention(name="beh", category="behavioral", overrides={"x": 3}),
        ]
        combined, warns = combine_interventions(interventions)
        # grid_energy is last, so it wins
        assert combined["x"] == 4

    def test_combine_for_year(self):
        i1 = Intervention(
            name="a",
            category="policy",
            overrides={"gas_ghg_per_gallon": 8.89},
            year_overrides={5: {"gas_ghg_per_gallon": 9.5}},
        )
        i2 = Intervention(
            name="b",
            category="technology",
            overrides={"production_battery_per_kwh": 100},
            year_overrides={5: {"production_battery_per_kwh": 80}},
        )
        combined, warns = combine_interventions_for_year([i1, i2], year=5)
        assert combined["gas_ghg_per_gallon"] == 9.5
        assert combined["production_battery_per_kwh"] == 80


class TestScenarioDifferencing:
    def test_compute_delta(self):
        baseline = {
            0: {"total_emissions": {"total_ghg": 1000}},
            1: {"total_emissions": {"total_ghg": 1100}},
        }
        intervention = {
            0: {"total_emissions": {"total_ghg": 900}},
            1: {"total_emissions": {"total_ghg": 950}},
        }
        deltas = compute_intervention_delta(baseline, intervention)
        assert deltas[0]["absolute"] == -100
        assert deltas[0]["percentage"] == pytest.approx(-10.0)
        assert deltas[1]["absolute"] == -150

    def test_attribute_interventions(self):
        baseline = {0: {"total_emissions": {"total_ghg": 1000}}}
        individual = {
            "policy_a": {0: {"total_emissions": {"total_ghg": 900}}},
            "tech_b": {0: {"total_emissions": {"total_ghg": 950}}},
        }
        combined = {0: {"total_emissions": {"total_ghg": 820}}}

        attr = attribute_interventions(baseline, individual, combined)
        assert attr["policy_a"][0] == -100  # independent effect
        assert attr["tech_b"][0] == -50
        # Interaction: combined effect (-180) - sum of individual (-150) = -30
        assert attr["interaction"][0] == -30

    def test_no_interaction_when_independent(self):
        baseline = {0: {"total_emissions": {"total_ghg": 1000}}}
        individual = {
            "a": {0: {"total_emissions": {"total_ghg": 900}}},
            "b": {0: {"total_emissions": {"total_ghg": 950}}},
        }
        # Combined effect = sum of individual effects (no interaction)
        combined = {0: {"total_emissions": {"total_ghg": 850}}}

        attr = attribute_interventions(baseline, individual, combined)
        assert attr["interaction"][0] == 0
