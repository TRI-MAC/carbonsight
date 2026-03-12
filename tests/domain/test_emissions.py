"""Tests for emissions model."""

import numpy as np
import pandas as pd
import pytest

from carbonsight.domain.emissions import (
    aggregate_emissions,
    compute_disposal_emissions,
    compute_production_emissions,
    compute_usage_emissions,
    compute_utility_factor,
    get_ev_range_from_batt_kwh,
)


@pytest.fixture
def icev_fleet():
    """Fleet of ICE vehicles only."""
    return pd.DataFrame({
        "age": [0, 5],
        "powertrain": ["icev", "icev"],
        "vmt_bucket": ["high", "low"],
        "mpg": [30.0, 25.0],
        "mpge": [np.nan, np.nan],
        "batt_kwh": [0.0, 0.0],
        "n": [1000.0, 2000.0],
        "vmt": [15000.0, 8000.0],
        "high_VMT_prop": [0.76, 0.76],
    })


@pytest.fixture
def bev_fleet():
    """Fleet of BEV vehicles only."""
    return pd.DataFrame({
        "age": [0, 3],
        "powertrain": ["bev", "bev"],
        "vmt_bucket": ["high", "low"],
        "mpg": [np.nan, np.nan],
        "mpge": [110.0, 105.0],
        "batt_kwh": [75.0, 60.0],
        "n": [500.0, 300.0],
        "vmt": [15000.0, 8000.0],
        "high_VMT_prop": [0.76, 0.76],
    })


@pytest.fixture
def phev_fleet():
    """Fleet of PHEV vehicles."""
    return pd.DataFrame({
        "age": [0],
        "powertrain": ["phev"],
        "vmt_bucket": ["high"],
        "mpg": [25.0],
        "mpge": [62.0],
        "batt_kwh": [15.0],
        "n": [100.0],
        "vmt": [12000.0],
        "high_VMT_prop": [0.76],
    })


@pytest.fixture
def mixed_fleet():
    """Fleet with all powertrain types."""
    return pd.DataFrame({
        "age": [0, 0, 0, 0],
        "powertrain": ["icev", "hev", "phev", "bev"],
        "vmt_bucket": ["high"] * 4,
        "mpg": [30.0, 40.0, 25.0, np.nan],
        "mpge": [np.nan, np.nan, 62.0, 110.0],
        "batt_kwh": [0.0, 0.0, 15.0, 75.0],
        "n": [1000.0, 500.0, 200.0, 300.0],
        "vmt": [12000.0] * 4,
        "high_VMT_prop": [0.76] * 4,
    })


class TestEvRange:
    def test_bev_range(self):
        r = get_ev_range_from_batt_kwh(75.0, 110.0, "bev")
        assert r is not None
        assert r > 200  # Should be a reasonable EV range

    def test_phev_range(self):
        r = get_ev_range_from_batt_kwh(15.0, 62.0, "phev")
        assert r is not None
        assert 20 < r < 80

    def test_icev_returns_none(self):
        assert get_ev_range_from_batt_kwh(0, 30, "icev") is None


class TestUtilityFactor:
    def test_higher_range_means_higher_uf(self):
        uf_low = compute_utility_factor(30)
        uf_high = compute_utility_factor(100)
        assert uf_high > uf_low

    def test_uf_between_0_and_1(self):
        for ev_range in [10, 30, 50, 100, 200, 300]:
            uf = compute_utility_factor(ev_range)
            assert 0 <= uf <= 1

    def test_large_range_near_one(self):
        uf = compute_utility_factor(300)
        assert uf > 0.9


class TestProductionEmissions:
    def test_only_new_vehicles_get_emissions(self, icev_fleet):
        result = compute_production_emissions(icev_fleet)
        # Age 0 should have emissions, age 5 should not
        new = result[result["age"] == 0]
        old = result[result["age"] == 5]
        assert new["production_ghg"].values[0] > 0
        assert old["production_ghg"].values[0] == 0

    def test_icev_production(self):
        fleet = pd.DataFrame({
            "age": [0], "powertrain": ["icev"], "vmt_bucket": ["high"],
            "mpg": [30.0], "mpge": [np.nan], "batt_kwh": [0.0],
            "n": [1.0], "vmt": [12000.0], "high_VMT_prop": [0.76],
        })
        result = compute_production_emissions(fleet)
        # Body (4200) + ICE (1400) = 5600
        assert abs(result["production_ghg"].values[0] - 5600) < 1

    def test_bev_production(self):
        fleet = pd.DataFrame({
            "age": [0], "powertrain": ["bev"], "vmt_bucket": ["high"],
            "mpg": [np.nan], "mpge": [110.0], "batt_kwh": [75.0],
            "n": [1.0], "vmt": [12000.0], "high_VMT_prop": [0.76],
        })
        result = compute_production_emissions(fleet)
        # Body (4200) + Battery (75 * 100 = 7500) = 11700
        assert abs(result["production_ghg"].values[0] - 11700) < 1

    def test_phev_production(self):
        fleet = pd.DataFrame({
            "age": [0], "powertrain": ["phev"], "vmt_bucket": ["high"],
            "mpg": [25.0], "mpge": [62.0], "batt_kwh": [15.0],
            "n": [1.0], "vmt": [12000.0], "high_VMT_prop": [0.76],
        })
        result = compute_production_emissions(fleet)
        # Body (4200) + ICE (1400) + Battery (15 * 100 = 1500) = 7100
        assert abs(result["production_ghg"].values[0] - 7100) < 1

    def test_hev_production(self):
        fleet = pd.DataFrame({
            "age": [0], "powertrain": ["hev"], "vmt_bucket": ["high"],
            "mpg": [40.0], "mpge": [np.nan], "batt_kwh": [0.0],
            "n": [1.0], "vmt": [12000.0], "high_VMT_prop": [0.76],
        })
        result = compute_production_emissions(fleet)
        # Body (4200) + ICE (1400) = 5600 (HEV has ICE but no significant battery)
        assert abs(result["production_ghg"].values[0] - 5600) < 1


