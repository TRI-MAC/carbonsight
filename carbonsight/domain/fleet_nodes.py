"""DAG node registration for fleet dynamics compute functions.

Registers fleet dynamics operations as nodes in the CarbonSight simulation graph,
enabling them to participate in the DAG-based execution engine.
"""

from __future__ import annotations

import pandas as pd

from carbonsight.core.node import Assumption, DataSource, Node, NodeType
from carbonsight.domain.fleet_dynamics import (
    DEFAULT_ANNUAL_SALES_VOLUME,
    add_new_vehicles,
    age_fleet,
    apply_scrappage,
    assign_vmt_by_age,
    compute_fleet_composition,
    reshuffle_used_market,
)


def compute_aged_fleet(prev_post_used_market: pd.DataFrame) -> pd.DataFrame:
    """DAG compute: age all vehicles by 1 year (uses prior year's final fleet)."""
    return age_fleet(prev_post_used_market)


def compute_post_scrappage(
    aged_fleet: pd.DataFrame, survival_curves: pd.DataFrame
) -> pd.DataFrame:
    """DAG compute: apply scrappage, return surviving fleet."""
    surviving, _ = apply_scrappage(aged_fleet, survival_curves)
    return surviving


def compute_scrapped_vehicles(
    aged_fleet: pd.DataFrame, survival_curves: pd.DataFrame
) -> pd.DataFrame:
    """DAG compute: apply scrappage, return scrapped vehicles."""
    _, scrapped = apply_scrappage(aged_fleet, survival_curves)
    return scrapped


def compute_post_new_entry(
    post_scrappage: pd.DataFrame,
    powertrain_proportions: dict,
    annual_sales_volume: float,
    sales_growth_rate: float,
    year_index: int,
) -> pd.DataFrame:
    """DAG compute: add new vehicles to the fleet."""
    n_new = annual_sales_volume * (1 + sales_growth_rate) ** year_index
    return add_new_vehicles(post_scrappage, powertrain_proportions, n_new)


def compute_post_vmt_assignment(
    post_new_entry: pd.DataFrame, vmt_by_age: pd.DataFrame
) -> pd.DataFrame:
    """DAG compute: assign VMT based on age and bucket."""
    return assign_vmt_by_age(post_new_entry, vmt_by_age)


def compute_post_used_market(
    post_vmt_assignment: pd.DataFrame, reshuffle_probability: float
) -> pd.DataFrame:
    """DAG compute: reshuffle used car market."""
    return reshuffle_used_market(post_vmt_assignment, reshuffle_probability)


def compute_post_used_market_adjusted(
    adjusted_vmt: pd.DataFrame, reshuffle_probability: float
) -> pd.DataFrame:
    """DAG compute: reshuffle used car market (reads from adjusted VMT)."""
    return reshuffle_used_market(adjusted_vmt, reshuffle_probability)


def compute_adjusted_new_entry(
    post_scrappage: pd.DataFrame,
    powertrain_proportions: dict,
    annual_sales_volume: float,
    sales_growth_rate: float,
    year_index: int,
    powertrain_preference_shift: float,
) -> pd.DataFrame:
    """DAG compute: add new vehicles with macro-adjusted powertrain mix.

    Shifts BEV proportion by the preference factor (>1 = more BEV),
    redistributes ICEV share to compensate, and normalizes to sum=1.0.
    """
    adjusted = dict(powertrain_proportions)
    if powertrain_preference_shift != 1.0 and "bev" in adjusted:
        old_bev = adjusted["bev"]
        new_bev = min(old_bev * powertrain_preference_shift, 0.95)
        delta = new_bev - old_bev
        # Take delta from ICEV share
        if "icev" in adjusted and adjusted["icev"] - delta > 0.01:
            adjusted["icev"] -= delta
            adjusted["bev"] = new_bev
        # Normalize to sum=1.0
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
    n_new = annual_sales_volume * (1 + sales_growth_rate) ** year_index
    return add_new_vehicles(post_scrappage, adjusted, n_new)


def compute_adjusted_vmt(
    post_vmt_assignment: pd.DataFrame,
    vmt_adjustment: float,
) -> pd.DataFrame:
    """DAG compute: scale fleet VMT by macro-economic adjustment factor."""
    if vmt_adjustment == 1.0:
        return post_vmt_assignment
    result = post_vmt_assignment.copy()
    if "vmt" in result.columns:
        result["vmt"] = result["vmt"] * vmt_adjustment
    return result


def compute_fleet_snapshot(post_used_market: pd.DataFrame) -> dict:
    """DAG compute: produce annual fleet composition snapshot."""
    return compute_fleet_composition(post_used_market)


