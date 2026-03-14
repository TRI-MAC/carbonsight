"""FastAPI application for CarbonSight.

Provides REST endpoints for scenario management, simulation execution,
comparison, graph introspection, provenance queries, and data export.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from carbonsight.core.engine import ExecutionMode, SimulationConfig, SimulationEngine
from carbonsight.core.graph import SimulationGraph
from carbonsight.core.node import Node, NodeType
from carbonsight.core.scenario import Scenario, ScenarioStore

app = FastAPI(
    title="CarbonSight API",
    description="Fleet carbon simulation with counterfactual interventions",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stores (replace with persistent storage for production)
scenario_store = ScenarioStore()
_graph: SimulationGraph | None = None
_results_store: dict[str, Any] = {}


def get_graph() -> SimulationGraph:
    """Get the current simulation graph. Must be initialized before use."""
    if _graph is None:
        raise HTTPException(status_code=503, detail="Simulation graph not initialized")
    return _graph


def set_graph(graph: SimulationGraph):
    """Set the simulation graph for the API to use."""
    global _graph
    _graph = graph


# --- Request/Response Models ---

class ScenarioCreate(BaseModel):
    name: str
    overrides: dict[str, Any] = {}
    metadata: dict[str, Any] = {}


class ScenarioUpdate(BaseModel):
    overrides: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class RunRequest(BaseModel):
    mode: str = "deterministic"  # "deterministic" or "uq"
    num_years: int = 10
    start_year: int = 2024
    uq_samples: int = 200


class CompareRequest(BaseModel):
    baseline_name: str
    intervention_names: list[str]


# --- Health Check ---

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


# --- Dashboard ---

_dashboard_cache: dict[str, Any] | None = None


@app.get("/dashboard")
def get_dashboard():
    """Run a baseline simulation and return dashboard summary data."""
    global _dashboard_cache
    if _dashboard_cache is not None:
        return _dashboard_cache

    graph = get_graph()
    config = SimulationConfig(
        start_year=2024,
        num_years=10,
        execution_mode=ExecutionMode.DETERMINISTIC,
    )
    engine = SimulationEngine(graph, config)
    result = engine.run(mode=ExecutionMode.DETERMINISTIC)

    trajectory = []
    composition = []
    for yr in result.year_results:
        # Emissions trajectory
        te = yr.outputs.get("total_emissions", {})
        if isinstance(te, dict):
            total_ghg = te.get("total_ghg", 0)
            trajectory.append({
                "year": yr.year,
                "ghg": round(total_ghg / 1e9, 2),  # Convert to Mt CO2e
                "production": round(te.get("production_ghg", 0) / 1e9, 2),
                "usage": round(te.get("usage_ghg_total", 0) / 1e9, 2),
                "disposal": round(te.get("disposal_ghg", 0) / 1e9, 2),
            })

        # Fleet composition
        fs = yr.outputs.get("fleet_snapshot", {})
        if isinstance(fs, dict):
            total = fs.get("total_vehicles", 1)
            by_pt = fs.get("by_powertrain", {})
            if isinstance(by_pt, dict) and isinstance(total, (int, float)) and total > 0:
                composition.append({
                    "year": yr.year,
                    "total_vehicles": round(float(total)),
                    "total_vmt": round(float(fs.get("total_vmt", 0))),
                    "ICEV": round(float(by_pt.get("icev", 0)) / float(total) * 100, 2),
                    "HEV": round(float(by_pt.get("hev", 0)) / float(total) * 100, 2),
                    "PHEV": round(float(by_pt.get("phev", 0)) / float(total) * 100, 2),
                    "BEV": round(float(by_pt.get("bev", 0)) / float(total) * 100, 2),
                })

    # Current metrics from first year
    first_comp = composition[0] if composition else {}
    last_comp = composition[-1] if composition else {}
    first_traj = trajectory[0] if trajectory else {}

    _dashboard_cache = {
        "metrics": {
            "fleet_size": first_comp.get("total_vehicles", 0),
            "annual_ghg": first_traj.get("ghg", 0),
            "bev_share": first_comp.get("BEV", 0),
            "bev_share_final": last_comp.get("BEV", 0),
            "total_vmt": first_comp.get("total_vmt", 0),
        },
        "trajectory": trajectory,
        "composition": composition,
        "wall_clock_seconds": result.wall_clock_seconds,
    }
    return _dashboard_cache


# --- Scenario CRUD ---

@app.post("/scenarios", status_code=201)
def create_scenario(body: ScenarioCreate):
    scenario = Scenario(
        name=body.name, overrides=body.overrides, metadata=body.metadata
    )
    try:
        scenario_store.create(scenario)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"name": scenario.name, "overrides": scenario.overrides}


@app.get("/scenarios")
def list_scenarios():
    names = scenario_store.list()
    return [
        {"name": n, "overrides": scenario_store.get(n).overrides, "metadata": scenario_store.get(n).metadata}
        for n in names
    ]


@app.get("/scenarios/{name}")
def get_scenario(name: str):
    try:
        scenario = scenario_store.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    return {"name": scenario.name, "overrides": scenario.overrides, "metadata": scenario.metadata}


@app.put("/scenarios/{name}")
def update_scenario(name: str, body: ScenarioUpdate):
    try:
        scenario = scenario_store.update(
            name, overrides=body.overrides, metadata=body.metadata
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    return {"name": scenario.name, "overrides": scenario.overrides}


@app.delete("/scenarios/{name}", status_code=204)
def delete_scenario(name: str):
    try:
        scenario_store.delete(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")


# --- Simulation Execution ---

@app.post("/scenarios/{name}/run")
def run_scenario(name: str, body: RunRequest):
    try:
        scenario = scenario_store.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")

    graph = get_graph()
    mode = ExecutionMode.UQ if body.mode == "uq" else ExecutionMode.DETERMINISTIC

    config = SimulationConfig(
        start_year=body.start_year,
        num_years=body.num_years,
        execution_mode=mode,
        uq_samples=body.uq_samples,
    )

    engine = SimulationEngine(graph, config)
    result = engine.run(overrides=scenario.overrides, mode=mode)

    # Store result for later retrieval
    _results_store[name] = result

    # Serialize result summary
    summary = {
        "scenario": name,
        "mode": mode.value,
        "years": result.years,
        "wall_clock_seconds": result.wall_clock_seconds,
        "performance_warning": result.performance_warning,
        "outputs": {},
    }

    for yr in result.year_results:
        year_outputs = {}
        for node_name, value in yr.outputs.items():
            if isinstance(value, (int, float, str, bool)):
                year_outputs[node_name] = value
            elif isinstance(value, dict):
                # Filter out numpy arrays for JSON serialization
                year_outputs[node_name] = {
                    k: v for k, v in value.items()
                    if isinstance(v, (int, float, str, bool, list, dict))
                }
        summary["outputs"][yr.year] = year_outputs

    return summary


# --- Scenario Comparison ---

@app.post("/compare")
def compare_scenarios(body: CompareRequest):
    from carbonsight.core.scenario import compare_scenarios

    baseline_result = _results_store.get(body.baseline_name)
    if baseline_result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No results for baseline '{body.baseline_name}'. Run it first.",
        )

    comparisons = {}
    for int_name in body.intervention_names:
        int_result = _results_store.get(int_name)
        if int_result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No results for intervention '{int_name}'. Run it first.",
            )
        comparison = compare_scenarios(baseline_result, int_result)
        comparisons[int_name] = {
            "deltas": [
                {
                    "node_name": d.node_name,
                    "year": d.year,
                    "absolute_delta": d.absolute_delta,
                    "percentage_delta": d.percentage_delta,
                }
                for d in comparison.deltas
            ]
        }

    return {"baseline": body.baseline_name, "comparisons": comparisons}


# --- Graph Introspection ---

@app.get("/graph/nodes")
def list_graph_nodes():
    graph = get_graph()
    nodes = []
    for name, node in graph.nodes.items():
        nodes.append({
            "name": name,
            "type": node.node_type.value,
            "is_input": node.is_input,
            "upstream": node.upstream_edges,
            "temporal": node.temporal_edges,
            "tags": node.tags,
        })
    return nodes


@app.get("/graph/nodes/{name}")
def get_graph_node(name: str):
    graph = get_graph()
    try:
        node = graph.get_node(name)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Node '{name}' not found")

    result: dict[str, Any] = {
        "name": node.name,
        "type": node.node_type.value,
        "is_input": node.is_input,
        "upstream": node.upstream_edges,
        "temporal": node.temporal_edges,
        "tags": node.tags,
    }

    if node.data_source:
        result["data_source"] = {
            "name": node.data_source.name,
            "publication_date": node.data_source.publication_date,
            "url": node.data_source.url,
        }

    if node.assumptions:
        result["assumptions"] = [
            {"description": a.description, "rationale": a.rationale, "confidence": a.confidence}
            for a in node.assumptions
        ]

    return result


# --- Provenance ---

@app.get("/scenarios/{name}/provenance/{node_name}")
def get_provenance(name: str, node_name: str):
    from carbonsight.analysis.explainability import generate_provenance_report

    result = _results_store.get(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No results for '{name}'")

    graph = get_graph()

    # Use provenance from the last year
    last_year = result.year_results[-1]
    report = generate_provenance_report(
        graph, last_year.provenance, node_name, year=last_year.year
    )

    return {"scenario": name, "node": node_name, "report": report}


# --- Node Trace ---

@app.get("/scenarios/{name}/trace/{node_name}")
def get_node_trace(name: str, node_name: str):
    """Return year-by-year values for a single node from a completed run."""
    result = _results_store.get(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No results for '{name}'. Run it first.")

    # Check node exists in outputs
    first_year = result.year_results[0] if result.year_results else None
    if first_year is None or node_name not in first_year.outputs:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{node_name}' not found in results for '{name}'",
        )

    years: list[int] = []
    raw_values: list[Any] = []
    for yr in result.year_results:
        if node_name in yr.outputs:
            years.append(yr.year)
            raw_values.append(yr.outputs[node_name])

    # Determine if scalar or dict-valued
    sample = raw_values[0] if raw_values else None
    if isinstance(sample, dict):
        fields = [k for k in sample.keys() if isinstance(sample[k], (int, float))]
        field_values = {
            field: [
                float(v.get(field, 0)) if isinstance(v, dict) else 0.0
                for v in raw_values
            ]
            for field in fields
        }
        values = field_values[fields[0]] if fields else []
    else:
        fields = None
        field_values = None
        values = [float(v) if isinstance(v, (int, float)) else 0.0 for v in raw_values]

    return {
        "scenario": name,
        "node": node_name,
        "years": years,
        "values": values,
        "fields": fields,
        "field_values": field_values,
    }


# --- Sensitivity ---

@app.get("/scenarios/{name}/sensitivity")
def get_sensitivity(name: str):
    result = _results_store.get(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No results for '{name}'")

    if result.execution_mode != ExecutionMode.UQ:
        raise HTTPException(
            status_code=400,
            detail="Sensitivity analysis requires UQ mode results",
        )

    return {
        "scenario": name,
        "note": "Full Sobol analysis available via the analysis.uncertainty module",
    }


# --- Export ---

@app.get("/scenarios/{name}/export")
def export_scenario(name: str, format: str = "yaml"):
    try:
        scenario = scenario_store.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")

    if format == "yaml":
        return {"format": "yaml", "content": scenario.to_yaml()}
    elif format == "json":
        return {"format": "json", "content": scenario.to_dict()}
    elif format == "csv":
        result = _results_store.get(name)
        if result is None:
            raise HTTPException(status_code=404, detail="Run the scenario first for CSV export")
        rows = []
        for yr in result.year_results:
            for node_name, value in yr.outputs.items():
                if isinstance(value, (int, float)):
                    rows.append({"year": yr.year, "node": node_name, "value": value})
        return {"format": "csv", "rows": rows}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
