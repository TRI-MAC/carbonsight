"""Start CarbonSight in demo mode with pre-seeded scenarios.

Usage:
    python run_demo.py

This starts the FastAPI backend, seeds demo scenarios, and prints the demo URL.
For the frontend, start separately:
    cd frontend && npm run dev
Then navigate to http://localhost:5173/demo
"""
import uvicorn

from carbonsight.app.api import app, seed_demo_scenarios, set_graph
from carbonsight.core.graph import SimulationGraph
from carbonsight.data.loaders import load_fleet_inventory, load_survival_curves, load_vmt_by_age
from carbonsight.domain.emissions_nodes import create_emissions_nodes
from carbonsight.domain.fleet_nodes import create_fleet_dynamics_nodes
from carbonsight.domain.macro_drivers import create_macro_driver_nodes

# Build and register the simulation graph
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
seed_demo_scenarios()

print(f"Graph initialized: {len(graph.nodes)} nodes")
print("Demo scenarios seeded: baseline, ev-grid-intervention")
print()
print("API running at: http://localhost:8000")
print("Demo endpoint:  http://localhost:8000/demo")
print()
print("To start the frontend:")
print("  cd frontend && npm run dev")
print("Then open: http://localhost:5173/demo")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
