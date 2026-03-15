"""Integration tests for the CarbonSight API."""

import pytest
from fastapi.testclient import TestClient

import carbonsight.app.api as api_module
from carbonsight.app.api import app, scenario_store, set_graph, _results_store, seed_demo_scenarios
from carbonsight.core.graph import SimulationGraph
from carbonsight.core.node import Node, NodeType


@pytest.fixture(autouse=True)
def reset_state():
    """Reset API state between tests."""
    scenario_store._scenarios.clear()
    _results_store.clear()
    api_module._dashboard_cache = None
    api_module._demo_cache = None

    # Set up a simple graph for testing
    graph = SimulationGraph()
    graph.add_node(Node(name="input_a", node_type=NodeType.SCALAR, value=10))
    graph.add_node(Node(name="input_b", node_type=NodeType.SCALAR, value=5))
    graph.add_node(Node(
        name="output",
        node_type=NodeType.SCALAR,
        compute_fn=lambda input_a, input_b: input_a * input_b,
    ))
    graph.validate()
    set_graph(graph)
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthCheck:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestScenarioCRUD:
    def test_create_scenario(self, client):
        response = client.post("/scenarios", json={
            "name": "baseline",
            "overrides": {"input_a": 20},
        })
        assert response.status_code == 201
        assert response.json()["name"] == "baseline"

    def test_create_duplicate_rejected(self, client):
        client.post("/scenarios", json={"name": "test"})
        response = client.post("/scenarios", json={"name": "test"})
        assert response.status_code == 409

    def test_list_scenarios(self, client):
        client.post("/scenarios", json={"name": "a"})
        client.post("/scenarios", json={"name": "b"})
        response = client.get("/scenarios")
        assert response.status_code == 200
        names = [s["name"] for s in response.json()]
        assert "a" in names
        assert "b" in names

    def test_get_scenario(self, client):
        client.post("/scenarios", json={"name": "test", "overrides": {"input_a": 15}})
        response = client.get("/scenarios/test")
        assert response.status_code == 200
        assert response.json()["overrides"]["input_a"] == 15

    def test_get_nonexistent(self, client):
        response = client.get("/scenarios/missing")
        assert response.status_code == 404

    def test_update_scenario(self, client):
        client.post("/scenarios", json={"name": "test"})
        response = client.put("/scenarios/test", json={"overrides": {"input_a": 99}})
        assert response.status_code == 200
        assert response.json()["overrides"]["input_a"] == 99

    def test_delete_scenario(self, client):
        client.post("/scenarios", json={"name": "test"})
        response = client.delete("/scenarios/test")
        assert response.status_code == 204
        response = client.get("/scenarios/test")
        assert response.status_code == 404


