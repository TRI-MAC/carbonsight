"""Macro-economic driver system for CarbonSight.

Implements oil price, electricity price, and consumer preference trajectories
with elasticity-based causal propagation to downstream nodes (VMT, powertrain mix).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from carbonsight.core.distributions import Distribution
from carbonsight.core.node import Assumption, DataSource, Node, NodeType
from carbonsight.data.models import EnergyPriceTrajectory, MacroDriverDefaults


@dataclass
class ElasticityLink:
    """A causal link between a driver and a downstream variable."""

    driver_node: str
    target_node: str
    elasticity: float
    description: str = ""
    source: str = ""


# Default elasticity values from literature
DEFAULT_ELASTICITIES = [
    ElasticityLink(
        driver_node="oil_price",
        target_node="vmt_adjustment",
        elasticity=-0.2,
        description="Short-run VMT elasticity w.r.t. fuel price",
        source="energy.gov FOTW 1313",
    ),
    ElasticityLink(
        driver_node="oil_price",
        target_node="powertrain_preference_shift",
        elasticity=0.1,
        description="EV preference elasticity w.r.t. oil price",
        source="Literature consensus",
    ),
    ElasticityLink(
        driver_node="electricity_price",
        target_node="powertrain_preference_shift",
        elasticity=-0.05,
        description="EV preference elasticity w.r.t. electricity price",
        source="Estimated",
    ),
]


def apply_elasticity(
    baseline_value: float,
    driver_baseline: float,
    driver_current: float,
    elasticity: float,
) -> float:
    """Apply elasticity to compute adjusted value.

    Returns: baseline_value * (1 + elasticity * (driver_current - driver_baseline) / driver_baseline)
    """
    if driver_baseline == 0:
        return baseline_value
    pct_change = (driver_current - driver_baseline) / driver_baseline
    return baseline_value * (1 + elasticity * pct_change)


def compute_vmt_adjustment(
    oil_price: float,
    baseline_oil_price: float = 75.0,
    elasticity: float = -0.2,
) -> float:
    """Compute VMT adjustment factor based on oil price change.

    Returns a multiplier (e.g., 0.96 means 4% VMT reduction).
    """
    return apply_elasticity(1.0, baseline_oil_price, oil_price, elasticity)


def compute_powertrain_preference_shift(
    oil_price: float,
    baseline_oil_price: float = 75.0,
    elasticity: float = 0.1,
) -> float:
    """Compute EV preference shift based on oil price.

    Returns a multiplier for BEV proportion (>1 means higher BEV share).
    """
    return apply_elasticity(1.0, baseline_oil_price, oil_price, elasticity)


def get_year_value(trajectory: EnergyPriceTrajectory, year_index: int) -> float:
    """Get the value for a specific year from a trajectory.

    Clamps to the last available value if year_index exceeds trajectory length.
    """
    if year_index < 0:
        return trajectory.values[0]
    if year_index >= len(trajectory.values):
        return trajectory.values[-1]
    return trajectory.values[year_index]


def get_causal_links() -> list[ElasticityLink]:
    """Return all documented causal links between macro drivers and downstream nodes."""
    return list(DEFAULT_ELASTICITIES)


def query_causal_links(
    driver: str | None = None, target: str | None = None
) -> list[ElasticityLink]:
    """Query which drivers affect which nodes (or vice versa)."""
    links = DEFAULT_ELASTICITIES
    if driver:
        links = [l for l in links if l.driver_node == driver]
    if target:
        links = [l for l in links if l.target_node == target]
    return links


# --- DAG node compute functions ---

def compute_oil_price_node(oil_price_trajectory: list, year_index: int) -> float:
    """Extract current year's oil price from trajectory."""
    idx = min(year_index, len(oil_price_trajectory) - 1)
    return oil_price_trajectory[max(0, idx)]


def compute_electricity_price_node(
    electricity_price_trajectory: list, year_index: int
) -> float:
    """Extract current year's electricity price from trajectory."""
    idx = min(year_index, len(electricity_price_trajectory) - 1)
    return electricity_price_trajectory[max(0, idx)]


def compute_vmt_adjustment_node(
    oil_price: float, vmt_oil_price_elasticity: float
) -> float:
    """DAG compute: VMT adjustment from oil price."""
    return compute_vmt_adjustment(oil_price, elasticity=vmt_oil_price_elasticity)


def compute_pt_pref_shift_node(
    oil_price: float,
    powertrain_pref_oil_elasticity: float,
    electricity_price: float,
    ev_elec_price_elasticity: float,
) -> float:
    """DAG compute: powertrain preference shift from oil and electricity prices."""
    oil_effect = compute_powertrain_preference_shift(
        oil_price, elasticity=powertrain_pref_oil_elasticity
    )
    baseline_elec_price = 0.130  # $/kWh, first value in default EIA AEO trajectory
    elec_effect = apply_elasticity(1.0, baseline_elec_price, electricity_price, ev_elec_price_elasticity)
    return oil_effect * elec_effect


