"""Tests for uncertainty quantification analysis."""

import numpy as np
import pytest

from carbonsight.core.distributions import Distribution
from carbonsight.analysis.uncertainty import (
    ConfidenceInterval,
    check_sample_sufficiency,
    compute_sobol_indices,
    extract_confidence_intervals,
    identify_top_drivers,
    latin_hypercube_sample,
)


class TestConfidenceInterval:
    def test_from_samples(self):
        rng = np.random.default_rng(42)
        samples = rng.normal(100, 10, 1000)
        ci = ConfidenceInterval.from_samples("test_node", 2024, samples)
        assert ci.node_name == "test_node"
        assert ci.year == 2024
        assert abs(ci.mean - 100) < 2
        assert abs(ci.std - 10) < 2
        assert ci.p5 < ci.p25 < ci.median < ci.p75 < ci.p95
        assert ci.n_samples == 1000

    def test_narrow_distribution(self):
        samples = np.array([10.0] * 100)
        ci = ConfidenceInterval.from_samples("const", 2024, samples)
        assert ci.mean == 10.0
        assert ci.std == 0.0
        assert ci.p5 == 10.0


class TestLatinHypercubeSample:
    def test_produces_correct_count(self):
        dists = {
            "a": Distribution.normal(0, 1),
            "b": Distribution.uniform(0, 10),
        }
        samples = latin_hypercube_sample(dists, 100)
        assert len(samples["a"]) == 100
        assert len(samples["b"]) == 100

    def test_empty_distributions(self):
        samples = latin_hypercube_sample({}, 100)
        assert samples == {}

    def test_better_coverage_than_random(self):
        dist = Distribution.uniform(0, 1)
        rng = np.random.default_rng(42)
        lhs = latin_hypercube_sample({"x": dist}, 100, rng=rng)
        # LHS should have samples in every decile
        samples = lhs["x"]
        for decile in range(10):
            lo = decile / 10
            hi = (decile + 1) / 10
            count = np.sum((samples >= lo) & (samples < hi))
            assert count > 0, f"No samples in decile [{lo}, {hi})"


class TestSobolIndices:
    def test_linear_model(self):
        rng = np.random.default_rng(42)
        n = 1000
        x1 = rng.normal(0, 1, n)
        x2 = rng.normal(0, 1, n)
        # y = 3*x1 + x2 → x1 should have higher sensitivity
        y = 3 * x1 + x2
        result = compute_sobol_indices({"x1": x1, "x2": x2}, y)
        assert result.first_order["x1"] > result.first_order["x2"]

    def test_constant_output(self):
        n = 100
        x = np.random.randn(n)
        y = np.ones(n) * 5.0
        result = compute_sobol_indices({"x": x}, y)
        assert result.first_order["x"] == 0.0

    def test_single_variable(self):
        rng = np.random.default_rng(42)
        n = 500
        x = rng.normal(0, 1, n)
        y = 2 * x + 0.1 * rng.normal(0, 1, n)
        result = compute_sobol_indices({"x": x}, y)
        assert result.first_order["x"] > 0.8


class TestTopDrivers:
    def test_ranks_correctly(self):
        from carbonsight.analysis.uncertainty import SensitivityResult
        sr = SensitivityResult(
            output_node="total_ghg", year=2024,
            first_order={"a": 0.5, "b": 0.3, "c": 0.1},
            total_order={"a": 0.6, "b": 0.3, "c": 0.1},
            n_samples=1000,
        )
        drivers = identify_top_drivers(sr, top_n=2)
        assert len(drivers) == 2
        assert drivers[0].input_node == "a"
        assert drivers[1].input_node == "b"

    def test_with_descriptions(self):
        from carbonsight.analysis.uncertainty import SensitivityResult
        sr = SensitivityResult(
            output_node="total_ghg", year=2024,
            first_order={"battery_cost": 0.5},
            total_order={"battery_cost": 0.6},
            n_samples=1000,
        )
        drivers = identify_top_drivers(
            sr, top_n=1,
            node_descriptions={"battery_cost": "Battery production cost per kWh"},
        )
        assert drivers[0].description == "Battery production cost per kWh"


class TestSampleSufficiency:
    def test_interactive_sufficient(self):
        warn = check_sample_sufficiency(200, 5, mode="interactive")
        assert warn is None

    def test_interactive_insufficient(self):
        warn = check_sample_sufficiency(10, 20, mode="interactive")
        assert warn is not None
        assert "insufficient" in warn.lower()

    def test_full_insufficient(self):
        warn = check_sample_sufficiency(100, 10, mode="full")
        assert warn is not None

    def test_full_sufficient(self):
        warn = check_sample_sufficiency(10000, 10, mode="full")
        assert warn is None
