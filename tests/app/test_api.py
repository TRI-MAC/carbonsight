"""Integration tests for the CarbonSight API."""

import pytest
from fastapi.testclient import TestClient

from carbonsight.app.api import app, scenario_store, set_graph, _results_store
from carbonsight.core.graph import SimulationGraph
from carbonsight.core.node import Node, NodeType


@pytest.fixture(autouse=True)
def reset_state():
    """Reset API state between tests."""
    scenario_store._scenarios.clear()
    _results_store.clear()

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