def create_macro_driver_nodes(
    defaults: MacroDriverDefaults | None = None,
) -> list[Node]:
    """Create all macro-economic driver DAG nodes."""
    if defaults is None:
        defaults = MacroDriverDefaults()

    return [
        # Trajectory input nodes
        Node(
            name="oil_price_trajectory",
            node_type=NodeType.TIMESERIES,
            value=defaults.oil_price_per_barrel.values,
            display_name="Oil Price Trajectory",
            description="Projected crude oil price per barrel over the simulation horizon. EIA Annual Energy Outlook 2024, Reference Case.",
            data_source=DataSource(
                name="EIA Annual Energy Outlook 2024, Table 12",
                publication_date="2024-03",
                url="https://www.eia.gov/outlooks/aeo/data/browser/#/?id=12-AEO2024",
            ),
            tags=["macro", "input"],
        ),
        Node(
            name="electricity_price_trajectory",
            node_type=NodeType.TIMESERIES,
            value=defaults.electricity_price_per_kwh.values,
            display_name="Electricity Price Trajectory",
            description="Projected residential electricity price per kWh. EIA Annual Energy Outlook 2024, Reference Case.",
            data_source=DataSource(
                name="EIA Annual Energy Outlook 2024, Table 8",
                publication_date="2024-03",
                url="https://www.eia.gov/outlooks/aeo/data/browser/#/?id=8-AEO2024",
            ),
            tags=["macro", "input"],
        ),
        # Year index (set per year during simulation)
        Node(
            name="year_index",
            node_type=NodeType.SCALAR,
            value=0,
            display_name="Simulation Year",
            description="Current year offset from simulation start (0 = base year).",
            tags=["macro", "input"],
        ),
        # Elasticity parameters
        Node(
            name="vmt_oil_price_elasticity",
            node_type=NodeType.DISTRIBUTION,
            value=Distribution.normal(mean=defaults.vmt_oil_price_elasticity, std=0.05),
            display_name="VMT-Oil Price Elasticity",
            description="Short-run elasticity of driving distance with respect to fuel price (~-0.2). Normal(-0.2, 0.05).",
            data_source=DataSource(
                name="Hymel, K., Small, K. & Van Dender, K. (2010). Induced demand and rebound effects in road transport. Transportation Research Part B, 44(10), 1220-1241.",
                publication_date="2010",
                url="https://doi.org/10.1016/j.trb.2010.02.007",
            ),
            assumptions=[
                Assumption(
                    description="Short-run VMT elasticity w.r.t. fuel price = -0.2",
                    rationale="Hymel et al. meta-analysis: short-run range -0.1 to -0.3; also consistent with DOE FOTW #1313",
                    confidence="medium",
                )
            ],
            tags=["macro", "input", "adjustable"],
        ),
        Node(
            name="powertrain_pref_oil_elasticity",
            node_type=NodeType.SCALAR,
            value=defaults.powertrain_pref_oil_elasticity,
            display_name="EV Preference-Oil Elasticity",
            description="Elasticity of BEV purchase preference with respect to oil price (~0.1). Higher oil prices increase EV adoption.",
            data_source=DataSource(
                name="Li, S., Tong, L., Xing, J. & Zhou, Y. (2017). The Market for Electric Vehicles. American Economic Review, 107(10), 2962-3000.",
                publication_date="2017",
                url="https://doi.org/10.1257/aer.20161492",
            ),
            assumptions=[
                Assumption(
                    description="EV preference oil-price elasticity ~0.1",
                    rationale="Li et al. estimate cross-price elasticity of EV demand w.r.t. gasoline price; range 0.05-0.15",
                    confidence="medium",
                )
            ],
            tags=["macro", "input", "adjustable"],
        ),
        Node(
            name="ev_elec_price_elasticity",
            node_type=NodeType.SCALAR,
            value=defaults.ev_elec_price_elasticity,
            display_name="EV Electricity Price Elasticity",
            description="Elasticity of BEV purchase preference with respect to electricity price (~-0.05). Higher electricity prices dampen EV adoption.",
            data_source=DataSource(
                name="Li, S., Tong, L., Xing, J. & Zhou, Y. (2017). The Market for Electric Vehicles. American Economic Review, 107(10), 2962-3000.",
                publication_date="2017",
                url="https://doi.org/10.1257/aer.20161492",
            ),
            assumptions=[
                Assumption(
                    description="EV electricity-price elasticity ~-0.05",
                    rationale="Estimated from Li et al. operating cost sensitivity; less studied than fuel price effects",
                    confidence="low",
                )
            ],
            tags=["macro", "input", "adjustable"],
        ),
        # Computed driver values
        Node(
            name="oil_price",
            node_type=NodeType.SCALAR,
            compute_fn=compute_oil_price_node,
            display_name="Oil Price",
            description="Current year's oil price, extracted from **Oil Price Trajectory** using **Simulation Year**.",
            tags=["macro", "process"],
        ),
        Node(
            name="electricity_price",
            node_type=NodeType.SCALAR,
            compute_fn=compute_electricity_price_node,
            display_name="Electricity Price",
            description="Current year's electricity price, extracted from **Electricity Price Trajectory** using **Simulation Year**.",
            tags=["macro", "process"],
        ),
        # Elasticity-derived adjustments
        Node(
            name="vmt_adjustment",
            node_type=NodeType.SCALAR,
            compute_fn=compute_vmt_adjustment_node,
            display_name="Driving Distance Adjustment",
            description="Multiplier on fleet mileage based on oil price changes. Applies **VMT-Oil Price Elasticity** to **Oil Price** (e.g., 0.96 = 4% reduction).",
            tags=["macro", "process"],
        ),
        Node(
            name="powertrain_preference_shift",
            node_type=NodeType.SCALAR,
            compute_fn=compute_pt_pref_shift_node,
            display_name="EV Preference Shift",
            description="Multiplier on BEV share of new sales based on energy price changes. Combines **Oil Price** (via **EV Preference-Oil Elasticity**) and **Electricity Price** (via **EV Electricity Price Elasticity**). >1 = more EVs.",
            tags=["macro", "process"],
        ),
    ]
