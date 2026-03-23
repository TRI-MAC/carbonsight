"""DAG node registration for fleet dynamics compute functions.

Registers fleet dynamics operations as nodes in the CarbonSight simulation graph,
enabling them to participate in the DAG-based execution engine.
"""

from __future__ import annotations

import pandas as pd

from carbonsight.core.distributions import Distribution
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
    new_vehicle_attrs: pd.DataFrame,
) -> pd.DataFrame:
    """DAG compute: add new vehicles to the fleet."""
    n_new = annual_sales_volume * (1 + sales_growth_rate) ** year_index
    return add_new_vehicles(post_scrappage, powertrain_proportions, n_new, new_vehicle_attrs)


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
    new_vehicle_attrs: pd.DataFrame,
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
    return add_new_vehicles(post_scrappage, adjusted, n_new, new_vehicle_attrs)


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

    # Extract age-0 vehicle attributes (mpg, mpge, batt_kwh) before aging
    # so new vehicles each year inherit representative powertrain characteristics
    age0 = fleet_inventory[fleet_inventory["age"] == 0]
    attr_cols = ["powertrain", "mpg", "mpge", "batt_kwh"]
    attr_cols = [c for c in attr_cols if c in age0.columns]
    if "ev_range" in age0.columns:
        attr_cols.append("ev_range")
    new_vehicle_attrs = age0[attr_cols].groupby("powertrain").first().reset_index()

    nodes = [
        # Input nodes
        Node(
            name="survival_curves",
            node_type=NodeType.DATAFRAME,
            value=survival_curves,
            display_name="Survival Curves",
            description="Age-based probability of a vehicle remaining in service. Weibull parameters from Greene & Leard (2015) survival model.",
            data_source=DataSource(
                name="Lu, S. (2006). Vehicle Survivability and Travel Mileage Schedules. NHTSA DOT HS 809 952.",
                publication_date="2006-01",
                url="https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/809952",
            ),
            tags=["fleet", "input"],
        ),
        Node(
            name="vmt_by_age",
            node_type=NodeType.DATAFRAME,
            value=vmt_by_age,
            display_name="Mileage by Age",
            description="Annual miles driven as a function of vehicle age. From the 2017 National Household Travel Survey.",
            data_source=DataSource(
                name="FHWA National Household Travel Survey (2017)",
                publication_date="2017",
                url="https://nhts.ornl.gov/",
            ),
            tags=["fleet", "input"],
        ),
        Node(
            name="powertrain_proportions",
            node_type=NodeType.SCALAR,
            value=powertrain_proportions,
            display_name="New Vehicle Powertrain Mix",
            description="Share of new vehicle sales by powertrain type (ICEV, HEV, PHEV, BEV). From EPA Automotive Trends Report Table 3.",
            data_source=DataSource(
                name="EPA Automotive Trends Report (2024)",
                publication_date="2024-12",
                url="https://www.epa.gov/automotive-trends",
            ),
            tags=["fleet", "input", "adjustable"],
        ),
        Node(
            name="annual_sales_volume",
            node_type=NodeType.DISTRIBUTION,
            value=Distribution.normal(mean=annual_sales_volume, std=1_000_000),
            display_name="Annual New Vehicle Sales",
            description="Total new vehicles sold per year (~15.5M default). Normal(15.5M, 1M).",
            data_source=DataSource(
                name="Bureau of Economic Analysis, Table 7.2.5S (2024)",
                publication_date="2024",
                url="https://www.bea.gov/data/consumer-spending/main",
            ),
            assumptions=[
                Assumption(
                    description="15.5M new vehicles sold per year",
                    rationale="2019-2024 US average (~15.3M); std ~1M reflects macroeconomic cycle uncertainty",
                    confidence="medium",
                )
            ],
            tags=["fleet", "input", "adjustable"],
        ),
        Node(
            name="sales_growth_rate",
            node_type=NodeType.SCALAR,
            value=sales_growth_rate,
            display_name="Sales Growth Rate",
            description="Annual compound growth rate applied to new vehicle sales volume.",
            assumptions=[
                Assumption(
                    description="0% annual sales growth rate (default)",
                    rationale="Neutral baseline; 0.3-0.5% matches historical trends per BEA data",
                    confidence="medium",
                )
            ],
            tags=["fleet", "input", "adjustable"],
        ),
        Node(
            name="reshuffle_probability",
            node_type=NodeType.SCALAR,
            value=reshuffle_probability,
            display_name="Used Market Reshuffle Rate",
            description="Fraction of fleet eligible for used car market redistribution each year (~15%).",
            data_source=DataSource(
                name="Manheim Used Vehicle Value Index (2024)",
                publication_date="2024",
                url="https://publish.manheim.com/en/services/consulting/used-vehicle-value-index.html",
            ),
            assumptions=[
                Assumption(
                    description="15% of fleet eligible for used market reshuffling",
                    rationale="Used vehicle market is ~3x new vehicle market (~40M transactions/yr for ~280M fleet)",
                    confidence="medium",
                )
            ],
            tags=["fleet", "input", "adjustable"],
        ),
        Node(
            name="new_vehicle_attrs",
            node_type=NodeType.DATAFRAME,
            value=new_vehicle_attrs,
            display_name="New Vehicle Characteristics",
            description="Fuel efficiency (MPG/MPGe) and battery size for new vehicles by powertrain. Extracted from age-0 cohort of EPA fleet inventory.",
            data_source=DataSource(
                name="EPA Automotive Trends Report, Table 3 (2024)",
                publication_date="2024-12",
                url="https://www.epa.gov/automotive-trends/explore-automotive-trends-data",
            ),
            tags=["fleet", "input"],
        ),
        Node(
            name="year_index",
            node_type=NodeType.SCALAR,
            value=0,
            display_name="Simulation Year",
            description="Current year offset from simulation start (0 = base year).",
            tags=["fleet", "input"],
        ),
        # Compute nodes
        Node(
            name="aged_fleet",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_aged_fleet,
            display_name="Aged Fleet",
            description="All vehicles aged by one year. Reads prior year's **Final Fleet** and increments each vehicle's age.",
            tags=["fleet", "process"],
        ),
        Node(
            name="post_scrappage",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_post_scrappage,
            display_name="Surviving Fleet",
            description="Vehicles remaining after age-based retirement. Applies **Survival Curves** to the **Aged Fleet** to probabilistically remove end-of-life vehicles.",
            tags=["fleet", "process"],
        ),
        Node(
            name="scrapped_vehicles",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_scrapped_vehicles,
            display_name="Retired Vehicles",
            description="Vehicles removed from service this year. The complement of **Surviving Fleet** — same scrappage calculation, opposite output.",
            tags=["fleet", "process"],
        ),
        Node(
            name="post_new_entry",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_adjusted_new_entry,
            display_name="Fleet With New Sales",
            description="Fleet after adding this year's new vehicles. Combines **Surviving Fleet** with new vehicles based on **New Vehicle Powertrain Mix**, **Annual New Vehicle Sales**, and **New Vehicle Characteristics**.",
            tags=["fleet", "process"],
        ),
        Node(
            name="post_vmt_assignment",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_post_vmt_assignment,
            display_name="Fleet With Mileage",
            description="Fleet after assigning annual driving distances. Applies **Mileage by Age** schedules to **Fleet With New Sales**.",
            tags=["fleet", "process"],
        ),
        Node(
            name="adjusted_vmt",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_adjusted_vmt,
            display_name="Mileage-Adjusted Fleet",
            description="Fleet with macro-economically adjusted driving distances. Scales mileage from **Fleet With Mileage** by an economic adjustment factor.",
            tags=["fleet", "process"],
        ),
        Node(
            name="post_used_market",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_post_used_market_adjusted,
            initial_value=fleet_inventory,
            display_name="Final Fleet",
            description="Year-end fleet after used car market reshuffling. Applies **Used Market Reshuffle Rate** to **Mileage-Adjusted Fleet** to redistribute vehicles across VMT buckets. Initialized from EPA fleet inventory data (~280M vehicles) at year 0.",
            tags=["fleet", "process"],
        ),
        Node(
            name="fleet_snapshot",
            node_type=NodeType.SCALAR,
            compute_fn=compute_fleet_snapshot,
            display_name="Fleet Composition",
            description="Annual summary of fleet size, powertrain shares, and average age. Computed from the **Final Fleet**.",
            tags=["fleet", "output"],
        ),
    ]
    return nodes
