"""Counterfactual intervention system for CarbonSight.

Defines intervention types, application to scenarios via DAG node overrides,
multi-intervention combination with conflict detection, and scenario differencing.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class InterventionCategory(Enum):
    POLICY = "policy"
    TECHNOLOGY = "technology"
    BEHAVIORAL = "behavioral"
    GRID_ENERGY = "grid_energy"


VALID_CATEGORIES = {c.value for c in InterventionCategory}

# Application order for multi-intervention combinations
CATEGORY_ORDER = [
    InterventionCategory.POLICY,
    InterventionCategory.TECHNOLOGY,
    InterventionCategory.BEHAVIORAL,
    InterventionCategory.GRID_ENERGY,
]


@dataclass
class Intervention:
    """A counterfactual intervention that overrides DAG input nodes.

    Interventions do not modify graph topology — they only change node values.
    """

    name: str
    category: InterventionCategory
    description: str = ""
    overrides: dict[str, Any] = field(default_factory=dict)
    year_overrides: dict[int, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.category, str):
            if self.category not in VALID_CATEGORIES:
                raise ValueError(
                    f"Invalid intervention category '{self.category}'. "
                    f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
                )
            self.category = InterventionCategory(self.category)

    def get_overrides_for_year(self, year: int) -> dict[str, Any]:
        """Get the effective overrides for a specific simulation year.

        Year-specific overrides take precedence over static overrides.
        """
        result = dict(self.overrides)
        if year in self.year_overrides:
            result.update(self.year_overrides[year])
        return result


# --- Pre-built intervention factories ---

def carbon_pricing(price_per_tonne: float, start_year: int = 0) -> Intervention:
    """Create a carbon pricing policy intervention."""
    year_overrides = {}
    for y in range(start_year, start_year + 10):
        # Carbon price adds to effective gas cost
        # $50/tonne CO2 ≈ $0.44/gallon at 8.89 kg CO2/gallon
        added_per_gallon = price_per_tonne * 8.89 / 1000
        year_overrides[y] = {"gas_ghg_per_gallon": 8.89 + added_per_gallon * 0.05}
    return Intervention(
        name=f"carbon_pricing_{price_per_tonne}",
        category=InterventionCategory.POLICY,
        description=f"Carbon price of ${price_per_tonne}/tonne CO2 starting year {start_year}",
        year_overrides=year_overrides,
    )


def ev_subsidy(proportion_shift: dict[str, float]) -> Intervention:
    """Create an EV subsidy intervention that shifts powertrain proportions.

    proportion_shift can be either:
    - A full dict with all powertrains (used as-is)
    - A partial dict (e.g., {'bev': 0.15}) — merged with baseline proportions,
      with ICEV absorbing the difference to keep sum=1.0
    """
    all_pts = {"icev", "hev", "phev", "bev"}
    if all_pts.issubset(proportion_shift.keys()):
        proportions = proportion_shift
    else:
        baseline = {"icev": 0.82, "hev": 0.09, "phev": 0.02, "bev": 0.07}
        proportions = dict(baseline)
        for pt, target in proportion_shift.items():
            if pt in proportions:
                delta = target - proportions[pt]
                proportions[pt] = target
                if "icev" in proportions:
                    proportions["icev"] = max(0.01, proportions["icev"] - delta)
        total = sum(proportions.values())
        proportions = {k: v / total for k, v in proportions.items()}
    return Intervention(
        name="ev_subsidy",
        category=InterventionCategory.POLICY,
        description="EV purchase subsidy shifting powertrain mix",
        overrides={"powertrain_proportions": proportions},
    )


def vmt_reduction(factor: float) -> Intervention:
    """Create a VMT reduction behavioral intervention.

    factor: fraction of VMT remaining (e.g., 0.9 = 10% reduction).
    """
    return Intervention(
        name=f"vmt_reduction_{int((1-factor)*100)}pct",
        category=InterventionCategory.BEHAVIORAL,
        description=f"VMT reduced to {factor*100:.0f}% of baseline",
        overrides={"vmt_reduction_factor": factor},
    )


def grid_decarbonization(trajectory: dict[int, float]) -> Intervention:
    """Create a grid decarbonization intervention.

    trajectory: year -> grid_ghg_per_kwh values.
    """
    year_overrides = {int(y): {"grid_ghg_per_kwh": v} for y, v in trajectory.items()}
    return Intervention(
        name="grid_decarbonization",
        category=InterventionCategory.GRID_ENERGY,
        description="Grid carbon intensity trajectory override",
        year_overrides=year_overrides,
    )


def battery_cost_reduction(trajectory: dict[int, float]) -> Intervention:
    """Create a battery manufacturing decarbonization intervention.

    trajectory: year -> production_battery_per_kwh values.
    """
    year_overrides = {y: {"production_battery_per_kwh": v} for y, v in trajectory.items()}
    return Intervention(
        name="battery_decarb",
        category=InterventionCategory.TECHNOLOGY,
        description="Battery production emissions trajectory",
        year_overrides=year_overrides,
    )


def scrappage_program(
    age_threshold: int = 15,
    acceleration_factor: float = 2.0,
    duration_years: int = 3,
    start_year: int = 0,
) -> Intervention:
    """Create a scrappage/cash-for-clunkers program."""
    return Intervention(
        name="scrappage_program",
        category=InterventionCategory.POLICY,
        description=(
            f"Accelerated scrappage for vehicles >{age_threshold}yr, "
            f"{acceleration_factor}x rate for {duration_years} years"
        ),
        overrides={
            "scrappage_age_threshold": age_threshold,
            "scrappage_acceleration": acceleration_factor,
        },
        metadata={
            "start_year": start_year,
            "duration": duration_years,
        },
    )


def phev_charging_improvement(charging_factor: float = 0.85) -> Intervention:
    """Create a PHEV charging behavior intervention."""
    return Intervention(
        name=f"phev_charging_{int(charging_factor*100)}pct",
        category=InterventionCategory.BEHAVIORAL,
        description=f"PHEV charging factor increased to {charging_factor*100:.0f}%",
        overrides={"charging_factor": charging_factor},
    )


# --- Multi-intervention combination ---

def combine_interventions(
    interventions: list[Intervention],
) -> tuple[dict[str, Any], list[str]]:
    """Combine multiple interventions into a single override dict.

    Applies in category order. Warns on conflicts.

    Returns:
        Tuple of (combined overrides dict, list of warning messages).
    """
    sorted_interventions = sorted(
        interventions, key=lambda i: CATEGORY_ORDER.index(i.category)
    )

    combined: dict[str, Any] = {}
    warnings_list: list[str] = []
    override_sources: dict[str, str] = {}  # node_name -> intervention that set it

    for intervention in sorted_interventions:
        for node_name, value in intervention.overrides.items():
            if node_name in combined and combined[node_name] != value:
                warnings_list.append(
                    f"Conflict on '{node_name}': "
                    f"'{override_sources[node_name]}' set {combined[node_name]}, "
                    f"'{intervention.name}' overrides to {value} "
                    f"(applying {intervention.category.value} category order)"
                )
            combined[node_name] = value
            override_sources[node_name] = intervention.name

    return combined, warnings_list


def combine_interventions_for_year(
    interventions: list[Intervention], year: int
) -> tuple[dict[str, Any], list[str]]:
    """Combine multiple interventions for a specific year.

    Year-specific overrides take precedence over static overrides.
    """
    sorted_interventions = sorted(
        interventions, key=lambda i: CATEGORY_ORDER.index(i.category)
    )

    combined: dict[str, Any] = {}
    warnings_list: list[str] = []
    override_sources: dict[str, str] = {}

    for intervention in sorted_interventions:
        year_overrides = intervention.get_overrides_for_year(year)
        for node_name, value in year_overrides.items():
            if node_name in combined and combined[node_name] != value:
                warnings_list.append(
                    f"Conflict on '{node_name}' in year {year}: "
                    f"'{override_sources[node_name]}' set {combined[node_name]}, "
                    f"'{intervention.name}' overrides to {value}"
                )
            combined[node_name] = value
            override_sources[node_name] = intervention.name

    return combined, warnings_list


# --- Scenario differencing ---

def compute_intervention_delta(
    baseline_outputs: dict[int, dict[str, Any]],
    intervention_outputs: dict[int, dict[str, Any]],
    output_node: str = "total_emissions",
    metric: str = "total_ghg",
) -> dict[int, dict[str, float]]:
    """Compute per-year deltas between baseline and intervention scenarios.

    Returns dict of year -> {absolute, percentage} deltas.
    """
    deltas = {}
    for year in baseline_outputs:
        if year not in intervention_outputs:
            continue

        baseline_val = baseline_outputs[year].get(output_node, {})
        intervention_val = intervention_outputs[year].get(output_node, {})

        if isinstance(baseline_val, dict):
            b = baseline_val.get(metric, 0)
            i = intervention_val.get(metric, 0)
        else:
            b = baseline_val
            i = intervention_val

        absolute = i - b
        percentage = (absolute / b * 100) if b != 0 else 0.0

        deltas[year] = {"absolute": absolute, "percentage": percentage}

    return deltas


def attribute_interventions(
    baseline_outputs: dict[int, dict[str, Any]],
    individual_outputs: dict[str, dict[int, dict[str, Any]]],
    combined_outputs: dict[int, dict[str, Any]],
    output_node: str = "total_emissions",
    metric: str = "total_ghg",
) -> dict[str, dict[int, float]]:
    """Attribute combined effect to individual interventions.

    Uses Shapley-style decomposition: each intervention's independent effect
    plus a share of interaction effects.

    Args:
        baseline_outputs: Baseline scenario year outputs.
        individual_outputs: Dict of intervention_name -> year outputs when applied alone.
        combined_outputs: Year outputs with all interventions applied together.

    Returns:
        Dict of intervention_name -> {year -> attributed delta},
        plus "interaction" key for unexplained interaction effects.
    """
    attributions: dict[str, dict[int, float]] = {}
    interventions = list(individual_outputs.keys())

    for name in interventions:
        attributions[name] = {}

    attributions["interaction"] = {}

    for year in baseline_outputs:
        if year not in combined_outputs:
            continue

        b_val = baseline_outputs[year].get(output_node, {})
        c_val = combined_outputs[year].get(output_node, {})
        baseline_metric = b_val.get(metric, 0) if isinstance(b_val, dict) else b_val
        combined_metric = c_val.get(metric, 0) if isinstance(c_val, dict) else c_val
        total_delta = combined_metric - baseline_metric

        individual_deltas = {}
        for name in interventions:
            i_val = individual_outputs[name][year].get(output_node, {})
            i_metric = i_val.get(metric, 0) if isinstance(i_val, dict) else i_val
            individual_deltas[name] = i_metric - baseline_metric
            attributions[name][year] = individual_deltas[name]

        # Interaction = combined - sum of individual effects
        sum_individual = sum(individual_deltas.values())
        attributions["interaction"][year] = total_delta - sum_individual

    return attributions
