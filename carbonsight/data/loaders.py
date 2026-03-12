"""Data loaders for CarbonSight CSV sources with schema validation.

Each loader reads a CSV, validates against the Pandera schema, and returns
a clean DataFrame ready for use in the simulation.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from carbonsight.data.schemas import (
    fleet_inventory_schema,
    powertrain_proportions_schema,
    survival_curve_schema,
    vmt_by_age_schema,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


def load_fleet_inventory(path: Path | None = None) -> pd.DataFrame:
    """Load and validate the fleet inventory (current_veh_t0_VMT.csv)."""
    path = path or DATA_DIR / "current_veh_t0_VMT.csv"
    df = pd.read_csv(path)
    # Convert NA strings to NaN for numeric columns
    for col in ["mpg", "mpge"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return fleet_inventory_schema.validate(df)


def load_survival_curves(path: Path | None = None) -> pd.DataFrame:
    """Load and validate survival curves (averaged_survival_v2.csv)."""
    path = path or DATA_DIR / "averaged_survival_v2.csv"
    df = pd.read_csv(path)
    return survival_curve_schema.validate(df)


def load_vmt_by_age(path: Path | None = None) -> pd.DataFrame:
    """Load and validate VMT-by-age data (vmt_by_age.csv)."""
    path = path or DATA_DIR / "vmt_by_age.csv"
    df = pd.read_csv(path)
    return vmt_by_age_schema.validate(df)


def load_powertrain_proportions(path: Path | None = None) -> pd.DataFrame:
    """Load and validate powertrain proportions (epa_table3.csv).

    Normalizes proportions to fractions (0-1) if they sum to ~100.
    """
    path = path or DATA_DIR / "epa_table3.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")  # Handle BOM
    # Normalize: if proportions sum to ~100, divide by 100
    for year_val in df["year"].unique():
        year_mask = df["year"] == year_val
        # Group by pathway if present
        if "pathway" in df.columns:
            for pathway in df["pathway"].unique():
                mask = year_mask & (df["pathway"] == pathway)
                total = df.loc[mask, "proportion"].sum()
                if total > 10:  # Likely percentages, not fractions
                    df.loc[mask, "proportion"] = df.loc[mask, "proportion"] / 100.0
        else:
            total = df.loc[year_mask, "proportion"].sum()
            if total > 10:
                df.loc[year_mask, "proportion"] = df.loc[year_mask, "proportion"] / 100.0

    return powertrain_proportions_schema.validate(df)
