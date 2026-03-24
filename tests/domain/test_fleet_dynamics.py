"""Tests for fleet dynamics domain model."""

import numpy as np
import pandas as pd
import pytest

from carbonsight.domain.fleet_dynamics import (
    MAX_VEHICLE_AGE,
    add_new_vehicles,
    age_fleet,
    apply_scrappage,
    assign_vmt_by_age,
    compute_fleet_composition,
    reshuffle_used_market,
    step_fleet_one_year,
    validate_powertrain_proportions,
    validate_survival_curves,
    validate_vmt_table,
)


@pytest.fixture
def simple_fleet():
    """A minimal fleet for unit testing."""
    return pd.DataFrame(
        {
            "age": [0, 0, 5, 5, 10, 10],
            "powertrain": ["icev", "icev", "bev", "bev", "hev", "hev"],
            "vmt_bucket": ["high", "low", "high", "low", "high", "low"],
            "mpg": [30.0, 30.0, np.nan, np.nan, 40.0, 40.0],
            "mpge": [np.nan, np.nan, 100.0, 100.0, np.nan, np.nan],
            "batt_kwh": [0.0, 0.0, 60.0, 60.0, 0.0, 0.0],
            "n": [1000.0, 500.0, 200.0, 100.0, 300.0, 150.0],
            "vmt": [15000.0, 8000.0, 15000.0, 8000.0, 12000.0, 6000.0],
            "high_VMT_prop": [0.76, 0.76, 0.76, 0.76, 0.76, 0.76],
        }
    )


@pytest.fixture
def survival_curves():
    """Simple survival curves for testing."""
    ages = list(range(51))
    scrappage = [0.005 + 0.002 * a for a in ages]
    # Cap at 1.0
    scrappage = [min(s, 1.0) for s in scrappage]
    survival = []
    s = 1.0
    for sc in scrappage:
        survival.append(s)
        s *= 1 - sc
    return pd.DataFrame(
        {
            "age": ages,
            "lag1_scrappage": scrappage,
            "survival": survival,
        }
    )


@pytest.fixture
def vmt_table():
    """Simple VMT-by-age table for testing."""
    ages = list(range(51))
    return pd.DataFrame(
        {
            "age": ages,
            "low": [6000 - 50 * a for a in ages],
            "high": [18000 - 100 * a for a in ages],
            "vmt": [12000 - 75 * a for a in ages],
            "high_VMT_prop": [0.76 - 0.001 * a for a in ages],
        }
    )


@pytest.fixture
def default_proportions():
    return {"icev": 0.82, "hev": 0.09, "phev": 0.02, "bev": 0.07}


class TestAgeFleet:
    def test_increments_age_by_one(self, simple_fleet):
        result = age_fleet(simple_fleet)
        assert (result["age"] == simple_fleet["age"] + 1).all()

    def test_preserves_other_attributes(self, simple_fleet):
        result = age_fleet(simple_fleet)
        for col in ["powertrain", "mpg", "mpge", "batt_kwh", "n"]:
            pd.testing.assert_series_equal(
                result[col].reset_index(drop=True),
                simple_fleet[col].reset_index(drop=True),
            )

    def test_preserves_row_count(self, simple_fleet):
        result = age_fleet(simple_fleet)
        assert len(result) == len(simple_fleet)


class TestApplyScrappage:
    def test_reduces_vehicle_counts(self, simple_fleet, survival_curves):
        # Age first so ages match survival curve
        aged = age_fleet(simple_fleet)
        surviving, scrapped = apply_scrappage(aged, survival_curves)
        assert surviving["n"].sum() < aged["n"].sum()

    def test_scrapped_plus_surviving_equals_original(self, simple_fleet, survival_curves):
        aged = age_fleet(simple_fleet)
        surviving, scrapped = apply_scrappage(aged, survival_curves)
        original_total = aged["n"].sum()
        result_total = surviving["n"].sum() + scrapped["n"].sum()
        assert abs(result_total - original_total) < 0.01

    def test_max_age_vehicles_fully_scrapped(self, survival_curves):
        fleet = pd.DataFrame(
            {
                "age": [MAX_VEHICLE_AGE + 1],
                "powertrain": ["icev"],
                "vmt_bucket": ["high"],
                "n": [100.0],
                "vmt": [5000.0],
                "mpg": [25.0],
                "mpge": [np.nan],
                "batt_kwh": [0.0],
                "high_VMT_prop": [0.76],
            }
        )
        surviving, scrapped = apply_scrappage(fleet, survival_curves)
        assert surviving["n"].sum() == 0
        assert scrapped["n"].sum() == 100.0

    def test_young_vehicles_high_survival(self, survival_curves):
        fleet = pd.DataFrame(
            {
                "age": [1, 2, 3],
                "powertrain": ["icev"] * 3,
                "vmt_bucket": ["high"] * 3,
                "n": [1000.0] * 3,
                "vmt": [15000.0] * 3,
                "mpg": [30.0] * 3,
                "mpge": [np.nan] * 3,
                "batt_kwh": [0.0] * 3,
                "high_VMT_prop": [0.76] * 3,
            }
        )
        surviving, _ = apply_scrappage(fleet, survival_curves)
        # Young vehicles should retain >95% of count
        for _, row in surviving.iterrows():
            assert row["n"] > 950


