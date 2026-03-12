"""Distribution types for CarbonSight's uncertainty-native value system.

Supports normal, lognormal, uniform, triangular, and empirical distributions.
Each can be used as a node value and sampled for Monte Carlo propagation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


class Distribution:
    """Base class for probability distributions used in UQ."""

    def mean(self) -> float:
        raise NotImplementedError

    def sample(self, n: int, rng: np.random.Generator | None = None) -> np.ndarray:
        raise NotImplementedError

    @staticmethod
    def point(value: float) -> PointDistribution:
        return PointDistribution(value=value)

    @staticmethod
    def normal(mean: float, std: float) -> NormalDistribution:
        if std < 0:
            raise ValueError(f"Standard deviation must be non-negative, got {std}")
        return NormalDistribution(mean=mean, std=std)

    @staticmethod
    def lognormal(mu: float, sigma: float) -> LognormalDistribution:
        if sigma < 0:
            raise ValueError(f"Sigma must be non-negative, got {sigma}")
        return LognormalDistribution(mu=mu, sigma=sigma)

    @staticmethod
    def uniform(low: float, high: float) -> UniformDistribution:
        if low > high:
            raise ValueError(f"Low ({low}) must be <= high ({high})")
        return UniformDistribution(low=low, high=high)

    @staticmethod
    def triangular(low: float, mode: float, high: float) -> TriangularDistribution:
        if not (low <= mode <= high):
            raise ValueError(f"Must have low <= mode <= high, got {low}, {mode}, {high}")
        return TriangularDistribution(low=low, mode=mode, high=high)

    @staticmethod
    def empirical(values: np.ndarray) -> EmpiricalDistribution:
        values = np.asarray(values, dtype=float)
        if values.size == 0:
            raise ValueError("Empirical distribution requires at least one value")
        return EmpiricalDistribution(values=values)


@dataclass(frozen=True)
class PointDistribution(Distribution):
    """Degenerate distribution at a single value (no uncertainty)."""

    value: float

    def mean(self) -> float:
        return self.value

    def sample(self, n: int, rng: np.random.Generator | None = None) -> np.ndarray:
        return np.full(n, self.value)


@dataclass(frozen=True)
class NormalDistribution(Distribution):
    mean_val: float
    std: float

    def __init__(self, mean: float, std: float):
        object.__setattr__(self, "mean_val", mean)
        object.__setattr__(self, "std", std)

    def mean(self) -> float:
        return self.mean_val

    def sample(self, n: int, rng: np.random.Generator | None = None) -> np.ndarray:
        rng = rng or np.random.default_rng()
        return rng.normal(self.mean_val, self.std, size=n)


@dataclass(frozen=True)
class LognormalDistribution(Distribution):
    mu: float
    sigma: float

    def mean(self) -> float:
        return float(np.exp(self.mu + self.sigma**2 / 2))

    def sample(self, n: int, rng: np.random.Generator | None = None) -> np.ndarray:
        rng = rng or np.random.default_rng()
        return rng.lognormal(self.mu, self.sigma, size=n)


@dataclass(frozen=True)
class UniformDistribution(Distribution):
    low: float
    high: float

    def mean(self) -> float:
        return (self.low + self.high) / 2

    def sample(self, n: int, rng: np.random.Generator | None = None) -> np.ndarray:
        rng = rng or np.random.default_rng()
        return rng.uniform(self.low, self.high, size=n)


@dataclass(frozen=True)
class TriangularDistribution(Distribution):
    low: float
    mode: float
    high: float

    def mean(self) -> float:
        return (self.low + self.mode + self.high) / 3

    def sample(self, n: int, rng: np.random.Generator | None = None) -> np.ndarray:
        rng = rng or np.random.default_rng()
        return rng.triangular(self.low, self.mode, self.high, size=n)


@dataclass
class EmpiricalDistribution(Distribution):
    values: np.ndarray = field(default_factory=lambda: np.array([]))

    def mean(self) -> float:
        return float(np.mean(self.values))

    def sample(self, n: int, rng: np.random.Generator | None = None) -> np.ndarray:
        rng = rng or np.random.default_rng()
        return rng.choice(self.values, size=n, replace=True)