class TestUsageEmissions:
    def test_icev_gasoline_emissions(self, icev_fleet):
        result = compute_usage_emissions(icev_fleet)
        # For age 0: 1000 * 15000 / 30 * 8.89 = 4,445,000
        expected = 1000 * 15000 / 30 * 8.89
        assert abs(result.loc[0, "ghg_gas"] - expected) < 1

    def test_icev_no_electric_emissions(self, icev_fleet):
        result = compute_usage_emissions(icev_fleet)
        assert (result["ghg_electric"] == 0).all()

    def test_bev_no_gas_emissions(self, bev_fleet):
        result = compute_usage_emissions(bev_fleet)
        assert (result["ghg_gas"] == 0).all()

    def test_bev_has_electric_emissions(self, bev_fleet):
        result = compute_usage_emissions(bev_fleet)
        assert (result["ghg_electric"] > 0).all()

    def test_phev_splits_emissions(self, phev_fleet):
        result = compute_usage_emissions(phev_fleet)
        # PHEV should have both gas and electric emissions
        assert result["ghg_gas"].values[0] > 0
        assert result["ghg_electric"].values[0] > 0
        # Utility factor should reduce gas vs pure ICEV
        pure_gas = 100 * 12000 / 25 * 8.89
        assert result["ghg_gas"].values[0] < pure_gas

    def test_total_usage_is_sum(self, mixed_fleet):
        result = compute_usage_emissions(mixed_fleet)
        for idx in result.index:
            assert abs(result.loc[idx, "use_ghg"] - (result.loc[idx, "ghg_gas"] + result.loc[idx, "ghg_electric"])) < 0.01

    def test_grid_decarbonization_reduces_electric_emissions(self, bev_fleet):
        result_high = compute_usage_emissions(bev_fleet, grid_ghg_per_kwh=0.369)
        result_low = compute_usage_emissions(bev_fleet, grid_ghg_per_kwh=0.200)
        assert result_low["ghg_electric"].sum() < result_high["ghg_electric"].sum()

    def test_biofuel_blending_reduces_gas_emissions(self, icev_fleet):
        result_high = compute_usage_emissions(icev_fleet, gas_ghg_per_gallon=8.89)
        result_low = compute_usage_emissions(icev_fleet, gas_ghg_per_gallon=8.00)
        assert result_low["ghg_gas"].sum() < result_high["ghg_gas"].sum()


class TestDisposalEmissions:
    def test_disposal_computation(self):
        scrapped = pd.DataFrame({
            "n": [100.0, 50.0],
            "powertrain": ["icev", "bev"],
        })
        result = compute_disposal_emissions(scrapped)
        assert result["disposal_ghg"].values[0] == 100 * 2800
        assert result["disposal_ghg"].values[1] == 50 * 2800

    def test_custom_disposal_rate(self):
        scrapped = pd.DataFrame({"n": [100.0], "powertrain": ["icev"]})
        result = compute_disposal_emissions(scrapped, disposal_per_vehicle=3000.0)
        assert result["disposal_ghg"].values[0] == 300000.0


class TestAggregateEmissions:
    def test_aggregate_sums_correctly(self, mixed_fleet):
        fleet = compute_production_emissions(mixed_fleet)
        fleet = compute_usage_emissions(fleet)
        scrapped = pd.DataFrame({"n": [50.0], "powertrain": ["icev"]})
        scrapped = compute_disposal_emissions(scrapped)

        agg = aggregate_emissions(fleet, scrapped)
        assert agg["total_ghg"] == (
            agg["production_ghg"] + agg["usage_ghg_total"] + agg["disposal_ghg"]
        )

    def test_disaggregated_by_powertrain(self, mixed_fleet):
        fleet = compute_production_emissions(mixed_fleet)
        fleet = compute_usage_emissions(fleet)
        agg = aggregate_emissions(fleet)

        assert "icev" in agg["by_powertrain"]
        assert "bev" in agg["by_powertrain"]
        assert "phev" in agg["by_powertrain"]
        assert "hev" in agg["by_powertrain"]

    def test_no_scrapped_vehicles(self, mixed_fleet):
        fleet = compute_production_emissions(mixed_fleet)
        fleet = compute_usage_emissions(fleet)
        agg = aggregate_emissions(fleet)
        assert agg["disposal_ghg"] == 0.0
        assert agg["total_ghg"] > 0

    def test_usage_breakdown(self, mixed_fleet):
        fleet = compute_production_emissions(mixed_fleet)
        fleet = compute_usage_emissions(fleet)
        agg = aggregate_emissions(fleet)
        assert abs(agg["usage_ghg_total"] - (agg["usage_ghg_gas"] + agg["usage_ghg_electric"])) < 0.01
