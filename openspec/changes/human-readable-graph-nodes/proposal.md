## Why

The graph explorer displays raw Python identifiers (e.g. `post_scrappage`, `gas_ghg_per_gallon`) as node labels. The target audience is industry decision-makers and policymakers who don't think in snake_case. Nodes need human-readable display names and plain-English descriptions that explain what each variable represents and how it's calculated from its upstream dependencies.

## What Changes

- Add `display_name` and `description` fields to the `Node` dataclass in `core/node.py`
- Populate display names and descriptions inline on all 26 nodes in `fleet_nodes.py` and `emissions_nodes.py`
- Extend the `/graph/nodes` and `/graph/nodes/{name}` API endpoints to include the new fields
- Update the frontend `GraphNode` type and `GraphPage` to show display names on nodes and descriptions in the detail panel
- Descriptions for compute nodes reference upstream nodes by their display names (e.g. "Applies **Survival Curves** to the **Aged Fleet**")

## Capabilities

### New Capabilities
- `node-metadata`: Human-readable display names and descriptions on DAG nodes, served via API and rendered in the graph explorer

### Modified Capabilities

## Impact

- **Backend**: `core/node.py` (Node dataclass), `domain/fleet_nodes.py`, `domain/emissions_nodes.py`, `app/api.py` (graph endpoints)
- **Frontend**: `types/index.ts` (GraphNode interface), `pages/GraphPage.tsx` (node labels + detail panel)
- **No breaking changes**: `display_name` and `description` are optional fields; existing API consumers see new fields but nothing removed
