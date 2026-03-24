"""Emissions model for CarbonSight.

Calculates production, usage (gasoline + electricity), and disposal GHG emissions
for the vehicle fleet, with support for time-varying emission factors.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# PHEV utility factor polynomial coefficients (from Ekiden v1)
# Maps EV range → fraction of miles on electricity
UF_COEFFICIENTS = [10.52, -7.28, -26.37, 79.08, -77.36, 26.07]
UF_NORM_DISTANCE = 400


def get_ev_range_from_batt_kwh(batt_kwh: float, mpge: float, powertrain: str) -> float | None:
    """Estimate EV range from battery size and electrical efficiency."""
    if powertrain == "phev":
        return -14.21 + 1.346 * batt_kwh + 0.3205 * mpge + 0.0003 * batt_kwh * mpge
    elif powertrain == "bev":
        return 13.518727 + 0.047706 * batt_kwh + 0.291313 * mpge + 0.025649 * batt_kwh * mpge
    return None


def compute_utility_factor(ev_range: float) -> float:
    """Compute PHEV utility factor from EV range using polynomial fit.

    Returns a value between 0 and 1 representing the fraction of miles driven on electricity.
    """
    x = ev_range / UF_NORM_DISTANCE
    exponent = sum(c * x ** (i + 1) for i, c in enumerate(UF_COEFFICIENTS))
    return float(1 - np.exp(-exponent))


def compute_production_emissions(
    fleet: pd.DataFrame,
    production_body: float = 4200.0,
    production_ice: float = 1400.0,
    production_battery_per_kwh: float = 100.0,
) -> pd.DataFrame:
    """Compute production-phase GHG emissions for new vehicles (age 0 only).

    Returns DataFrame with production_ghg column (kg CO2).
    """
    result = fleet.copy()
    result["production_ghg"] = 0.0

    # Only new vehicles get production emissions
    new_mask = result["age"] == 0

    # Body emissions for all new vehicles
    result.loc[new_mask, "production_ghg"] = result.loc[new_mask, "n"] * production_body

    # ICE powertrain emissions (ICEV, HEV, PHEV have ICE)
    ice_mask = new_mask & result["powertrain"].isin(["icev", "hev", "phev"])
    result.loc[ice_mask, "production_ghg"] += result.loc[ice_mask, "n"] * production_ice

    # Battery emissions (PHEV, BEV have batteries)
    batt_mask = new_mask & result["powertrain"].isin(["phev", "bev"])
    batt_kwh = result.loc[batt_mask, "batt_kwh"].fillna(0)
    result.loc[batt_mask, "production_ghg"] += (
        result.loc[batt_mask, "n"] * batt_kwh * production_battery_per_kwh
    )

    return result


def compute_usage_emissions(
    fleet: pd.DataFrame,
    gas_ghg_per_gallon: float = 8.89,
    grid_ghg_per_kwh: float = 0.369,
    charging_factor: float = 1.0,
) -> pd.DataFrame:
    """Compute usage-phase GHG emissions for all active vehicles.

    Computes both gasoline and electricity emissions, using utility factor
    for PHEVs to split VMT between electric and gas driving.

    Args:
        fleet: Fleet DataFrame with n, vmt, mpg, mpge, batt_kwh, powertrain columns.
        gas_ghg_per_gallon: Gasoline GHG intensity (kg CO2/gallon).
        grid_ghg_per_kwh: Grid carbon intensity (kg CO2/kWh).
        charging_factor: Fraction of optimal charging realized (0-1, default 1.0).

    Returns:
        Fleet DataFrame with added usage emission columns.
    """
    result = fleet.copy()

    # Compute EV range for BEV/PHEV where missing
    if "ev_range" not in result.columns:
        result["ev_range"] = np.nan

    for idx in result.index:
        pt = result.loc[idx, "powertrain"]
        if pt in ("bev", "phev") and pd.isna(result.loc[idx, "ev_range"]):
            bkwh = result.loc[idx, "batt_kwh"]
            mpge_val = result.loc[idx, "mpge"]
            if pd.notna(bkwh) and pd.notna(mpge_val):
                result.loc[idx, "ev_range"] = get_ev_range_from_batt_kwh(bkwh, mpge_val, pt)

    # Compute utility factor
    result["utility_factor"] = 0.0
    for idx in result.index:
        pt = result.loc[idx, "powertrain"]
        if pt == "bev":
            result.loc[idx, "utility_factor"] = 1.0
        elif pt == "phev":
            ev_r = result.loc[idx, "ev_range"]
            if pd.notna(ev_r) and ev_r > 0:
                result.loc[idx, "utility_factor"] = compute_utility_factor(ev_r) * charging_factor
            else:
                result.loc[idx, "utility_factor"] = 0.0

    # Gasoline emissions: VMT * (1 - UF) / MPG * ghg_per_gallon
    gas_fraction = 1 - result["utility_factor"]
    mpg_safe = result["mpg"].fillna(np.inf)  # BEVs have no mpg
    result["ghg_gas"] = result["n"] * result["vmt"] * gas_fraction / mpg_safe * gas_ghg_per_gallon
    # Zero out for BEVs (they have no gas usage)
    result.loc[result["powertrain"] == "bev", "ghg_gas"] = 0.0

    # Electricity emissions: VMT * UF / MPGe * (grid_ghg_per_kwh * 33.7)
    # 33.7 kWh per gallon equivalent
    kwh_per_gallon_equiv = 33.7
    electricity_ghg_per_gallon_equiv = grid_ghg_per_kwh * kwh_per_gallon_equiv
    mpge_safe = result["mpge"].fillna(np.inf)  # ICEVs have no mpge
    result["ghg_electric"] = (
        result["n"]
        * result["vmt"]
        * result["utility_factor"]
        / mpge_safe
        * electricity_ghg_per_gallon_equiv
    )
    # Zero out for ICEV/HEV (no electric usage)
    result.loc[result["powertrain"].isin(["icev", "hev"]), "ghg_electric"] = 0.0

    result["use_ghg"] = result["ghg_gas"] + result["ghg_electric"]

    return result


def compute_disposal_emissions(
    scrapped: pd.DataFrame,
    disposal_per_vehicle: float = 2800.0,
) -> pd.DataFrame:
    """Compute disposal-phase GHG for scrapped vehicles.

    Returns DataFrame with disposal_ghg column (kg CO2).
    """
    result = scrapped.copy()
    result["disposal_ghg"] = result["n"] * disposal_per_vehicle
    return result


def aggregate_emissions(
    fleet_with_emissions: pd.DataFrame,
    scrapped_with_disposal: pd.DataFrame | None = None,
) -> dict:
    """Aggregate total emissions across all vehicles for one simulation year.

    Returns dict with:
        production_ghg, usage_ghg_gas, usage_ghg_electric, usage_ghg_total,
        disposal_ghg, total_ghg, by_powertrain
    """
    production = fleet_with_emissions.get("production_ghg", pd.Series([0])).sum()
    gas = fleet_with_emissions.get("ghg_gas", pd.Series([0])).sum()
    electric = fleet_with_emissions.get("ghg_electric", pd.Series([0])).sum()
    use_total = gas + electric

    disposal = 0.0
    if scrapped_with_disposal is not None and "disposal_ghg" in scrapped_with_disposal.columns:
        disposal = scrapped_with_disposal["disposal_ghg"].sum()

    total = production + use_total + disposal

    # By powertrain breakdown
    by_pt = {}
    for pt in fleet_with_emissions["powertrain"].unique():
        mask = fleet_with_emissions["powertrain"] == pt
        pt_prod = (
            fleet_with_emissions.loc[mask, "production_ghg"].sum()
            if "production_ghg" in fleet_with_emissions.columns
            else 0
        )
        pt_gas = (
            fleet_with_emissions.loc[mask, "ghg_gas"].sum()
            if "ghg_gas" in fleet_with_emissions.columns
            else 0
        )
        pt_elec = (
            fleet_with_emissions.loc[mask, "ghg_electric"].sum()
            if "ghg_electric" in fleet_with_emissions.columns
            else 0
        )
        by_pt[pt] = {
            "production": pt_prod,
            "usage_gas": pt_gas,
            "usage_electric": pt_elec,
            "usage_total": pt_gas + pt_elec,
        }

    return {
        "production_ghg": production,
        "usage_ghg_gas": gas,
        "usage_ghg_electric": electric,
        "usage_ghg_total": use_total,
        "disposal_ghg": disposal,
        "total_ghg": total,
        "by_powertrain": by_pt,
    }
