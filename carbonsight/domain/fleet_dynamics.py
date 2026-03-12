"""Fleet dynamics domain model for CarbonSight.

Implements vehicle aging, scrappage, new vehicle entry, VMT assignment,
fleet composition tracking, and used car market dynamics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


MAX_VEHICLE_AGE = 50
DEFAULT_RENEWAL_RATE = 0.05
DEFAULT_RESHUFFLE_PROB = 0.15


def age_fleet(fleet: pd.DataFrame) -> pd.DataFrame:
    """Increment age of every cohort by 1 year, preserving all other attributes."""
    result = fleet.copy()
    result["age"] = result["age"] + 1
    return result


def apply_scrappage(
    fleet: pd.DataFrame, survival_curves: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply survival-curve-based scrappage and max-age cutoff.

    Returns:
        Tuple of (surviving fleet, scrapped vehicles).
    """
    # Unconditionally scrap vehicles exceeding max age
    over_max = fleet[fleet["age"] > MAX_VEHICLE_AGE].copy()
    under_max = fleet[fleet["age"] <= MAX_VEHICLE_AGE].copy()

    # Merge with survival curves to get lag1_scrappage rate
    merged = under_max.merge(
        survival_curves[["age", "lag1_scrappage"]], on="age", how="left"
    )

    # For ages beyond survival curve data, scrap entirely
    merged["lag1_scrappage"] = merged["lag1_scrappage"].fillna(1.0)

    # Compute scrapped and surviving counts
    merged["n_scrapped"] = merged["n"] * merged["lag1_scrappage"]
    merged["n_surviving"] = merged["n"] - merged["n_scrapped"]
    merged.loc[merged["n_surviving"] < 0, "n_surviving"] = 0

    # Build scrapped DataFrame
    scrapped_under_max = merged[merged["n_scrapped"] > 0].copy()
    scrapped_under_max["n"] = scrapped_under_max["n_scrapped"]
    scrapped_cols = [c for c in fleet.columns if c in scrapped_under_max.columns]
    scrapped = pd.concat(
        [scrapped_under_max[scrapped_cols], over_max[scrapped_cols]],
        ignore_index=True,
    )

    # Build surviving DataFrame
    surviving = merged.copy()
    surviving["n"] = surviving["n_surviving"]
    # Drop helper columns
    surviving = surviving.drop(
        columns=["lag1_scrappage", "n_scrapped", "n_surviving"], errors="ignore"
    )

    return surviving, scrapped


