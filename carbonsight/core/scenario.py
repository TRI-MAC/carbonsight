"""Scenario management for CarbonSight.

A Scenario is a named configuration of input-node overrides that defines
a specific "what if" case. The system compares baseline vs. counterfactual
scenarios to quantify intervention impacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import yaml

from carbonsight.core.engine import SimulationResult


@dataclass
class InterventionSpec:
    """A lightweight reference to an intervention factory with parameters."""

    type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scenario:
    """A named configuration of input-node value overrides."""

    name: str
    overrides: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    interventions: list[InterventionSpec] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "overrides": {k: _serialize_value(v) for k, v in self.overrides.items()},
            "metadata": self.metadata,
            "interventions": [{"type": i.type, "params": i.params} for i in self.interventions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Scenario:
        interventions = [
            InterventionSpec(type=i["type"], params=i.get("params", {}))
            for i in data.get("interventions", [])
        ]
        return cls(
            name=data["name"],
            overrides=data.get("overrides", {}),
            metadata=data.get("metadata", {}),
            interventions=interventions,
        )

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> Scenario:
        return cls.from_dict(yaml.safe_load(yaml_str))


def _serialize_value(v: Any) -> Any:
    """Convert numpy types to Python native for serialization."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


class ScenarioStore:
    """In-memory CRUD store for scenarios with unique name enforcement."""

    def __init__(self):
        self._scenarios: dict[str, Scenario] = {}

    def create(self, scenario: Scenario) -> Scenario:
        if scenario.name in self._scenarios:
            raise ValueError(f"Scenario '{scenario.name}' already exists")
        self._scenarios[scenario.name] = scenario
        return scenario

    def get(self, name: str) -> Scenario:
        if name not in self._scenarios:
            raise KeyError(f"Scenario '{name}' not found")
        return self._scenarios[name]

    def update(
        self,
        name: str,
        overrides: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Scenario:
        scenario = self.get(name)
        if overrides is not None:
            scenario.overrides = overrides
        if metadata is not None:
            scenario.metadata = metadata
        return scenario

    def delete(self, name: str):
        if name not in self._scenarios:
            raise KeyError(f"Scenario '{name}' not found")
        del self._scenarios[name]

    def list(self) -> list[str]:
        return list(self._scenarios.keys())


@dataclass
class ComparisonDelta:
    """Per-node, per-year delta between baseline and intervention."""

    node_name: str
    year: int
    baseline_value: Any
    intervention_value: Any
    absolute_delta: float
    percentage_delta: float | None  # None if baseline is 0


@dataclass
class ScenarioComparison:
    """Full comparison between a baseline and intervention scenario."""

    baseline_name: str
    intervention_name: str
    deltas: list[ComparisonDelta] = field(default_factory=list)

    def deltas_for_node(self, node_name: str) -> list[ComparisonDelta]:
        return [d for d in self.deltas if d.node_name == node_name]

    def deltas_for_year(self, year: int) -> list[ComparisonDelta]:
        return [d for d in self.deltas if d.year == year]


@dataclass
class DistributionSummary:
    """Summary statistics for a distribution-typed output."""

    mean: float
    median: float
    p5: float
    p25: float
    p75: float
    p95: float
    std: float


def summarize_samples(samples: np.ndarray) -> DistributionSummary:
    """Compute summary statistics from Monte Carlo samples."""
    return DistributionSummary(
        mean=float(np.mean(samples)),
        median=float(np.median(samples)),
        p5=float(np.percentile(samples, 5)),
        p25=float(np.percentile(samples, 25)),
        p75=float(np.percentile(samples, 75)),
        p95=float(np.percentile(samples, 95)),
        std=float(np.std(samples)),
    )


def compare_scenarios(
    baseline: SimulationResult,
    intervention: SimulationResult,
    baseline_name: str = "baseline",
    intervention_name: str = "intervention",
    nodes: list[str] | None = None,
) -> ScenarioComparison:
    """Compare two simulation results, computing per-year deltas for all output nodes.

    Args:
        baseline: SimulationResult from baseline scenario.
        intervention: SimulationResult from intervention scenario.
        baseline_name: Name for the baseline scenario.
        intervention_name: Name for the intervention scenario.
        nodes: Optional list of node names to compare. If None, compares all.

    Returns:
        ScenarioComparison with per-node, per-year deltas.
    """
    comparison = ScenarioComparison(
        baseline_name=baseline_name,
        intervention_name=intervention_name,
    )

    for b_yr, i_yr in zip(baseline.year_results, intervention.year_results):
        assert b_yr.year == i_yr.year, "Year mismatch between scenarios"
        year = b_yr.year

        compare_nodes = nodes or list(b_yr.outputs.keys())
        for node_name in compare_nodes:
            if node_name not in b_yr.outputs or node_name not in i_yr.outputs:
                continue

            b_val = b_yr.outputs[node_name]
            i_val = i_yr.outputs[node_name]

            # Handle numeric values
            if isinstance(b_val, (int, float)) and isinstance(i_val, (int, float)):
                abs_delta = i_val - b_val
                pct_delta = (abs_delta / b_val * 100) if b_val != 0 else None
                comparison.deltas.append(
                    ComparisonDelta(
                        node_name=node_name,
                        year=year,
                        baseline_value=b_val,
                        intervention_value=i_val,
                        absolute_delta=abs_delta,
                        percentage_delta=pct_delta,
                    )
                )

    return comparison


def compare_distribution_results(
    baseline_samples: dict[str, dict[int, np.ndarray]],
    intervention_samples: dict[str, dict[int, np.ndarray]],
    baseline_name: str = "baseline",
    intervention_name: str = "intervention",
) -> dict[str, dict[int, dict[str, float]]]:
    """Compare distribution-typed results, computing deltas on summary statistics.

    Args:
        baseline_samples: {node_name: {year: samples_array}}
        intervention_samples: {node_name: {year: samples_array}}

    Returns:
        {node_name: {year: {stat_name: delta_value}}}
    """
    result = {}
    for node_name in baseline_samples:
        if node_name not in intervention_samples:
            continue
        result[node_name] = {}
        for year in baseline_samples[node_name]:
            if year not in intervention_samples[node_name]:
                continue
            b_summary = summarize_samples(baseline_samples[node_name][year])
            i_summary = summarize_samples(intervention_samples[node_name][year])
            result[node_name][year] = {
                "mean_delta": i_summary.mean - b_summary.mean,
                "median_delta": i_summary.median - b_summary.median,
                "p5_delta": i_summary.p5 - b_summary.p5,
                "p95_delta": i_summary.p95 - b_summary.p95,
            }
    return result


# --- Intervention resolution ---

INTERVENTION_FACTORIES = {
    "carbon_pricing": "carbonsight.domain.interventions.carbon_pricing",
    "ev_subsidy": "carbonsight.domain.interventions.ev_subsidy",
    "vmt_reduction": "carbonsight.domain.interventions.vmt_reduction",
    "grid_decarbonization": "carbonsight.domain.interventions.grid_decarbonization",
    "battery_cost_reduction": "carbonsight.domain.interventions.battery_cost_reduction",
    "scrappage_program": "carbonsight.domain.interventions.scrappage_program",
    "phev_charging_improvement": "carbonsight.domain.interventions.phev_charging_improvement",
    "oil_price_shock": "carbonsight.domain.interventions.oil_price_shock",
    "electricity_price_change": "carbonsight.domain.interventions.electricity_price_change",
    "body_manufacturing_decarb": "carbonsight.domain.interventions.body_manufacturing_decarb",
    "ice_manufacturing_decarb": "carbonsight.domain.interventions.ice_manufacturing_decarb",
    "disposal_reduction": "carbonsight.domain.interventions.disposal_reduction",
    "sales_volume_change": "carbonsight.domain.interventions.sales_volume_change",
    "used_market_incentive": "carbonsight.domain.interventions.used_market_incentive",
    "eco_driving": "carbonsight.domain.interventions.eco_driving",
}


def resolve_interventions(specs: list[InterventionSpec]) -> list:
    """Convert InterventionSpec list to Intervention objects via factory functions.

    Returns list of Intervention objects.
    Raises ValueError for unknown intervention types.
    """
    from carbonsight.domain import interventions as iv_module

    factory_map = {
        "carbon_pricing": iv_module.carbon_pricing,
        "ev_subsidy": iv_module.ev_subsidy,
        "vmt_reduction": iv_module.vmt_reduction,
        "grid_decarbonization": iv_module.grid_decarbonization,
        "battery_cost_reduction": iv_module.battery_cost_reduction,
        "scrappage_program": iv_module.scrappage_program,
        "phev_charging_improvement": iv_module.phev_charging_improvement,
        "oil_price_shock": iv_module.oil_price_shock,
        "electricity_price_change": iv_module.electricity_price_change,
        "body_manufacturing_decarb": iv_module.body_manufacturing_decarb,
        "ice_manufacturing_decarb": iv_module.ice_manufacturing_decarb,
        "disposal_reduction": iv_module.disposal_reduction,
        "sales_volume_change": iv_module.sales_volume_change,
        "used_market_incentive": iv_module.used_market_incentive,
        "eco_driving": iv_module.eco_driving,
    }

    results = []
    for spec in specs:
        factory = factory_map.get(spec.type)
        if factory is None:
            raise ValueError(
                f"Unknown intervention type '{spec.type}'. "
                f"Available: {', '.join(sorted(factory_map.keys()))}"
            )
        results.append(factory(**spec.params))
    return results


def resolve_year_overrides(
    interventions: list,
    years: list[int],
) -> dict[int, dict[str, Any]]:
    """Convert Intervention objects to per-year override dicts.

    Uses combine_interventions_for_year() for each year to merge
    multiple interventions with conflict detection.
    """
    from carbonsight.domain.interventions import combine_interventions_for_year

    year_overrides: dict[int, dict[str, Any]] = {}
    for year in years:
        combined, _warnings = combine_interventions_for_year(interventions, year)
        if combined:
            year_overrides[year] = combined
    return year_overrides
