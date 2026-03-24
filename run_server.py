"""Start CarbonSight API with initialized simulation graph."""
import os
from pathlib import Path

import uvicorn

from carbonsight.app.api import app, set_graph, seed_demo_scenarios, run_scenario_by_name
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

# Seed and pre-run standard scenarios
seed_demo_scenarios()
for name in ["baseline", "ev-grid-intervention"]:
    run_scenario_by_name(name)
    print(f"Pre-ran scenario: {name}")


# Serve frontend static files if built (production / Docker)
static_dir = Path(__file__).parent / "static"
if static_dir.is_dir():
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        """Serve the SPA frontend — fall back to index.html for client-side routing."""
        file = static_dir / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(static_dir / "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
