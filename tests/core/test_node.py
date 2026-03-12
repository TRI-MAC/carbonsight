"""Tests for node typing, distribution storage, auto-wiring, and temporal edges."""

import numpy as np
import pytest

from carbonsight.core.distributions import Distribution
from carbonsight.core.node import Node, NodeType, TEMPORAL_PREFIX


class TestNodeTyping:
    def test_create_scalar_node(self):
        node = Node(name="fleet_size", node_type=NodeType.SCALAR)
        assert node.node_type == NodeType.SCALAR
        assert node.name == "fleet_size"
        assert node.is_input

    def test_create_node_from_string_type(self):
        node = Node(name="x", node_type="scalar")
        assert node.node_type == NodeType.SCALAR

    def test_reject_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid node type 'matrix'"):
            Node(name="x", node_type="matrix")

    def test_all_valid_types(self):
        for t in NodeType:
            node = Node(name="x", node_type=t)
            assert node.node_type == t

    def test_distribution_node_holds_point_value(self):
        node = Node(name="grid_intensity", node_type=NodeType.DISTRIBUTION)
        node.set_value(369.0)
        assert isinstance(node.value, Distribution)
        assert node.get_point_estimate() == 369.0

    def test_distribution_node_holds_distribution(self):
        dist = Distribution.normal(mean=369, std=20)
        node = Node(name="grid_intensity", node_type=NodeType.DISTRIBUTION, value=dist)
        assert node.get_point_estimate() == 369.0

    def test_scalar_node_get_point_estimate(self):
        node = Node(name="x", node_type=NodeType.SCALAR, value=42.0)
        assert node.get_point_estimate() == 42.0

    def test_sample_from_distribution_node(self):
        dist = Distribution.normal(mean=100, std=10)
        node = Node(name="x", node_type=NodeType.DISTRIBUTION, value=dist)
        samples = node.sample(1000, rng=np.random.default_rng(42))
        assert len(samples) == 1000
        assert abs(np.mean(samples) - 100) < 2  # within ~2 std of mean

    def test_sample_from_non_distribution_raises(self):
        node = Node(name="x", node_type=NodeType.SCALAR, value=42.0)
        with pytest.raises(TypeError, match="cannot sample"):
            node.sample(10)


class TestDistributions:
    def test_point_distribution(self):
        d = Distribution.point(5.0)
        assert d.mean() == 5.0
        samples = d.sample(10)
        assert np.all(samples == 5.0)

    def test_normal_distribution(self):
        d = Distribution.normal(mean=100, std=10)
        assert d.mean() == 100.0
        samples = d.sample(10000, rng=np.random.default_rng(0))
        assert abs(np.mean(samples) - 100) < 1

    def test_normal_negative_std_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            Distribution.normal(mean=0, std=-1)

    def test_lognormal_distribution(self):
        d = Distribution.lognormal(mu=0, sigma=0.5)
        samples = d.sample(10000, rng=np.random.default_rng(0))
        assert abs(np.mean(samples) - d.mean()) < 0.1

    def test_uniform_distribution(self):
        d = Distribution.uniform(low=0, high=10)
        assert d.mean() == 5.0
        samples = d.sample(10000, rng=np.random.default_rng(0))
        assert np.all(samples >= 0)
        assert np.all(samples <= 10)

    def test_uniform_invalid_range(self):
        with pytest.raises(ValueError, match="<="):
            Distribution.uniform(low=10, high=0)

    def test_triangular_distribution(self):
        d = Distribution.triangular(low=0, mode=5, high=10)
        assert d.mean() == 5.0
        samples = d.sample(10000, rng=np.random.default_rng(0))
        assert abs(np.mean(samples) - 5.0) < 0.2

    def test_triangular_invalid_order(self):
        with pytest.raises(ValueError, match="low <= mode <= high"):
            Distribution.triangular(low=5, mode=2, high=10)

    def test_empirical_distribution(self):
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        d = Distribution.empirical(values)
        assert d.mean() == 3.0
        samples = d.sample(10000, rng=np.random.default_rng(0))
        assert set(samples).issubset({1.0, 2.0, 3.0, 4.0, 5.0})

    def test_empirical_empty_rejected(self):
        with pytest.raises(ValueError, match="at least one"):
            Distribution.empirical(np.array([]))


class TestAutoWiring:
    def test_compute_function_wires_upstream(self):
        def compute_total(fleet_size, renewal_rate):
            return fleet_size * renewal_rate

        node = Node(name="total", node_type=NodeType.SCALAR, compute_fn=compute_total)
        assert node.upstream_edges == ["fleet_size", "renewal_rate"]
        assert node.temporal_edges == []
        assert not node.is_input

    def test_temporal_parameter_wiring(self):
        def compute_preference(oil_price, prev_fleet_composition):
            return oil_price * 0.5

        node = Node(name="preference", node_type=NodeType.SCALAR, compute_fn=compute_preference)
        assert node.upstream_edges == ["oil_price"]
        assert node.temporal_edges == ["fleet_composition"]

    def test_mixed_temporal_and_regular(self):
        def compute(a, prev_b, c, prev_d):
            return a + c

        node = Node(name="x", node_type=NodeType.SCALAR, compute_fn=compute)
        assert node.upstream_edges == ["a", "c"]
        assert node.temporal_edges == ["b", "d"]

    def test_no_compute_function_no_edges(self):
        node = Node(name="input", node_type=NodeType.SCALAR)
        assert node.upstream_edges == []
        assert node.temporal_edges == []

    def test_all_dependencies(self):
        def compute(a, prev_b):
            return a

        node = Node(name="x", node_type=NodeType.SCALAR, compute_fn=compute)
        assert set(node.all_dependencies) == {"a", "b"}