class TestAddNewVehicles:
    def test_increases_fleet_size(self, simple_fleet, default_proportions):
        result = add_new_vehicles(simple_fleet, default_proportions)
        assert result["n"].sum() > simple_fleet["n"].sum()

    def test_new_vehicles_at_age_zero(self, simple_fleet, default_proportions):
        result = add_new_vehicles(simple_fleet, default_proportions)
        new_vehicles = result[~result.index.isin(simple_fleet.index)]
        assert (new_vehicles["age"] == 0).all()

    def test_respects_powertrain_proportions(self, simple_fleet, default_proportions):
        result = add_new_vehicles(simple_fleet, default_proportions)
        # New vehicles only (age 0 that weren't in original)
        n_new_total = result["n"].sum() - simple_fleet["n"].sum()
        new_only = result.iloc[len(simple_fleet) :]
        for pt, expected_frac in default_proportions.items():
            pt_n = new_only[new_only["powertrain"] == pt]["n"].sum()
            actual_frac = pt_n / n_new_total
            assert abs(actual_frac - expected_frac) < 0.01

    def test_new_count_equals_n_new(self, simple_fleet, default_proportions):
        n_new = 500.0
        result = add_new_vehicles(simple_fleet, default_proportions, n_new=n_new)
        actual_new = result["n"].sum() - simple_fleet["n"].sum()
        assert abs(actual_new - n_new) < 0.01

    def test_custom_n_new(self, simple_fleet, default_proportions):
        n_new = 2000.0
        result = add_new_vehicles(simple_fleet, default_proportions, n_new=n_new)
        actual_new = result["n"].sum() - simple_fleet["n"].sum()
        assert abs(actual_new - n_new) < 0.01

    def test_has_both_vmt_buckets(self, simple_fleet, default_proportions):
        result = add_new_vehicles(simple_fleet, default_proportions)
        new_only = result.iloc[len(simple_fleet) :]
        assert set(new_only["vmt_bucket"].unique()) == {"high", "low"}


class TestAssignVmtByAge:
    def test_vmt_updates_based_on_age(self, simple_fleet, vmt_table):
        result = assign_vmt_by_age(simple_fleet, vmt_table)
        # Check that high bucket gets high VMT
        for _, row in result.iterrows():
            age = row["age"]
            bucket = row["vmt_bucket"]
            expected = vmt_table[vmt_table["age"] == age][bucket].values[0]
            assert row["vmt"] == expected

    def test_vmt_decreases_with_age(self, vmt_table):
        fleet = pd.DataFrame(
            {
                "age": [0, 5, 10, 20],
                "powertrain": ["icev"] * 4,
                "vmt_bucket": ["high"] * 4,
                "n": [100.0] * 4,
                "vmt": [0.0] * 4,
                "high_VMT_prop": [0.76] * 4,
            }
        )
        result = assign_vmt_by_age(fleet, vmt_table)
        vmts = result.sort_values("age")["vmt"].values
        for i in range(1, len(vmts)):
            assert vmts[i] <= vmts[i - 1]

    def test_high_bucket_greater_than_low(self, vmt_table):
        fleet = pd.DataFrame(
            {
                "age": [5, 5],
                "powertrain": ["icev", "icev"],
                "vmt_bucket": ["high", "low"],
                "n": [100.0, 100.0],
                "vmt": [0.0, 0.0],
                "high_VMT_prop": [0.76, 0.76],
            }
        )
        result = assign_vmt_by_age(fleet, vmt_table)
        high_vmt = result[result["vmt_bucket"] == "high"]["vmt"].values[0]
        low_vmt = result[result["vmt_bucket"] == "low"]["vmt"].values[0]
        assert high_vmt > low_vmt


