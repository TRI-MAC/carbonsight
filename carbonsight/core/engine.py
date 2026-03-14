"""Simulation engine with year-by-year time stepping.

Orchestrates the SimulationGraph execution over a configurable time horizon,
resolving temporal edges from the year-indexed output store. Supports
deterministic (point estimate) and UQ (Monte Carlo) execution modes.
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any

from carbonsight.core.graph import ProvenanceRecord, SimulationGraph


class ExecutionMode(enum.Enum):
    DETERMINISTIC = "deterministic"
    UQ = "uq"


@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""

    start_year: int = 2024
    num_years: int = 10
    renewal_rate: float = 0.05
    execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC
    uq_samples: int = 200  # For UQ mode: number of Monte Carlo samples

    @property
    def years(self) -> list[int]:
        return list(range(self.start_year, self.start_year + self.num_years))


@dataclass
class YearResult:
    """Results from a single year of simulation."""

    year: int
    outputs: dict[str, Any]
    provenance: list[ProvenanceRecord]


@dataclass
class SimulationResult:
    """Complete results from a multi-year simulation run."""

    config: SimulationConfig
    execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC
    year_results: list[YearResult] = field(default_factory=list)
    wall_clock_seconds: float = 0.0
    performance_warning: str | None = None

    @property
    def years(self) -> list[int]:
        return [yr.year for yr in self.year_results]

    def outputs_for_year(self, year: int) -> dict[str, Any]:
        for yr in self.year_results:
            if yr.year == year:
                return yr.outputs
        raise KeyError(f"No results for year {year}")

    def output_timeseries(self, node_name: str) -> dict[int, Any]:
        """Get a node's output value for each year."""
        return {yr.year: yr.outputs[node_name] for yr in self.year_results if node_name in yr.outputs}


