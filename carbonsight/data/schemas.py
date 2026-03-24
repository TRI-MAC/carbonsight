"""Pandera schemas for validating CarbonSight input DataFrames.

Validates fleet inventory, survival curves, VMT-by-age, and powertrain
proportion data on ingest.
"""

from __future__ import annotations

from pandera import Check, Column, DataFrameSchema

fleet_inventory_schema = DataFrameSchema(
    {
        "age": Column(int, Check.ge(0), nullable=False),
        "powertrain": Column(str, Check.isin(["icev", "hev", "phev", "bev"]), nullable=False),
        "mpg": Column(float, Check.gt(0), nullable=True),  # NA for BEV
        "mpge": Column(float, Check.gt(0), nullable=True),  # NA for ICEV
        "batt_kwh": Column(float, Check.ge(0), nullable=True),  # NaN for ICEV/HEV without battery
        "n": Column(float, Check.ge(0), nullable=False),  # 0 for cohorts not yet in fleet
        "vmt": Column(float, Check.gt(0), nullable=False),
        "high_VMT_prop": Column(float, Check.in_range(0, 1), nullable=False),
        "vmt_bucket": Column(str, Check.isin(["high", "low"]), nullable=False),
    },
    coerce=True,
    strict=False,  # Allow extra columns
)


survival_curve_schema = DataFrameSchema(
    {
        "age": Column(int, Check.ge(0), nullable=False),
        "lag1_scrappage": Column(float, Check.in_range(0, 1), nullable=False),
        "survival": Column(float, Check.in_range(0, 1), nullable=False),
    },
    coerce=True,
    strict=False,
)


vmt_by_age_schema = DataFrameSchema(
    {
        "age": Column(int, Check.ge(0), nullable=False),
        "low": Column(float, Check.gt(0), nullable=False),
        "high": Column(float, Check.gt(0), nullable=False),
        "vmt": Column(float, Check.gt(0), nullable=False),
        "high_VMT_prop": Column(float, Check.in_range(0, 1), nullable=False),
    },
    coerce=True,
    strict=False,
)


powertrain_proportions_schema = DataFrameSchema(
    {
        "powertrain": Column(str, Check.isin(["icev", "hev", "phev", "bev"]), nullable=False),
        "year": Column(int, Check.ge(0), nullable=False),
        "proportion": Column(float, Check.ge(0), nullable=False),
    },
    coerce=True,
    strict=False,
)