def add_new_vehicles(
    fleet: pd.DataFrame,
    powertrain_proportions: dict[str, float],
    renewal_rate: float = DEFAULT_RENEWAL_RATE,
    new_vehicle_attrs: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add new age-0 vehicles to the fleet based on renewal rate and powertrain mix.

    Args:
        fleet: Current fleet DataFrame.
        powertrain_proportions: Dict mapping powertrain -> fraction (must sum to ~1).
        renewal_rate: Fraction of fleet size to add as new vehicles.
        new_vehicle_attrs: Optional DataFrame with powertrain-specific attributes
            (mpg, mpge, batt_kwh) for new vehicles. If None, uses fleet age-0 averages.

    Returns:
        Fleet with new vehicles appended.
    """
    total_fleet = fleet["n"].sum()
    n_new = total_fleet * renewal_rate

    new_rows = []
    for powertrain, proportion in powertrain_proportions.items():
        n_pt = n_new * proportion
        # Split evenly between high and low VMT buckets
        for bucket in ["high", "low"]:
            row = {
                "age": 0,
                "powertrain": powertrain,
                "vmt_bucket": bucket,
                "n": n_pt / 2,
            }

            # Add powertrain-specific attributes from template
            if new_vehicle_attrs is not None:
                pt_row = new_vehicle_attrs[
                    new_vehicle_attrs["powertrain"] == powertrain
                ]
                if len(pt_row) > 0:
                    pt_row = pt_row.iloc[0]
                    for col in ["mpg", "mpge", "batt_kwh", "ev_range"]:
                        if col in pt_row.index:
                            row[col] = pt_row[col]

            new_rows.append(row)

    new_df = pd.DataFrame(new_rows)

    # Ensure columns match
    for col in fleet.columns:
        if col not in new_df.columns:
            new_df[col] = np.nan if fleet[col].dtype in ["float64", "object"] else 0

    result = pd.concat([fleet, new_df[fleet.columns]], ignore_index=True)
    return result


def assign_vmt_by_age(
    fleet: pd.DataFrame, vmt_table: pd.DataFrame
) -> pd.DataFrame:
    """Reassign VMT to each cohort based on age and VMT bucket.

    Args:
        fleet: Fleet DataFrame with age and vmt_bucket columns.
        vmt_table: VMT-by-age data with columns: age, high, low, vmt, high_VMT_prop.

    Returns:
        Fleet with updated vmt and high_VMT_prop columns.
    """
    result = fleet.copy()

    # Drop existing vmt and high_VMT_prop to replace them
    result = result.drop(columns=["vmt", "high_VMT_prop"], errors="ignore")

    # Build lookup: age -> {high: vmt, low: vmt, high_VMT_prop: prop}
    vmt_lookup = vmt_table.set_index("age")

    # For ages beyond the table, use the last available value
    max_table_age = vmt_table["age"].max()

    def get_vmt(row):
        age = min(row["age"], max_table_age)
        if age in vmt_lookup.index:
            bucket = row["vmt_bucket"]
            return vmt_lookup.loc[age, bucket]
        return np.nan

    def get_high_vmt_prop(row):
        age = min(row["age"], max_table_age)
        if age in vmt_lookup.index:
            return vmt_lookup.loc[age, "high_VMT_prop"]
        return np.nan

    result["vmt"] = result.apply(get_vmt, axis=1)
    result["high_VMT_prop"] = result.apply(get_high_vmt_prop, axis=1)

    return result


def compute_fleet_composition(fleet: pd.DataFrame) -> dict:
    """Compute a summary snapshot of fleet composition.

    Returns dict with:
        total_vehicles, by_powertrain, age_distribution, total_vmt
    """
    return {
        "total_vehicles": fleet["n"].sum(),
        "by_powertrain": fleet.groupby("powertrain")["n"].sum().to_dict(),
        "age_distribution": fleet.groupby("age")["n"].sum().to_dict(),
        "total_vmt": (fleet["n"] * fleet["vmt"]).sum(),
    }


def reshuffle_used_market(
    fleet: pd.DataFrame, reshuffle_prob: float = DEFAULT_RESHUFFLE_PROB
) -> pd.DataFrame:
    """Simulate used car market dynamics by reshuffling vehicles between VMT buckets.

    Moves a fraction of vehicles between high/low VMT buckets within each
    age x powertrain group. Total fleet size is conserved.

    Args:
        fleet: Fleet DataFrame.
        reshuffle_prob: Fraction of fleet eligible for redistribution (default 15%).

    Returns:
        Fleet with adjusted n values across VMT buckets.
    """
    result = fleet.copy()

    for (age, pt), group in result.groupby(["age", "powertrain"]):
        high_mask = (result["age"] == age) & (result["powertrain"] == pt) & (result["vmt_bucket"] == "high")
        low_mask = (result["age"] == age) & (result["powertrain"] == pt) & (result["vmt_bucket"] == "low")

        n_high = result.loc[high_mask, "n"].values
        n_low = result.loc[low_mask, "n"].values

        if len(n_high) == 0 or len(n_low) == 0:
            continue

        n_high = n_high[0]
        n_low = n_low[0]

        if np.isnan(n_high) or np.isnan(n_low):
            continue

        # Move vehicles toward equilibrium: each bucket moves toward the mean
        delta = reshuffle_prob * 0.5 * (n_high - n_low)
        result.loc[high_mask, "n"] = n_high - delta
        result.loc[low_mask, "n"] = n_low + delta

    return result


def validate_survival_curves(survival_curves: pd.DataFrame) -> None:
    """Validate survival curve data: bounds 0-1, monotonically non-increasing."""
    if not survival_curves["survival"].between(0, 1).all():
        bad = survival_curves[~survival_curves["survival"].between(0, 1)]
        raise ValueError(
            f"Survival probabilities must be between 0 and 1. "
            f"Invalid values at ages: {bad['age'].tolist()}"
        )

    if not survival_curves["lag1_scrappage"].between(0, 1).all():
        bad = survival_curves[~survival_curves["lag1_scrappage"].between(0, 1)]
        raise ValueError(
            f"Scrappage rates must be between 0 and 1. "
            f"Invalid values at ages: {bad['age'].tolist()}"
        )

    # Check monotonicity of survival (should be non-increasing)
    sorted_surv = survival_curves.sort_values("age")
    survival_vals = sorted_surv["survival"].values
    for i in range(1, len(survival_vals)):
        if survival_vals[i] > survival_vals[i - 1]:
            raise ValueError(
                f"Survival curve is not monotonically non-increasing: "
                f"survival increases from age {sorted_surv['age'].iloc[i-1]} "
                f"to age {sorted_surv['age'].iloc[i]}"
            )


def validate_vmt_table(vmt_table: pd.DataFrame) -> None:
    """Validate VMT table: positive values, complete age range."""
    for col in ["low", "high", "vmt"]:
        if col in vmt_table.columns:
            if (vmt_table[col] <= 0).any():
                bad = vmt_table[vmt_table[col] <= 0]
                raise ValueError(
                    f"VMT column '{col}' contains non-positive values "
                    f"at ages: {bad['age'].tolist()}"
                )


def validate_powertrain_proportions(proportions: dict[str, float]) -> None:
    """Validate powertrain proportions sum to ~1.0."""
    total = sum(proportions.values())
    if not (0.999 <= total <= 1.001):
        raise ValueError(
            f"Powertrain proportions must sum to 1.0 (got {total:.6f})"
        )


def step_fleet_one_year(
    fleet: pd.DataFrame,
    survival_curves: pd.DataFrame,
    vmt_table: pd.DataFrame,
    powertrain_proportions: dict[str, float],
    renewal_rate: float = DEFAULT_RENEWAL_RATE,
    reshuffle_prob: float = DEFAULT_RESHUFFLE_PROB,
    new_vehicle_attrs: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Execute one full year of fleet dynamics.

    Order: age -> scrap -> add new -> assign VMT -> reshuffle used market

    Returns:
        Tuple of (updated fleet, scrapped vehicles, composition snapshot).
    """
    # Extract new vehicle attributes from current age-0 before aging
    if new_vehicle_attrs is None:
        age0 = fleet[fleet["age"] == 0]
        if len(age0) > 0:
            # Get one representative row per powertrain (average across VMT buckets)
            attr_cols = ["powertrain", "mpg", "mpge", "batt_kwh"]
            attr_cols = [c for c in attr_cols if c in age0.columns]
            if "ev_range" in age0.columns:
                attr_cols.append("ev_range")
            new_vehicle_attrs = age0[attr_cols].groupby("powertrain").first().reset_index()

    # 1. Age all vehicles
    fleet = age_fleet(fleet)

    # 2. Apply scrappage
    fleet, scrapped = apply_scrappage(fleet, survival_curves)

    # 3. Add new vehicles
    fleet = add_new_vehicles(
        fleet, powertrain_proportions, renewal_rate, new_vehicle_attrs
    )

    # 4. Assign VMT by age
    fleet = assign_vmt_by_age(fleet, vmt_table)

    # 5. Reshuffle used car market
    fleet = reshuffle_used_market(fleet, reshuffle_prob)

    # 6. Compute composition snapshot
    composition = compute_fleet_composition(fleet)

    return fleet, scrapped, composition