class SimulationEngine:
    """Executes a SimulationGraph over a multi-year time horizon.

    Handles:
    - Year-by-year time stepping
    - Output chaining (year N outputs → year N+1 temporal edge resolution)
    - Year-indexed output store
    - Configurable time horizon
    - Performance timing and warnings
    """

    PERFORMANCE_TARGET_SECONDS = 60.0

    def __init__(self, graph: SimulationGraph, config: SimulationConfig | None = None):
        self.graph = graph
        self.config = config or SimulationConfig()
        self._running = False
        self._active_mode: ExecutionMode | None = None

    def run(
        self,
        overrides: dict[str, Any] | None = None,
        mode: ExecutionMode | None = None,
        year_overrides: dict[int, dict[str, Any]] | None = None,
    ) -> SimulationResult:
        """Run the simulation over the full time horizon.

        Args:
            overrides: Optional dict of node_name -> value to override input nodes.
                These overrides apply to every year step.
            mode: Execution mode override. If None, uses config.execution_mode.
            year_overrides: Optional dict of year -> {node_name: value} for
                time-varying overrides. Year-specific values take precedence
                over base overrides.

        Returns:
            SimulationResult with year-by-year outputs and provenance.
        """
        if self._running:
            raise RuntimeError("Simulation is already running. Cannot change mode mid-execution.")

        exec_mode = mode or self.config.execution_mode
        self._running = True
        self._active_mode = exec_mode

        try:
            self.graph.validate()

            if exec_mode == ExecutionMode.DETERMINISTIC:
                return self._run_deterministic(overrides, year_overrides)
            else:
                return self._run_uq(overrides, year_overrides)
        finally:
            self._running = False
            self._active_mode = None

    def _run_deterministic(self, overrides: dict[str, Any] | None, year_overrides: dict[int, dict[str, Any]] | None = None) -> SimulationResult:
        """Run in deterministic mode: collapse distributions to point estimates."""
        from carbonsight.core.distributions import Distribution

        # Collapse any distribution overrides to point estimates
        effective_overrides = dict(overrides) if overrides else {}
        for node_name, node in self.graph.nodes.items():
            if isinstance(node.value, Distribution) and node_name not in effective_overrides:
                effective_overrides[node_name] = node.value.mean()

        result = SimulationResult(
            config=self.config,
            execution_mode=ExecutionMode.DETERMINISTIC,
        )
        prior_year_outputs: dict[str, Any] | None = None
        start_time = time.monotonic()

        for idx, year in enumerate(self.config.years):
            step_overrides = dict(effective_overrides)
            step_overrides["year_index"] = idx
            if year_overrides and year in year_overrides:
                step_overrides.update(year_overrides[year])
            outputs, provenance = self.graph.execute(
                overrides=step_overrides,
                prior_year_outputs=prior_year_outputs,
            )
            result.year_results.append(YearResult(year=year, outputs=outputs, provenance=provenance))
            prior_year_outputs = outputs

        result.wall_clock_seconds = time.monotonic() - start_time
        self._check_performance(result)
        return result

    def _run_uq(self, overrides: dict[str, Any] | None, year_overrides: dict[int, dict[str, Any]] | None = None) -> SimulationResult:
        """Run in UQ mode: Monte Carlo propagation through the DAG."""
        import numpy as np

        from carbonsight.core.distributions import Distribution

        n_samples = self.config.uq_samples
        rng = np.random.default_rng()

        # Identify distribution nodes and pre-sample
        dist_nodes: dict[str, Distribution] = {}
        for node_name, node in self.graph.nodes.items():
            if isinstance(node.value, Distribution) and node_name not in (overrides or {}):
                dist_nodes[node_name] = node.value

        # For each sample, run the full simulation
        all_sample_results: list[SimulationResult] = []
        start_time = time.monotonic()

        for i in range(n_samples):
            sample_overrides = dict(overrides) if overrides else {}
            for node_name, dist in dist_nodes.items():
                sample_overrides[node_name] = float(dist.sample(1, rng=rng)[0])

            prior_year_outputs: dict[str, Any] | None = None
            sample_year_results = []

            for idx, year in enumerate(self.config.years):
                step_overrides = dict(sample_overrides)
                step_overrides["year_index"] = idx
                if year_overrides and year in year_overrides:
                    step_overrides.update(year_overrides[year])
                outputs, provenance = self.graph.execute(
                    overrides=step_overrides,
                    prior_year_outputs=prior_year_outputs,
                )
                sample_year_results.append(YearResult(year=year, outputs=outputs, provenance=provenance))
                prior_year_outputs = outputs

            all_sample_results.append(
                SimulationResult(config=self.config, year_results=sample_year_results)
            )

        # Aggregate: for each year and node, collect samples and compute summary
        result = SimulationResult(
            config=self.config,
            execution_mode=ExecutionMode.UQ,
        )

        for year_idx, year in enumerate(self.config.years):
            aggregated_outputs: dict[str, Any] = {}
            # Collect all node names from first sample
            node_names = list(all_sample_results[0].year_results[year_idx].outputs.keys())

            for node_name in node_names:
                values = []
                for sr in all_sample_results:
                    v = sr.year_results[year_idx].outputs[node_name]
                    if isinstance(v, (int, float)):
                        values.append(v)

                if values:
                    samples_array = np.array(values)
                    aggregated_outputs[node_name] = {
                        "mean": float(np.mean(samples_array)),
                        "median": float(np.median(samples_array)),
                        "std": float(np.std(samples_array)),
                        "p5": float(np.percentile(samples_array, 5)),
                        "p25": float(np.percentile(samples_array, 25)),
                        "p75": float(np.percentile(samples_array, 75)),
                        "p95": float(np.percentile(samples_array, 95)),
                        "samples": samples_array,
                    }
                else:
                    # Non-numeric output, take from first sample
                    aggregated_outputs[node_name] = all_sample_results[0].year_results[year_idx].outputs[node_name]

            # Use provenance from first sample as representative
            result.year_results.append(YearResult(
                year=year,
                outputs=aggregated_outputs,
                provenance=all_sample_results[0].year_results[year_idx].provenance,
            ))

        result.wall_clock_seconds = time.monotonic() - start_time
        self._check_performance(result)
        return result

    def _check_performance(self, result: SimulationResult):
        if result.wall_clock_seconds > self.PERFORMANCE_TARGET_SECONDS:
            result.performance_warning = (
                f"Execution took {result.wall_clock_seconds:.1f}s, exceeding the "
                f"{self.PERFORMANCE_TARGET_SECONDS:.0f}s target by "
                f"{result.wall_clock_seconds - self.PERFORMANCE_TARGET_SECONDS:.1f}s"
            )
