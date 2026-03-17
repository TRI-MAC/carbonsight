"""Pydantic models for emissions factors and macro-driver trajectories."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EmissionsFactors(BaseModel):
    """Component-level production, usage, and disposal emission factors."""

    # Production (kg CO2)
    production_body: float = Field(default=4200, description="Body manufacturing emissions (kg CO2)")
    production_body_low: float = Field(default=3500)
    production_body_high: float = Field(default=5000)

    production_ice: float = Field(default=1400, description="ICE powertrain manufacturing (kg CO2)")
    production_ice_low: float = Field(default=1000)
    production_ice_high: float = Field(default=1800)

    production_battery_per_kwh: float = Field(default=100, description="Battery manufacturing (kg CO2/kWh)")
    production_battery_per_kwh_low: float = Field(default=30)
    production_battery_per_kwh_high: float = Field(default=200)

    # Usage
    gas_ghg_per_gallon: float = Field(default=8.89, description="Gasoline GHG intensity (kg CO2/gallon)")
    grid_ghg_per_kwh: float = Field(default=0.369, description="Grid carbon intensity (kg CO2/kWh)")

    # Disposal (kg CO2)
    disposal_per_vehicle: float = Field(default=2800, description="End-of-life recycling emissions (kg CO2)")
    disposal_per_vehicle_low: float = Field(default=2000)
    disposal_per_vehicle_high: float = Field(default=3500)


class EnergyPriceTrajectory(BaseModel):
    """10-year price trajectory for an energy source."""

    name: str
    unit: str
    values: list[float] = Field(description="One value per simulation year")
    source: str = ""
    scenario: str = "reference"  # reference, high, low


class MacroDriverDefaults(BaseModel):
    """Default macro-economic driver parameters."""

    oil_price_per_barrel: EnergyPriceTrajectory = Field(
        default_factory=lambda: EnergyPriceTrajectory(
            name="Oil Price",
            unit="$/barrel",
            # EIA AEO 2024 Reference case: gradual increase 2024-2033
            values=[75.0, 77.0, 79.5, 82.0, 84.5, 87.0, 89.5, 92.0, 94.0, 96.0],
            source="EIA AEO 2024 Reference",
            scenario="reference",
        )
    )
    electricity_price_per_kwh: EnergyPriceTrajectory = Field(
        default_factory=lambda: EnergyPriceTrajectory(
            name="Electricity Price",
            unit="$/kWh",
            # EIA AEO 2024 Reference case: slight decline as renewables grow
            values=[0.130, 0.129, 0.127, 0.126, 0.124, 0.123, 0.121, 0.120, 0.118, 0.117],
            source="EIA AEO 2024 Reference",
            scenario="reference",
        )
    )
    # Elasticities
    vmt_oil_price_elasticity: float = Field(
        default=-0.2, description="Short-run VMT elasticity w.r.t. fuel price"
    )
    powertrain_pref_oil_elasticity: float = Field(
        default=0.1, description="EV preference elasticity w.r.t. oil price"
    )
    ev_elec_price_elasticity: float = Field(
        default=-0.05, description="EV preference elasticity w.r.t. electricity price"
    )
