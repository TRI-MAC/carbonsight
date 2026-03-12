"""Tests for data loading and schema validation."""

import pandas as pd
import pytest

from carbonsight.data.loaders import (
    load_fleet_inventory,
    load_powertrain_proportions,
    load_survival_curves,
    load_vmt_by_age,
)
from carbonsight.data.models import EmissionsFactors, MacroDriverDefaults
from carbonsight.data.schemas import fleet_inventory_schema


class TestFleetInventoryLoader:
    def test_loads_successfully(self):
        df = load_fleet_inventory()
        assert len(df) > 0
        assert "age" in df.columns
        assert "powertrain" in df.columns
        assert "n" in df.columns

    def test_powertrains_are_valid(self):
        df = load_fleet_inventory()
        assert set(df["powertrain"].unique()).issubset({"icev", "hev", "phev", "bev"})

    def test_has_high_and_low_vmt_buckets(self):
        df = load_fleet_inventory()
        assert set(df["vmt_bucket"].unique()) == {"high", "low"}


class TestSurvivalCurveLoader:
    def test_loads_successfully(self):
        df = load_survival_curves()
        assert len(df) > 0
        assert "age" in df.columns
        assert "lag1_scrappage" in df.columns
        assert "survival" in df.columns

    def test_scrappage_rates_valid(self):
        df = load_survival_curves()
        assert df["lag1_scrappage"].between(0, 1).all()
        assert df["survival"].between(0, 1).all()


class TestVmtByAgeLoader:
    def test_loads_successfully(self):
        df = load_vmt_by_age()
        assert len(df) > 0
        assert "age" in df.columns
        assert "vmt" in df.columns

    def test_vmt_positive(self):
        df = load_vmt_by_age()
        assert (df["vmt"] > 0).all()
        assert (df["high"] > 0).all()
        assert (df["low"] > 0).all()


class TestPowertrainProportionsLoader:
    def test_loads_successfully(self):
        df = load_powertrain_proportions()
        assert len(df) > 0
        assert "powertrain" in df.columns
        assert "proportion" in df.columns

    def test_proportions_are_fractions(self):
        df = load_powertrain_proportions()
        assert (df["proportion"] >= 0).all()
        assert (df["proportion"] <= 1).all()


class TestSchemaValidation:
    def test_invalid_fleet_inventory_rejected(self):
        bad_df = pd.DataFrame({
            "age": [-1],  # Negative age
            "powertrain": ["icev"],
            "mpg": [30.0],
            "mpge": [None],
            "batt_kwh": [0.0],
            "n": [100.0],
            "vmt": [10000.0],
            "high_VMT_prop": [0.76],
            "vmt_bucket": ["high"],
        })
        with pytest.raises(Exception):  # Pandera SchemaError
            fleet_inventory_schema.validate(bad_df)

    def test_invalid_powertrain_rejected(self):
        bad_df = pd.DataFrame({
            "age": [0],
            "powertrain": ["diesel"],  # Not in valid set
            "mpg": [30.0],
            "mpge": [None],
            "batt_kwh": [0.0],
            "n": [100.0],
            "vmt": [10000.0],
            "high_VMT_prop": [0.76],
            "vmt_bucket": ["high"],
        })
        with pytest.raises(Exception):
            fleet_inventory_schema.validate(bad_df)


class TestPydanticModels:
    def test_emissions_factors_defaults(self):
        ef = EmissionsFactors()
        assert ef.production_body == 4200
        assert ef.gas_ghg_per_gallon == 8.89
        assert ef.production_battery_per_kwh_low < ef.production_battery_per_kwh < ef.production_battery_per_kwh_high

    def test_macro_driver_defaults(self):
        md = MacroDriverDefaults()
        assert len(md.oil_price_per_barrel.values) == 10
        assert len(md.electricity_price_per_kwh.values) == 10
        assert md.vmt_oil_price_elasticity == -0.2