class TestSimulationExecution:
    def test_run_deterministic(self, client):
        client.post("/scenarios", json={"name": "baseline"})
        response = client.post("/scenarios/baseline/run", json={
            "mode": "deterministic", "num_years": 2,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "deterministic"
        assert len(data["years"]) == 2

    def test_run_with_overrides(self, client):
        client.post("/scenarios", json={
            "name": "override_test", "overrides": {"input_a": 100},
        })
        response = client.post("/scenarios/override_test/run", json={
            "mode": "deterministic", "num_years": 1,
        })
        assert response.status_code == 200
        data = response.json()
        # output = input_a * input_b = 100 * 5 = 500
        first_year = str(data["years"][0])
        assert data["outputs"][first_year]["output"] == 500

    def test_run_nonexistent_scenario(self, client):
        response = client.post("/scenarios/missing/run", json={"mode": "deterministic"})
        assert response.status_code == 404


class TestGraphIntrospection:
    def test_list_nodes(self, client):
        response = client.get("/graph/nodes")
        assert response.status_code == 200
        names = [n["name"] for n in response.json()]
        assert "input_a" in names
        assert "output" in names

    def test_get_node_detail(self, client):
        response = client.get("/graph/nodes/output")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "output"
        assert data["is_input"] is False

    def test_get_nonexistent_node(self, client):
        response = client.get("/graph/nodes/nonexistent")
        assert response.status_code == 404


class TestProvenance:
    def test_get_provenance(self, client):
        client.post("/scenarios", json={"name": "baseline"})
        client.post("/scenarios/baseline/run", json={"mode": "deterministic", "num_years": 1})
        response = client.get("/scenarios/baseline/provenance/output")
        assert response.status_code == 200
        assert "report" in response.json()

    def test_provenance_no_results(self, client):
        response = client.get("/scenarios/missing/provenance/output")
        assert response.status_code == 404


class TestNodeTrace:
    def test_trace_scalar_node(self, client):
        client.post("/scenarios", json={"name": "baseline"})
        client.post("/scenarios/baseline/run", json={"mode": "deterministic", "num_years": 3})
        response = client.get("/scenarios/baseline/trace/output")
        assert response.status_code == 200
        data = response.json()
        assert data["scenario"] == "baseline"
        assert data["node"] == "output"
        assert len(data["years"]) == 3
        assert len(data["values"]) == 3
        assert data["fields"] is None
        assert data["field_values"] is None

    def test_trace_no_results(self, client):
        response = client.get("/scenarios/missing/trace/output")
        assert response.status_code == 404
        assert "Run it first" in response.json()["detail"]

    def test_trace_node_not_found(self, client):
        client.post("/scenarios", json={"name": "baseline"})
        client.post("/scenarios/baseline/run", json={"mode": "deterministic", "num_years": 1})
        response = client.get("/scenarios/baseline/trace/nonexistent_node")
        assert response.status_code == 404
        assert "not found in results" in response.json()["detail"]


class TestInterventionCatalog:
    def test_list_interventions(self, client):
        response = client.get("/interventions")
        assert response.status_code == 200
        catalog = response.json()
        assert len(catalog) == 7
        types = [i["type"] for i in catalog]
        assert "carbon_pricing" in types
        assert "ev_subsidy" in types
        assert "vmt_reduction" in types
        for item in catalog:
            assert "category" in item
            assert "description" in item
            assert "params" in item

    def test_catalog_param_schemas(self, client):
        response = client.get("/interventions")
        catalog = response.json()
        carbon = next(i for i in catalog if i["type"] == "carbon_pricing")
        param_names = [p["name"] for p in carbon["params"]]
        assert "price_per_tonne" in param_names
        price_param = next(p for p in carbon["params"] if p["name"] == "price_per_tonne")
        assert price_param["type"] == "float"
        assert price_param["min"] == 10
        assert price_param["max"] == 500


class TestScenarioWithInterventions:
    def test_create_with_interventions(self, client):
        response = client.post("/scenarios", json={
            "name": "ev_push",
            "interventions": [{"type": "vmt_reduction", "params": {"factor": 0.9}}],
        })
        assert response.status_code == 201
        data = response.json()
        assert len(data["interventions"]) == 1
        assert data["interventions"][0]["type"] == "vmt_reduction"

    def test_update_with_interventions(self, client):
        client.post("/scenarios", json={"name": "test"})
        response = client.put("/scenarios/test", json={
            "interventions": [{"type": "carbon_pricing", "params": {"price_per_tonne": 100}}],
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["interventions"]) == 1
        assert data["interventions"][0]["type"] == "carbon_pricing"

    def test_run_with_interventions(self, client):
        client.post("/scenarios", json={
            "name": "test",
            "interventions": [{"type": "vmt_reduction", "params": {"factor": 0.9}}],
        })
        response = client.post("/scenarios/test/run", json={
            "mode": "deterministic", "num_years": 2,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["scenario"] == "test"
        assert len(data["years"]) == 2

    def test_run_with_invalid_intervention_type(self, client):
        client.post("/scenarios", json={
            "name": "bad",
            "interventions": [{"type": "nonexistent", "params": {}}],
        })
        response = client.post("/scenarios/bad/run", json={
            "mode": "deterministic", "num_years": 1,
        })
        assert response.status_code == 400
        assert "Unknown intervention type" in response.json()["detail"]


class TestDemo:
    @pytest.fixture(autouse=True)
    def _full_graph(self):
        """Demo endpoint requires the full simulation graph."""
        from carbonsight.core.graph import SimulationGraph
        from carbonsight.data.loaders import load_fleet_inventory, load_survival_curves, load_vmt_by_age
        from carbonsight.domain.fleet_nodes import create_fleet_dynamics_nodes
        from carbonsight.domain.emissions_nodes import create_emissions_nodes
        from carbonsight.domain.macro_drivers import create_macro_driver_nodes

        fleet = load_fleet_inventory()
        survival = load_survival_curves()
        vmt = load_vmt_by_age()
        graph = SimulationGraph()
        for n in create_fleet_dynamics_nodes(fleet, survival, vmt):
            graph.add_node(n)
        for n in create_emissions_nodes():
            graph.add_node(n)
        for n in create_macro_driver_nodes():
            graph.add_node(n)
        graph.validate()
        set_graph(graph)

    def test_demo_endpoint(self, client):
        response = client.get("/demo")
        assert response.status_code == 200
        data = response.json()
        assert "baseline" in data
        assert "intervention" in data
        assert "deltas" in data
        assert "cumulative_avoided_mt" in data
        assert "intervention_description" in data
        assert "wall_clock_seconds" in data
        assert len(data["baseline"]["trajectory"]) == 10
        assert len(data["intervention"]["trajectory"]) == 10
        assert len(data["deltas"]) == 10

    def test_demo_cached(self, client):
        r1 = client.get("/demo")
        r2 = client.get("/demo")
        assert r1.json() == r2.json()


class TestDemoSeeding:
    def test_seeded_scenarios_appear(self, client):
        seed_demo_scenarios()
        response = client.get("/scenarios")
        names = [s["name"] for s in response.json()]
        assert "baseline" in names
        assert "ev-grid-intervention" in names

    def test_seeding_idempotent(self, client):
        seed_demo_scenarios()
        seed_demo_scenarios()
        response = client.get("/scenarios")
        names = [s["name"] for s in response.json()]
        assert names.count("baseline") == 1
        assert names.count("ev-grid-intervention") == 1


class TestSensitivity:
    def test_sensitivity_requires_uq(self, client):
        client.post("/scenarios", json={"name": "test"})
        client.post("/scenarios/test/run", json={"mode": "deterministic", "num_years": 1})
        response = client.get("/scenarios/test/sensitivity")
        assert response.status_code == 400
        assert "UQ mode" in response.json()["detail"]

    def test_sensitivity_no_results(self, client):
        response = client.get("/scenarios/missing/sensitivity")
        assert response.status_code == 404


class TestExport:
    def test_export_yaml(self, client):
        client.post("/scenarios", json={"name": "test", "overrides": {"input_a": 10}})
        response = client.get("/scenarios/test/export?format=yaml")
        assert response.status_code == 200
        assert response.json()["format"] == "yaml"

    def test_export_json(self, client):
        client.post("/scenarios", json={"name": "test"})
        response = client.get("/scenarios/test/export?format=json")
        assert response.status_code == 200
        assert response.json()["format"] == "json"

    def test_export_unsupported_format(self, client):
        client.post("/scenarios", json={"name": "test"})
        response = client.get("/scenarios/test/export?format=xml")
        assert response.status_code == 400
