"""DAG node registration for emissions model compute functions."""

from __future__ import annotations

import pandas as pd

from carbonsight.core.node import Assumption, Node, NodeType
from carbonsight.domain.emissions import (
    aggregate_emissions,
    compute_disposal_emissions,
    compute_production_emissions,
    compute_usage_emissions,
)


def compute_fleet_production_ghg(
    post_used_market: pd.DataFrame,
    production_body: float,
    production_ice: float,
    production_battery_per_kwh: float,
) -> pd.DataFrame:
    """DAG compute: production emissions for the fleet."""
    return compute_production_emissions(
        post_used_market, production_body, production_ice, production_battery_per_kwh
    )


def compute_fleet_usage_ghg(
    fleet_production_ghg: pd.DataFrame,
    gas_ghg_per_gallon: float,
    grid_ghg_per_kwh: float,
) -> pd.DataFrame:
    """DAG compute: usage emissions (gas + electric)."""
    return compute_usage_emissions(
        fleet_production_ghg, gas_ghg_per_gallon, grid_ghg_per_kwh
    )


def compute_scrapped_disposal_ghg(
    scrapped_vehicles: pd.DataFrame,
    disposal_per_vehicle: float,
) -> pd.DataFrame:
    """DAG compute: disposal emissions for scrapped vehicles."""
    return compute_disposal_emissions(scrapped_vehicles, disposal_per_vehicle)


def compute_total_emissions(
    fleet_usage_ghg: pd.DataFrame,
    scrapped_disposal_ghg: pd.DataFrame,
) -> dict:
    """DAG compute: aggregate all emissions for the year."""
    return aggregate_emissions(fleet_usage_ghg, scrapped_disposal_ghg)


def create_emissions_nodes(
    production_body: float = 4200.0,
    production_ice: float = 1400.0,
    production_battery_per_kwh: float = 100.0,
    gas_ghg_per_gallon: float = 8.89,
    grid_ghg_per_kwh: float = 0.369,
    disposal_per_vehicle: float = 2800.0,
) -> list[Node]:
    """Create all emissions model DAG nodes.

    These nodes depend on fleet dynamics nodes (post_used_market, scrapped_vehicles).
    """
    return [
        # Emission factor input nodes
        Node(
            name="production_body",
            node_type=NodeType.SCALAR,
            value=production_body,
            display_name="Body Manufacturing Emissions",
            description="CO2 emitted manufacturing a vehicle body (~4,200 kg).",
            assumptions=[
                Assumption(
                    description="Body manufacturing emissions ~4200 kg CO2",
                    rationale="Source: autoexpress.co.uk lifecycle analysis",
                    confidence="medium",
                )
            ],
            tags=["emissions", "input", "adjustable"],
        ),
        Node(
            name="production_ice",
            node_type=NodeType.SCALAR,
            value=production_ice,
            display_name="ICE Powertrain Emissions",
            description="Additional CO2 from manufacturing an internal combustion powertrain (~1,400 kg).",
            tags=["emissions", "input", "adjustable"],
        ),
        Node(
            name="production_battery_per_kwh",
            node_type=NodeType.SCALAR,
            value=production_battery_per_kwh,
            display_name="Battery Manufacturing Emissions",
            description="CO2 per kWh of battery capacity manufactured (~100 kg/kWh).",
            assumptions=[
                Assumption(
                    description="Battery manufacturing ~100 kg CO2/kWh",
                    rationale="McKinsey estimate; range 30-200 kg/kWh",
                    confidence="low",
                )
            ],
            tags=["emissions", "input", "adjustable"],
        ),
        Node(
            name="gas_ghg_per_gallon",
            node_type=NodeType.SCALAR,
            value=gas_ghg_per_gallon,
            display_name="Gasoline Carbon Intensity",
            description="CO2 emitted per gallon of gasoline burned (~8.89 kg/gal).",
            tags=["emissions", "input", "adjustable"],
        ),
        Node(
            name="grid_ghg_per_kwh",
            node_type=NodeType.SCALAR,
            value=grid_ghg_per_kwh,
            display_name="Grid Carbon Intensity",
            description="CO2 emitted per kWh of electricity from the grid (~0.369 kg/kWh).",
            tags=["emissions", "input", "adjustable"],
        ),
        Node(
            name="disposal_per_vehicle",
            node_type=NodeType.SCALAR,
            value=disposal_per_vehicle,
            display_name="End-of-Life Emissions per Vehicle",
            description="CO2 from scrapping and recycling one vehicle (~2,800 kg).",
            tags=["emissions", "input", "adjustable"],
        ),
        # Compute nodes
        Node(
            name="fleet_production_ghg",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_fleet_production_ghg,
            display_name="Manufacturing Emissions",
            description="Total emissions from producing this year's vehicles. Combines **Final Fleet** with **Body Manufacturing Emissions**, **ICE Powertrain Emissions**, and **Battery Manufacturing Emissions**.",
            tags=["emissions", "process"],
        ),
        Node(
            name="fleet_usage_ghg",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_fleet_usage_ghg,
            display_name="Driving Emissions",
            description="Emissions from all vehicles on the road this year. Applies **Gasoline Carbon Intensity** and **Grid Carbon Intensity** to mileage and fuel consumption from **Manufacturing Emissions**.",
            tags=["emissions", "process"],
        ),
        Node(
            name="scrapped_disposal_ghg",
            node_type=NodeType.DATAFRAME,
            compute_fn=compute_scrapped_disposal_ghg,
            display_name="End-of-Life Emissions",
            description="Emissions from vehicles leaving the fleet this year. Multiplies **Retired Vehicles** count by **End-of-Life Emissions per Vehicle**.",
            tags=["emissions", "process"],
        ),
        Node(
            name="total_emissions",
            node_type=NodeType.SCALAR,
            compute_fn=compute_total_emissions,
            display_name="Total Emissions",
            description="Sum of all lifecycle emissions for the year: **Manufacturing Emissions** + **Driving Emissions** + **End-of-Life Emissions**.",
            tags=["emissions", "output"],
        ),
    ]