def create_fleet_dynamics_nodes(
    fleet_inventory: pd.DataFrame,
    survival_curves: pd.DataFrame,
    vmt_by_age: pd.DataFrame,
    powertrain_proportions: dict[str, float] | None = None,
    annual_sales_volume: float = DEFAULT_ANNUAL_SALES_VOLUME,
    sales_growth_rate: float = 0.0,
    reshuffle_probability: float = 0.15,
) -> list[Node]:
    """Create all fleet dynamics DAG nodes.

    Args:
        fleet_inventory: Initial fleet DataFrame.
        survival_curves: Survival curve DataFrame.
        vmt_by_age: VMT-by-age DataFrame.
        powertrain_proportions: New vehicle powertrain mix.
        annual_sales_volume: New vehicles sold per year (absolute count).
        sales_growth_rate: Annual compound growth rate for sales volume.
        reshuffle_probability: Used car market reshuffle fraction.

    Returns:
        List of Node objects ready for graph registration.
    """
    if powertrain_proportions is None:
        powertrain_proportions = {"icev": 0.82, "hev": 0.09, "phev": 0.02, "bev": 0.07}

    nodes = [
        # Input nodes
        Node(
            name="fleet_inventory",
            node_type=NodeType.DATAFRAME,
            value=fleet_inventory,
            initial_value=fleet_inventory,
            data_source=DataSource(
                name="Fleet Inventory",
                publication_date="2024",
                url="current_veh_t0_VMT.csv",
                transformations="Loaded from Ekiden v1 format",
            ),
            tags=["fleet", "input"],
        ),
        Node(
            name="survival_curves",
            node_type=NodeType.DATAFRAME,
            value=survival_curves,
            data_source=DataSource(
                name="Greene & Leard Survival Model",
                publication_date="2024",
                url="averaged_survival_v2.csv",
            ),
            tags=["fleet", "input"],
        ),
        Node(
            name="vmt_by_age",
            node_type=NodeType.DATAFRAME,
            value=vmt_by_age,
            data_source=DataSource(
                name="NHTS 2017",
                url="vmt_by_age.csv",
            ),
            tags=["fleet", "input"],
        ),
        Node(
            name="powertrain_proportions",
            node_type=NodeType.SCALAR,
            value=powertrain_proportions,
            tags=["fleet", "input", "adjustable"],
        ),
        Node(
            name="annual_sales_volume",
            node_type=NodeType.SCALAR,
            value=annual_sales_volume,
            assumptions=[
                Assumption(
                    description="15.5M new vehicles sold per year",
                    rationale="2019-2024 US average (~15.3M); exogenous to fleet size",
                    confidence="medium",
                )
            ],
            tags=["fleet", "input", "adjustable"],
        ),
        Node(
            name="sales_growth_rate",
            node_type=NodeType.SCALAR,
            value=sales_growth_rate,
            assumptions=[
                Assumption(
                    description="0% annual sales growth rate (default)",
                    rationale="Neutral baseline; 0.3-0.5% matches historical trends",
                    confidence="medium",
                )
            ],
            tags=["fleet", "input", "adjustable"],
        ),
        Node(
            name="reshuffle_probability",
            node_type=NodeType.SCALAR,
            value=reshuffle_probability,
            assumptions=[
                Assumption(
                    description="15% of fleet eligible for used market reshuffling",
                    rationale="Used vehicle market is ~3x new vehicle market, reaching ~15% of stock",
                    confidence="medium",
                )
            ],
            tags=["fleet", "input", "adjustable"],
        ),
        Node(
            name="year_index",
            node_type=NodeType.SCALAR,
            value=0,
            tags=["fleet", "input"],
        ),
        # Compute nodes
        Node(
            name="aged_fleet",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_aged_fleet,
            tags=["fleet", "process"],
        ),
        Node(
            name="post_scrappage",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_post_scrappage,
            tags=["fleet", "process"],
        ),
        Node(
            name="scrapped_vehicles",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_scrapped_vehicles,
            tags=["fleet", "process"],
        ),
        Node(
            name="post_new_entry",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_adjusted_new_entry,
            tags=["fleet", "process"],
        ),
        Node(
            name="post_vmt_assignment",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_post_vmt_assignment,
            tags=["fleet", "process"],
        ),
        Node(
            name="adjusted_vmt",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_adjusted_vmt,
            tags=["fleet", "process"],
        ),
        Node(
            name="post_used_market",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_post_used_market_adjusted,
            initial_value=fleet_inventory,
            tags=["fleet", "process"],
        ),
        Node(
            name="fleet_snapshot",
            node_type=NodeType.SCALAR,
            compute_fn=compute_fleet_snapshot,
            tags=["fleet", "output"],
        ),
    ]
    return nodes
