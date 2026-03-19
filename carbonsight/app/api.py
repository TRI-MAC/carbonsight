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
from carbonsight.core.scenario import InterventionSpec, Scenario, ScenarioStore, resolve_interventions, resolve_year_overrides
from carbonsight.domain.interventions import InterventionCategory

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

class InterventionSpecModel(BaseModel):
    type: str
    params: dict[str, Any] = {}


class ScenarioCreate(BaseModel):
    name: str
    overrides: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    interventions: list[InterventionSpecModel] = []


class ScenarioUpdate(BaseModel):
    overrides: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    interventions: list[InterventionSpecModel] | None = None


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


# --- Intervention Catalog ---

INTERVENTION_CATALOG = [
    {
        "type": "carbon_pricing",
        "category": InterventionCategory.POLICY.value,
        "description": "Carbon price applied to fuel costs",
        "params": [
            {"name": "price_per_tonne", "type": "float", "default": 50, "min": 10, "max": 500},
            {"name": "start_year", "type": "int", "default": 2024, "min": 2024, "max": 2034},
        ],
    },
    {
        "type": "ev_subsidy",
        "category": InterventionCategory.POLICY.value,
        "description": "EV purchase subsidy shifting powertrain mix",
        "params": [
            {"name": "proportion_shift", "type": "dict", "default": {"bev": 0.15}, "min": None, "max": None},
        ],
    },
    {
        "type": "vmt_reduction",
        "category": InterventionCategory.BEHAVIORAL.value,
        "description": "Reduce vehicle miles traveled",
        "params": [
            {"name": "factor", "type": "float", "default": 0.9, "min": 0.5, "max": 1.0},
        ],
    },
    {
        "type": "grid_decarbonization",
        "category": InterventionCategory.GRID_ENERGY.value,
        "description": "Grid carbon intensity trajectory override",
        "params": [
            {"name": "trajectory", "type": "dict", "default": {}, "min": None, "max": None},
        ],
    },
    {
        "type": "battery_cost_reduction",
        "category": InterventionCategory.TECHNOLOGY.value,
        "description": "Battery production emissions trajectory",
        "params": [
            {"name": "trajectory", "type": "dict", "default": {}, "min": None, "max": None},
        ],
    },
    {
        "type": "scrappage_program",
        "category": InterventionCategory.POLICY.value,
        "description": "Accelerated scrappage for old vehicles",
        "params": [
            {"name": "age_threshold", "type": "int", "default": 15, "min": 5, "max": 25},
            {"name": "acceleration_factor", "type": "float", "default": 2.0, "min": 1.1, "max": 5.0},
            {"name": "duration_years", "type": "int", "default": 3, "min": 1, "max": 10},
            {"name": "start_year", "type": "int", "default": 0, "min": 0, "max": 2034},
        ],
    },
    {
        "type": "phev_charging_improvement",
        "category": InterventionCategory.BEHAVIORAL.value,
        "description": "Improve PHEV charging behavior",
        "params": [
            {"name": "charging_factor", "type": "float", "default": 0.85, "min": 0.5, "max": 1.0},
        ],
    },
]


@app.get("/interventions")
def list_interventions():
    return INTERVENTION_CATALOG


# --- Dashboard ---

_dashboard_cache: dict[str, Any] | None = None
_demo_cache: dict[str, Any] | None = None


def seed_demo_scenarios():
    """Create pre-configured demo scenarios in the store."""
    if "baseline" not in scenario_store.list():
        scenario_store.create(Scenario(
            name="baseline",
            overrides={},
            metadata={"description": "Default baseline scenario"},
        ))
    if "ev-grid-intervention" not in scenario_store.list():
        scenario_store.create(Scenario(
            name="ev-grid-intervention",
            overrides={},
            metadata={"description": "EV subsidy + grid decarbonization"},
            interventions=[
                InterventionSpec(type="ev_subsidy", params={"proportion_shift": {"bev": 0.15}}),
                InterventionSpec(type="grid_decarbonization", params={
                    "trajectory": {str(2024 + i): 0.369 * (1 - 0.05 * i) for i in range(10)},
                }),
            ],
        ))