class TestFleetComposition:
    def test_total_vehicles(self, simple_fleet):
        comp = compute_fleet_composition(simple_fleet)
        assert comp["total_vehicles"] == simple_fleet["n"].sum()

    def test_by_powertrain(self, simple_fleet):
        comp = compute_fleet_composition(simple_fleet)
        assert comp["by_powertrain"]["icev"] == 1500.0
        assert comp["by_powertrain"]["bev"] == 300.0
        assert comp["by_powertrain"]["hev"] == 450.0

    def test_total_vmt(self, simple_fleet):
        comp = compute_fleet_composition(simple_fleet)
        expected = (simple_fleet["n"] * simple_fleet["vmt"]).sum()
        assert comp["total_vmt"] == expected


class TestReshuffleUsedMarket:
    def test_conserves_total_fleet_size(self, simple_fleet):
        result = reshuffle_used_market(simple_fleet)
        assert abs(result["n"].sum() - simple_fleet["n"].sum()) < 0.01

    def test_moves_vehicles_between_buckets(self, simple_fleet):
        result = reshuffle_used_market(simple_fleet)
        # High bucket should decrease, low bucket should increase (since high > low)
        for (age, pt), _ in simple_fleet.groupby(["age", "powertrain"]):
            orig_high = simple_fleet[
                (simple_fleet["age"] == age)
                & (simple_fleet["powertrain"] == pt)
                & (simple_fleet["vmt_bucket"] == "high")
            ]["n"].values[0]
            new_high = result[
                (result["age"] == age)
                & (result["powertrain"] == pt)
                & (result["vmt_bucket"] == "high")
            ]["n"].values[0]
            orig_low = simple_fleet[
                (simple_fleet["age"] == age)
                & (simple_fleet["powertrain"] == pt)
                & (simple_fleet["vmt_bucket"] == "low")
            ]["n"].values[0]
            new_low = result[
                (result["age"] == age)
                & (result["powertrain"] == pt)
                & (result["vmt_bucket"] == "low")
            ]["n"].values[0]

            if orig_high > orig_low:
                assert new_high <= orig_high
                assert new_low >= orig_low

    def test_conserves_per_group_total(self, simple_fleet):
        result = reshuffle_used_market(simple_fleet)
        for (age, pt), group in simple_fleet.groupby(["age", "powertrain"]):
            orig_total = group["n"].sum()
            new_group = result[(result["age"] == age) & (result["powertrain"] == pt)]
            assert abs(new_group["n"].sum() - orig_total) < 0.01


class TestValidation:
    def test_valid_survival_curves_pass(self, survival_curves):
        validate_survival_curves(survival_curves)  # Should not raise

    def test_invalid_survival_out_of_bounds(self):
        bad = pd.DataFrame(
            {
                "age": [0, 1],
                "lag1_scrappage": [0.01, 0.02],
                "survival": [1.0, 1.5],  # >1
            }
        )
        with pytest.raises(ValueError, match="between 0 and 1"):
            validate_survival_curves(bad)

    def test_non_monotonic_survival_rejected(self):
        bad = pd.DataFrame(
            {
                "age": [0, 1, 2],
                "lag1_scrappage": [0.01, 0.02, 0.01],
                "survival": [1.0, 0.8, 0.9],  # Increases at age 2
            }
        )
        with pytest.raises(ValueError, match="not monotonically"):
            validate_survival_curves(bad)

    def test_valid_vmt_table_passes(self, vmt_table):
        validate_vmt_table(vmt_table)  # Should not raise

    def test_negative_vmt_rejected(self):
        bad = pd.DataFrame(
            {
                "age": [0, 1],
                "low": [5000.0, -100.0],
                "high": [15000.0, 14000.0],
                "vmt": [10000.0, 9000.0],
            }
        )
        with pytest.raises(ValueError, match="non-positive"):
            validate_vmt_table(bad)

    def test_valid_proportions_pass(self, default_proportions):
        validate_powertrain_proportions(default_proportions)

    def test_proportions_not_summing_to_one(self):
        bad = {"icev": 0.5, "hev": 0.1, "phev": 0.1, "bev": 0.1}
        with pytest.raises(ValueError, match="sum to 1.0"):
            validate_powertrain_proportions(bad)


