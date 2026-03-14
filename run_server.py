"""Start CarbonSight API with initialized simulation graph."""
import uvicorn

from carbonsight.app.api import app, set_graph
from carbonsight.core.graph import SimulationGraph
from carbonsight.data.loaders import load_fleet_inventory, load_survival_curves, load_vmt_by_age
from carbonsight.domain.fleet_nodes import create_fleet_dynamics_nodes
from carbonsight.domain.emissions_nodes import create_emissions_nodes
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
print(f"Graph initialized: {len(graph.nodes)} nodes")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