def run_scenario_by_name(name: str):
    """Run a scenario by name and store the result. For use at startup."""
    scenario = scenario_store.get(name)
    graph = get_graph()
    config = SimulationConfig(
        start_year=2024,
        num_years=10,
        execution_mode=ExecutionMode.DETERMINISTIC,
    )
    year_overrides = None
    if scenario.interventions:
        intervention_objs = resolve_interventions(scenario.interventions)
        year_overrides = resolve_year_overrides(
            intervention_objs, list(range(2024, 2034))
        )
    engine = SimulationEngine(graph, config)
    result = engine.run(overrides=scenario.overrides, mode=ExecutionMode.DETERMINISTIC, year_overrides=year_overrides)
    _results_store[name] = result


@app.get("/demo")
def get_demo():
    """Run curated baseline + intervention and return combined comparison data."""
    global _demo_cache
    if _demo_cache is not None:
        return _demo_cache

    graph = get_graph()
    config = SimulationConfig(
        start_year=2024,
        num_years=10,
        execution_mode=ExecutionMode.DETERMINISTIC,
    )

    # Run baseline
    engine_b = SimulationEngine(graph, config)
    baseline_result = engine_b.run(mode=ExecutionMode.DETERMINISTIC)

    # Run intervention: EV subsidy (15% BEV shift) + grid decarbonization (~50% over 10 years)
    intervention_overrides = {"powertrain_preference_shift": 2.14}  # shifts 7% BEV -> ~15%
    grid_trajectory = {str(2024 + i): 0.369 * (1 - 0.05 * i) for i in range(10)}
    year_overrides = {}
    for i in range(10):
        yr = 2024 + i
        year_overrides[yr] = {"grid_ghg_per_kwh": grid_trajectory[str(yr)]}

    engine_i = SimulationEngine(graph, config)
    intervention_result = engine_i.run(
        overrides=intervention_overrides,
        mode=ExecutionMode.DETERMINISTIC,
        year_overrides=year_overrides,
    )

    def _extract_trajectory(result):
        trajectory = []
        composition = []
        for yr in result.year_results:
            te = yr.outputs.get("total_emissions", {})
            if isinstance(te, dict):
                trajectory.append({
                    "year": yr.year,
                    "ghg": round(te.get("total_ghg", 0) / 1e9, 2),
                    "production": round(te.get("production_ghg", 0) / 1e9, 2),
                    "usage": round(te.get("usage_ghg_total", 0) / 1e9, 2),
                    "disposal": round(te.get("disposal_ghg", 0) / 1e9, 2),
                })
            fs = yr.outputs.get("fleet_snapshot", {})
            if isinstance(fs, dict):
                total = fs.get("total_vehicles", 1)
                by_pt = fs.get("by_powertrain", {})
                if isinstance(by_pt, dict) and isinstance(total, (int, float)) and total > 0:
                    composition.append({
                        "year": yr.year,
                        "total_vehicles": round(float(total)),
                        "ICEV": round(float(by_pt.get("icev", 0)) / float(total) * 100, 2),
                        "HEV": round(float(by_pt.get("hev", 0)) / float(total) * 100, 2),
                        "PHEV": round(float(by_pt.get("phev", 0)) / float(total) * 100, 2),
                        "BEV": round(float(by_pt.get("bev", 0)) / float(total) * 100, 2),
                    })
        return trajectory, composition

    b_traj, b_comp = _extract_trajectory(baseline_result)
    i_traj, i_comp = _extract_trajectory(intervention_result)

    # Compute deltas
    deltas = []
    cumulative_avoided = 0.0
    for bt, it in zip(b_traj, i_traj):
        diff = it["ghg"] - bt["ghg"]
        pct = (diff / bt["ghg"] * 100) if bt["ghg"] != 0 else 0
        cumulative_avoided += abs(diff)
        deltas.append({
            "year": bt["year"],
            "baseline_ghg": bt["ghg"],
            "intervention_ghg": it["ghg"],
            "absolute_delta": round(diff, 2),
            "percentage_delta": round(pct, 2),
        })

    _demo_cache = {
        "baseline": {"trajectory": b_traj, "composition": b_comp},
        "intervention": {"trajectory": i_traj, "composition": i_comp},
        "deltas": deltas,
        "cumulative_avoided_mt": round(cumulative_avoided, 2),
        "intervention_description": {
            "name": "EV Subsidy + Grid Decarbonization",
            "components": [
                {"type": "ev_subsidy", "description": "15% BEV proportion shift in new vehicle sales"},
                {"type": "grid_decarbonization", "description": "Grid carbon intensity declining ~50% by 2033"},
            ],
        },
        "wall_clock_seconds": round(
            baseline_result.wall_clock_seconds + intervention_result.wall_clock_seconds, 2
        ),
    }
    return _demo_cache


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
    interventions = [
        InterventionSpec(type=i.type, params=i.params)
        for i in body.interventions
    ]
    scenario = Scenario(
        name=body.name, overrides=body.overrides, metadata=body.metadata,
        interventions=interventions,
    )
    try:
        scenario_store.create(scenario)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"name": scenario.name, "overrides": scenario.overrides, "interventions": [{"type": i.type, "params": i.params} for i in scenario.interventions]}


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
    if body.interventions is not None:
        scenario.interventions = [
            InterventionSpec(type=i.type, params=i.params)
            for i in body.interventions
        ]
    return {"name": scenario.name, "overrides": scenario.overrides, "interventions": [{"type": i.type, "params": i.params} for i in scenario.interventions]}


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

    # Resolve interventions to year_overrides
    year_overrides = None
    if scenario.interventions:
        try:
            intervention_objs = resolve_interventions(scenario.interventions)
            year_overrides = resolve_year_overrides(
                intervention_objs, list(range(body.start_year, body.start_year + body.num_years))
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    engine = SimulationEngine(graph, config)
    result = engine.run(overrides=scenario.overrides, mode=mode, year_overrides=year_overrides)

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
            "display_name": node.display_name,
            "description": node.description,
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
        "display_name": node.display_name,
        "description": node.description,
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

    # Skip DataFrame-valued nodes (not reducible to a simple timeseries)
    import pandas as pd
    sample = raw_values[0] if raw_values else None
    if isinstance(sample, pd.DataFrame):
        raise HTTPException(
            status_code=422,
            detail=f"Node '{node_name}' produces DataFrame values; trace not supported.",
        )

    # Determine if scalar or dict-valued
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
        def _scalar(v, yi):
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, list):
                idx = min(yi, len(v) - 1)
                return float(v[idx]) if v else 0.0
            return 0.0

        values = [_scalar(v, i) for i, v in enumerate(raw_values)]

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
    from carbonsight.analysis.uncertainty import compute_sobol_indices, identify_top_drivers

    result = _results_store.get(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No results for '{name}'")

    if result.execution_mode != ExecutionMode.UQ:
        raise HTTPException(
            status_code=400,
            detail="Sensitivity analysis requires UQ mode results",
        )

    # Collect input samples and output samples from UQ results
    last_year = result.year_results[-1]
    input_samples: dict[str, Any] = {}
    output_samples = None

    for node_name, value in last_year.outputs.items():
        if isinstance(value, dict) and "samples" in value:
            import numpy as np
            samples = np.asarray(value["samples"])
            if output_samples is None:
                output_samples = samples
            input_samples[node_name] = samples

    if output_samples is None or len(input_samples) < 2:
        return {
            "scenario": name,
            "drivers": [],
            "message": "Insufficient sample data for sensitivity analysis",
        }

    sensitivity = compute_sobol_indices(input_samples, output_samples)
    drivers = identify_top_drivers(sensitivity, top_n=10)

    return {
        "scenario": name,
        "drivers": [
            {
                "input_node": d.input_node,
                "total_order_index": round(d.total_order_index, 4),
                "first_order_index": round(d.first_order_index, 4),
            }
            for d in drivers
        ],
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