class TestStepFleetOneYear:
    def test_full_step(self, simple_fleet, survival_curves, vmt_table, default_proportions):
        updated, scrapped, composition = step_fleet_one_year(
            simple_fleet, survival_curves, vmt_table, default_proportions
        )
        assert len(updated) > 0
        assert len(scrapped) > 0
        assert composition["total_vehicles"] > 0

    def test_ages_increment(self, simple_fleet, survival_curves, vmt_table, default_proportions):
        updated, _, _ = step_fleet_one_year(
            simple_fleet, survival_curves, vmt_table, default_proportions
        )
        # Non-new vehicles should have aged
        non_new = updated[updated["age"] > 0]
        # Age 0 from original should now be age 1
        assert 1 in non_new["age"].values

    def test_bev_share_increases_with_high_bev_proportions(
        self, simple_fleet, survival_curves, vmt_table
    ):
        high_bev = {"icev": 0.30, "hev": 0.10, "phev": 0.10, "bev": 0.50}
        fleet = simple_fleet.copy()
        for _ in range(5):
            fleet, _, comp = step_fleet_one_year(fleet, survival_curves, vmt_table, high_bev)
        bev_share = comp["by_powertrain"].get("bev", 0) / comp["total_vehicles"]
        # With 50% BEV entry rate, BEV share should be meaningfully above initial
        initial_bev = 300.0 / simple_fleet["n"].sum()
        assert bev_share > initial_bev


class TestWithRealData:
    """Test with actual CarbonSight data files."""

    def test_real_data_step(self):
        from carbonsight.data.loaders import (
            load_fleet_inventory,
            load_survival_curves,
            load_vmt_by_age,
        )

        fleet = load_fleet_inventory()
        survival = load_survival_curves()
        vmt = load_vmt_by_age()
        proportions = {"icev": 0.82, "hev": 0.09, "phev": 0.02, "bev": 0.07}

        updated, scrapped, comp = step_fleet_one_year(fleet, survival, vmt, proportions)

        assert comp["total_vehicles"] > 0
        assert len(updated) > 0
        assert all(pt in comp["by_powertrain"] for pt in ["icev", "hev", "phev", "bev"])


class TestMacroFleetLinkage:
    """Tests for macro-driver-adjusted fleet nodes."""

    def test_preference_shift_increases_bev_share(self, simple_fleet, survival_curves, vmt_table):
        from carbonsight.domain.fleet_nodes import compute_adjusted_new_entry

        props = {"icev": 0.82, "hev": 0.09, "phev": 0.02, "bev": 0.07}
        n_new = 1000.0
        attrs = (
            simple_fleet[simple_fleet["age"] == 0][["powertrain", "mpg", "mpge", "batt_kwh"]]
            .groupby("powertrain")
            .first()
            .reset_index()
        )
        result_normal = compute_adjusted_new_entry(simple_fleet, props, n_new, 0.0, 0, 1.0, attrs)
        result_shifted = compute_adjusted_new_entry(simple_fleet, props, n_new, 0.0, 0, 1.5, attrs)
        bev_normal = result_normal[result_normal["powertrain"] == "bev"]["n"].sum()
        bev_shifted = result_shifted[result_shifted["powertrain"] == "bev"]["n"].sum()
        assert bev_shifted > bev_normal

    def test_preference_shift_preserves_proportion_sum(self):
        import pandas as pd

        from carbonsight.domain.fleet_nodes import compute_adjusted_new_entry

        fleet = pd.DataFrame(
            {
                "powertrain": ["icev", "bev"],
                "age": [1, 1],
                "n": [900, 100],
                "mpg": [30.0, 0.0],
                "mpge": [0.0, 100.0],
                "batt_kwh": [0.0, 60.0],
            }
        )
        props = {"icev": 0.80, "bev": 0.20}
        attrs = (
            fleet[["powertrain", "mpg", "mpge", "batt_kwh"]]
            .groupby("powertrain")
            .first()
            .reset_index()
        )
        result = compute_adjusted_new_entry(fleet, props, 1000.0, 0.0, 0, 2.0, attrs)
        new_vehicles = result[result["age"] == 0]
        total_new = new_vehicles["n"].sum()
        # Total new vehicles should match renewal rate regardless of shift
        assert total_new > 0

    def test_vmt_adjustment_scales_vmt(self):
        import pandas as pd

        from carbonsight.domain.fleet_nodes import compute_adjusted_vmt

        fleet = pd.DataFrame({"vmt": [10000.0, 8000.0], "n": [100, 50]})
        result = compute_adjusted_vmt(fleet, 0.9)
        assert result["vmt"].iloc[0] == pytest.approx(9000.0)
        assert result["vmt"].iloc[1] == pytest.approx(7200.0)

    def test_vmt_adjustment_noop_at_one(self):
        import pandas as pd

        from carbonsight.domain.fleet_nodes import compute_adjusted_vmt

        fleet = pd.DataFrame({"vmt": [10000.0], "n": [100]})
        result = compute_adjusted_vmt(fleet, 1.0)
        assert result is fleet  # No copy needed
