"""Explainability and provenance system for CarbonSight.

Provides provenance recording, traceability queries, intervention attribution,
data source lineage, assumption documentation, and report generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from carbonsight.core.graph import ProvenanceRecord, SimulationGraph
from carbonsight.core.node import Assumption, DataSource


@dataclass
class ProvenanceChain:
    """A chain of provenance records tracing from output to inputs."""

    target_node: str
    chain: list[ProvenanceRecord]
    data_sources: list[DataSource]
    assumptions: list[tuple[str, Assumption]]  # (node_name, assumption)


@dataclass
class AttributionResult:
    """Decomposition of total effect into per-intervention contributions."""

    total_delta: float
    per_intervention: dict[str, float]
    interaction_effect: float


def trace_provenance_forward(
    graph: SimulationGraph,
    start_node: str,
    provenance: list[ProvenanceRecord],
) -> list[str]:
    """Forward chain: find all nodes downstream of start_node.

    Returns list of node names that depend (directly or transitively) on start_node.
    """
    import networkx as nx

    dag = graph._dag
    if start_node not in dag:
        return []

    return list(nx.descendants(dag, start_node))


def trace_provenance_backward(
    graph: SimulationGraph,
    target_node: str,
    provenance: list[ProvenanceRecord],
) -> ProvenanceChain:
    """Backward chain: trace all inputs that contribute to target_node.

    Collects provenance records, data sources, and assumptions along the way.
    """
    import networkx as nx

    dag = graph._dag
    if target_node not in dag:
        return ProvenanceChain(target_node=target_node, chain=[], data_sources=[], assumptions=[])

    ancestors = list(nx.ancestors(dag, target_node))
    ancestors.append(target_node)

    # Collect provenance records for the chain
    prov_map = {r.node_name: r for r in provenance}
    chain = [prov_map[name] for name in ancestors if name in prov_map]

    # Collect data sources and assumptions
    data_sources = []
    assumptions = []
    for name in ancestors:
        node = graph.nodes.get(name)
        if node:
            if node.data_source:
                data_sources.append(node.data_source)
            for a in node.assumptions:
                assumptions.append((name, a))

    return ProvenanceChain(
        target_node=target_node,
        chain=chain,
        data_sources=data_sources,
        assumptions=assumptions,
    )


def get_node_lineage(graph: SimulationGraph, node_name: str) -> dict[str, Any]:
    """Get data source lineage metadata for a node."""
    node = graph.nodes.get(node_name)
    if not node:
        return {"node": node_name, "error": "Node not found"}

    result: dict[str, Any] = {
        "node": node_name,
        "type": node.node_type.value,
        "is_input": node.is_input,
        "tags": node.tags,
    }

    if node.data_source:
        result["data_source"] = {
            "name": node.data_source.name,
            "publication_date": node.data_source.publication_date,
            "version": node.data_source.version,
            "url": node.data_source.url,
            "transformations": node.data_source.transformations,
        }

    if node.assumptions:
        result["assumptions"] = [
            {
                "description": a.description,
                "rationale": a.rationale,
                "confidence": a.confidence,
            }
            for a in node.assumptions
        ]

    return result


def compute_intervention_attribution(
    baseline_value: float,
    individual_effects: dict[str, float],
    combined_value: float,
) -> AttributionResult:
    """Decompose the combined effect into per-intervention contributions.

    Uses additive decomposition with interaction term.
    """
    total_delta = combined_value - baseline_value
    per_intervention = {name: val - baseline_value for name, val in individual_effects.items()}
    sum_individual = sum(per_intervention.values())
    interaction = total_delta - sum_individual

    return AttributionResult(
        total_delta=total_delta,
        per_intervention=per_intervention,
        interaction_effect=interaction,
    )


def generate_provenance_report(
    graph: SimulationGraph,
    provenance: list[ProvenanceRecord],
    target_node: str,
    year: int | None = None,
) -> str:
    """Generate a human-readable provenance report for a node.

    Returns Markdown-formatted report with:
    - Node description and value
    - Input chain with data sources
    - Assumptions and confidence levels
    - Top uncertainty drivers (if available)
    """
    chain = trace_provenance_backward(graph, target_node, provenance)
    node = graph.nodes.get(target_node)

    lines = []
    lines.append(f"# Provenance Report: {target_node}")
    if year is not None:
        lines.append(f"**Year:** {year}")
    lines.append("")

    if node:
        lines.append(f"**Node Type:** {node.node_type.value}")
        lines.append(f"**Tags:** {', '.join(node.tags) if node.tags else 'none'}")
        lines.append("")

    # Input chain
    lines.append("## Input Chain")
    for record in chain.chain:
        inputs_str = ", ".join(f"{k}" for k in record.inputs.keys()) if record.inputs else "none"
        temporal_str = (
            ", ".join(
                f"{k} (from {v.get('source_year', '?')})" for k, v in record.temporal_inputs.items()
            )
            if record.temporal_inputs
            else ""
        )
        fn_str = f" via `{record.compute_fn_name}`" if record.compute_fn_name else " (input)"
        lines.append(f"- **{record.node_name}**{fn_str}")
        if inputs_str != "none":
            lines.append(f"  - Inputs: {inputs_str}")
        if temporal_str:
            lines.append(f"  - Temporal inputs: {temporal_str}")
    lines.append("")

    # Data sources
    if chain.data_sources:
        lines.append("## Data Sources")
        for ds in chain.data_sources:
            lines.append(f"- **{ds.name}**")
            if ds.publication_date:
                lines.append(f"  - Published: {ds.publication_date}")
            if ds.url:
                lines.append(f"  - Source: {ds.url}")
            if ds.transformations:
                lines.append(f"  - Transformations: {ds.transformations}")
        lines.append("")

    # Assumptions
    if chain.assumptions:
        lines.append("## Assumptions")
        for node_name, assumption in chain.assumptions:
            lines.append(f"- **{node_name}**: {assumption.description}")
            lines.append(f"  - Rationale: {assumption.rationale}")
            lines.append(f"  - Confidence: {assumption.confidence}")
        lines.append("")

    return "\n".join(lines)
