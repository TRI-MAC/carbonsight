## Context

The graph explorer renders DAG nodes using their Python identifiers (`post_scrappage`, `gas_ghg_per_gallon`). The `Node` dataclass in `core/node.py` has no fields for human-readable names or descriptions. The API endpoints at `/graph/nodes` serialize `name`, `type`, `is_input`, `upstream`, `temporal`, `tags`, `data_source`, and `assumptions` — but no display metadata.

The frontend `GraphPage.tsx` renders `gn.name` directly as the node label and uses `gn.name` in the detail panel header. The `GraphNode` TypeScript interface mirrors the API shape with no display fields.

There are 26 nodes total across `fleet_nodes.py` (17 nodes) and `emissions_nodes.py` (10 nodes), plus `year_index`.

## Goals / Non-Goals

**Goals:**
- Every DAG node has a human-readable display name and plain-English description
- Descriptions for compute nodes reference upstream dependencies by display name
- Metadata is defined inline on Node definitions (single source of truth)
- Graph explorer shows display names on nodes and descriptions in the detail panel
- API serves new fields so any future client can use them

**Non-Goals:**
- Internationalization / multi-language support
- User-editable node names or descriptions
- Clickable upstream references in descriptions (future enhancement)
- Changing internal node `name` identifiers (these remain snake_case for code compatibility)

## Decisions

### 1. Add `display_name` and `description` to the `Node` dataclass

Both fields are `str | None = None`, keeping them optional so tests and ad-hoc graph construction aren't burdened. When `display_name` is `None`, the frontend falls back to `name`.

**Alternative considered**: A separate metadata registry (dict or JSON file) mapping node names to display info. Rejected because it drifts from node definitions and adds a maintenance surface.

### 2. Descriptions reference upstream nodes by display name in bold

Compute node descriptions read like: "Applies **Survival Curves** to the **Aged Fleet** to probabilistically remove end-of-life vehicles." This is Markdown-flavored plain text — the frontend can render bold references, and a future enhancement could make them clickable.

**Alternative considered**: Reference by internal name with auto-substitution at render time. Rejected because it couples the frontend to a name-resolution step and makes descriptions harder to read in raw form (e.g., in API responses or logs).

### 3. API changes are additive only

The `/graph/nodes` list endpoint and `/graph/nodes/{name}` detail endpoint add `display_name` and `description` fields. No existing fields are removed or renamed. This is fully backward-compatible.

### 4. Frontend shows display name on nodes, internal name as subtitle

Node boxes show the display name prominently. The internal `name` moves to a secondary position (small, monospace, muted) so developers can still identify nodes for debugging. The detail panel header shows the display name, with internal name below it.

## Risks / Trade-offs

- **Description drift**: Descriptions reference upstream display names by text, not by ID. If a display name changes, descriptions mentioning it become stale. → Mitigation: All metadata is co-located in the same files (`fleet_nodes.py`, `emissions_nodes.py`), making it easy to grep and update together.
- **Description length**: Some compute nodes have many upstream dependencies, leading to longer descriptions. → Mitigation: Keep descriptions to 1-2 sentences; reference only the most important upstream nodes rather than exhaustively listing all inputs.
