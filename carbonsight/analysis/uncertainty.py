"""Uncertainty quantification analysis for CarbonSight.

Provides distribution specification, confidence interval computation,
sensitivity analysis (Sobol indices), and top-N driver identification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from carbonsight.core.distributions import Distribution


@dataclass
class ConfidenceInterval:
    """Confidence interval summary for a simulation output."""

    node_name: str
    year: int
    mean: float
    median: float
    std: float
    p5: float
    p25: float
    p75: float
    p95: float
    n_samples: int

    @classmethod
    def from_samples(cls, node_name: str, year: int, samples: np.ndarray) -> ConfidenceInterval:
        return cls(
            node_name=node_name,
            year=year,
            mean=float(np.mean(samples)),
            median=float(np.median(samples)),
            std=float(np.std(samples)),
            p5=float(np.percentile(samples, 5)),
            p25=float(np.percentile(samples, 25)),
            p75=float(np.percentile(samples, 75)),
            p95=float(np.percentile(samples, 95)),
            n_samples=len(samples),
        )


@dataclass
class SensitivityResult:
    """Result of variance-based sensitivity analysis."""

    output_node: str
    year: int
    first_order: dict[str, float]  # input_node -> S1
    total_order: dict[str, float]  # input_node -> ST
    n_samples: int


@dataclass
class UncertaintyDriver:
    """A ranked uncertainty contributor."""

    input_node: str
    total_order_index: float
    first_order_index: float
    description: str = ""


def extract_confidence_intervals(
    simulation_result: Any, node_name: str
) -> list[ConfidenceInterval]:
    """Extract confidence intervals from a UQ SimulationResult.

    Args:
        simulation_result: SimulationResult from UQ mode execution.
        node_name: Name of the output node to analyze.

    Returns:
        List of ConfidenceInterval, one per year.
    """
    intervals = []
    for yr in simulation_result.year_results:
        output = yr.outputs.get(node_name)
        if output is None:
            continue
        if isinstance(output, dict) and "samples" in output:
            ci = ConfidenceInterval.from_samples(
                node_name=node_name,
                year=yr.year,
                samples=output["samples"],
            )
            intervals.append(ci)
        elif isinstance(output, dict) and "mean" in output:
            intervals.append(
                ConfidenceInterval(
                    node_name=node_name,
                    year=yr.year,
                    mean=output["mean"],
                    median=output["median"],
                    std=output["std"],
                    p5=output["p5"],
                    p25=output["p25"],
                    p75=output["p75"],
                    p95=output["p95"],
                    n_samples=output.get("n_samples", 0),
                )
            )
    return intervals


def latin_hypercube_sample(
    distributions: dict[str, Distribution],
    n_samples: int,
    rng: np.random.Generator | None = None,
) -> dict[str, np.ndarray]:
    """Generate Latin Hypercube Samples for the given distributions.

    Provides better stratified coverage than pure random sampling.

    Returns:
        Dict of node_name -> array of n_samples values.
    """
    if rng is None:
        rng = np.random.default_rng()

    n_vars = len(distributions)
    if n_vars == 0:
        return {}

    samples = {}
    for name, dist in distributions.items():
        # Generate stratified uniform samples
        intervals = np.linspace(0, 1, n_samples + 1)
        lower = intervals[:-1]
        upper = intervals[1:]
        # Random point within each stratum
        uniform_samples = rng.uniform(lower, upper)
        # Shuffle to decorrelate across variables
        rng.shuffle(uniform_samples)
        # Transform uniform to target distribution via inverse CDF
        # For now, use distribution sampling with sorted approach
        raw_samples = dist.sample(n_samples, rng=rng)
        raw_samples.sort()
        # Apply LHS ordering
        order = np.argsort(uniform_samples)
        lhs_samples = np.empty(n_samples)
        lhs_samples[order] = raw_samples
        samples[name] = lhs_samples

    return samples


def compute_sobol_indices(
    input_samples: dict[str, np.ndarray],
    output_samples: np.ndarray,
) -> SensitivityResult:
    """Compute first-order and total-order Sobol sensitivity indices.

    Uses a correlation-based approximation for computational efficiency.
    For production use, should be replaced with SALib's Sobol analysis.

    Args:
        input_samples: Dict of input_name -> sample arrays.
        output_samples: Array of output values corresponding to input samples.

    Returns:
        SensitivityResult with first-order and total-order indices.
    """
    n = len(output_samples)
    var_y = np.var(output_samples)

    first_order = {}
    total_order = {}

    if var_y == 0:
        # No variance in output
        for name in input_samples:
            first_order[name] = 0.0
            total_order[name] = 0.0
        return SensitivityResult(
            output_node="",
            year=0,
            first_order=first_order,
            total_order=total_order,
            n_samples=n,
        )

    for name, x_samples in input_samples.items():
        # First-order: correlation-based approximation
        # S1 ≈ corr(X, Y)^2
        corr = np.corrcoef(x_samples, output_samples)[0, 1]
        s1 = corr**2 if not np.isnan(corr) else 0.0
        first_order[name] = float(s1)

        # Total-order: approximate as first-order for now
        # (proper total-order requires Saltelli's sampling scheme)
        total_order[name] = float(s1)

    return SensitivityResult(
        output_node="",
        year=0,
        first_order=first_order,
        total_order=total_order,
        n_samples=n,
    )


def identify_top_drivers(
    sensitivity: SensitivityResult,
    top_n: int = 5,
    node_descriptions: dict[str, str] | None = None,
) -> list[UncertaintyDriver]:
    """Identify the top-N uncertainty drivers from sensitivity analysis.

    Args:
        sensitivity: SensitivityResult from Sobol analysis.
        top_n: Number of top drivers to return.
        node_descriptions: Optional human-readable descriptions for nodes.

    Returns:
        List of UncertaintyDriver ranked by total-order index.
    """
    descriptions = node_descriptions or {}
    drivers = []
    for name, st in sensitivity.total_order.items():
        drivers.append(
            UncertaintyDriver(
                input_node=name,
                total_order_index=st,
                first_order_index=sensitivity.first_order.get(name, 0),
                description=descriptions.get(name, name),
            )
        )

    drivers.sort(key=lambda d: d.total_order_index, reverse=True)
    return drivers[:top_n]


def check_sample_sufficiency(
    n_samples: int, n_inputs: int, mode: str = "interactive"
) -> str | None:
    """Check if sample count is sufficient and return warning if not.

    Args:
        n_samples: Number of MC samples.
        n_inputs: Number of uncertain input parameters.
        mode: "interactive" (100-500), "full" (5000+), "custom".

    Returns:
        Warning message if insufficient, None otherwise.
    """
    if mode == "interactive":
        recommended = max(100, 10 * n_inputs)
        if n_samples < recommended:
            return (
                f"Sample count {n_samples} may be insufficient for {n_inputs} "
                f"uncertain inputs. Recommended minimum: {recommended} for interactive mode."
            )
    elif mode == "full":
        recommended = max(5000, 100 * n_inputs)
        if n_samples < recommended:
            return (
                f"Sample count {n_samples} is below the recommended {recommended} "
                f"for full sensitivity analysis with {n_inputs} inputs."
            )
    return None
