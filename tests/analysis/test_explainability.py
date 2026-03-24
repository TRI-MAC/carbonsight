"""Tests for explainability and provenance system."""

import pytest

from carbonsight.analysis.explainability import (
    compute_intervention_attribution,
    generate_provenance_report,
    get_node_lineage,
    trace_provenance_backward,
    trace_provenance_forward,
)
from carbonsight.core.graph import SimulationGraph
from carbonsight.core.node import Assumption, DataSource, Node, NodeType


@pytest.fixture
def simple_graph():
    """Graph with documented nodes for explainability testing."""
    graph = SimulationGraph()

    graph.add_node(
        Node(
            name="input_a",
            node_type=NodeType.SCALAR,
            value=10,
            data_source=DataSource(name="EPA Data", publication_date="2024", url="https://epa.gov"),
            assumptions=[
                Assumption(
                    description="Constant input",
                    rationale="Historical average",
                    confidence="high",
                )
            ],
            tags=["input"],
        )
    )

    graph.add_node(
        Node(
            name="input_b",
            node_type=NodeType.SCALAR,
            value=5,
            data_source=DataSource(name="NHTS 2017"),
            tags=["input"],
        )
    )

    graph.add_node(
        Node(
            name="intermediate",
            node_type=NodeType.SCALAR,
            compute_fn=lambda input_a, input_b: input_a * input_b,
            tags=["process"],
        )
    )

    graph.add_node(
        Node(
            name="output",
            node_type=NodeType.SCALAR,
            compute_fn=lambda intermediate: intermediate + 1,
            tags=["output"],
        )
    )

    graph.validate()
    return graph


class TestProvenanceTracing:
    def test_forward_trace(self, simple_graph):
        outputs, provenance = simple_graph.execute()
        downstream = trace_provenance_forward(simple_graph, "input_a", provenance)
        assert "intermediate" in downstream
        assert "output" in downstream
        assert "input_b" not in downstream

    def test_backward_trace(self, simple_graph):
        outputs, provenance = simple_graph.execute()
        chain = trace_provenance_backward(simple_graph, "output", provenance)
        assert chain.target_node == "output"
        assert len(chain.chain) > 0
        node_names = [r.node_name for r in chain.chain]
        assert "input_a" in node_names
        assert "input_b" in node_names
        assert "intermediate" in node_names

    def test_backward_collects_data_sources(self, simple_graph):
        outputs, provenance = simple_graph.execute()
        chain = trace_provenance_backward(simple_graph, "output", provenance)
        source_names = [ds.name for ds in chain.data_sources]
        assert "EPA Data" in source_names
        assert "NHTS 2017" in source_names

    def test_backward_collects_assumptions(self, simple_graph):
        outputs, provenance = simple_graph.execute()
        chain = trace_provenance_backward(simple_graph, "output", provenance)
        assert len(chain.assumptions) > 0
        assert chain.assumptions[0][0] == "input_a"
        assert chain.assumptions[0][1].confidence == "high"

    def test_nonexistent_node(self, simple_graph):
        outputs, provenance = simple_graph.execute()
        result = trace_provenance_forward(simple_graph, "nonexistent", provenance)
        assert result == []


class TestNodeLineage:
    def test_input_node_lineage(self, simple_graph):
        lineage = get_node_lineage(simple_graph, "input_a")
        assert lineage["node"] == "input_a"
        assert lineage["is_input"] is True
        assert lineage["data_source"]["name"] == "EPA Data"
        assert len(lineage["assumptions"]) == 1

    def test_compute_node_lineage(self, simple_graph):
        lineage = get_node_lineage(simple_graph, "intermediate")
        assert lineage["is_input"] is False
        assert "data_source" not in lineage

    def test_missing_node(self, simple_graph):
        lineage = get_node_lineage(simple_graph, "nonexistent")
        assert "error" in lineage


class TestInterventionAttribution:
    def test_additive_effects(self):
        result = compute_intervention_attribution(
            baseline_value=1000,
            individual_effects={"policy_a": 900, "tech_b": 950},
            combined_value=850,
        )
        assert result.total_delta == -150
        assert result.per_intervention["policy_a"] == -100
        assert result.per_intervention["tech_b"] == -50
        assert result.interaction_effect == 0  # Purely additive

    def test_interaction_effect(self):
        result = compute_intervention_attribution(
            baseline_value=1000,
            individual_effects={"a": 900, "b": 950},
            combined_value=800,
        )
        assert result.interaction_effect == -50  # Synergy

    def test_single_intervention(self):
        result = compute_intervention_attribution(
            baseline_value=1000,
            individual_effects={"policy": 900},
            combined_value=900,
        )
        assert result.total_delta == -100
        assert result.interaction_effect == 0


class TestProvenanceReport:
    def test_report_generation(self, simple_graph):
        outputs, provenance = simple_graph.execute()
        report = generate_provenance_report(simple_graph, provenance, "output", year=2024)
        assert "# Provenance Report: output" in report
        assert "2024" in report
        assert "EPA Data" in report
        assert "NHTS 2017" in report
        assert "Constant input" in report

    def test_report_contains_chain(self, simple_graph):
        outputs, provenance = simple_graph.execute()
        report = generate_provenance_report(simple_graph, provenance, "output")
        assert "input_a" in report
        assert "input_b" in report
        assert "intermediate" in report

    def test_report_for_input_node(self, simple_graph):
        outputs, provenance = simple_graph.execute()
        report = generate_provenance_report(simple_graph, provenance, "input_a")
        assert "# Provenance Report: input_a" in report
