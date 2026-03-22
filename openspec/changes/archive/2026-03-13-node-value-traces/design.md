## Context

CarbonSight runs 10-year fleet simulations producing year-by-year outputs for ~23 graph nodes. Run results are stored in `_results_store` (in-memory dict keyed by scenario name) as `SimulationResult` objects containing `YearResult` entries with `outputs: dict[str, Any]`. Node outputs are either scalar (`float`) or dict-valued (e.g., `total_emissions` has sub-fields `total_ghg`, `production_ghg`, `usage_ghg_total`, `disposal_ghg`).

The frontend has two relevant pages:

- **ScenariosPage**: manages scenario CRUD and execution, holds `RunResult` in component state after a run
- **GraphPage**: visualizes the DAG with a detail panel for selected nodes, currently shows metadata only (type, tags, data source, assumptions, connections)

Neither page currently supports viewing a node's values across simulation years.

## Goals / Non-Goals

**Goals:**

- View any node's year-by-year values as a line chart after running a scenario
- Support dict-valued nodes via sub-field dropdown selection
- On ScenariosPage: client-side extraction from existing RunResult (no extra API call)
- On GraphPage: fetch traces via API, overlay multiple scenarios on one chart
- Shared `<NodeTraceChart>` component for consistent rendering

**Non-Goals:**

- UQ uncertainty bands on traces (future enhancement)
- Editing or overriding node values from the trace view
- Persisting run results to disk (remains in-memory)
- Real-time streaming of trace data during simulation

## Decisions

### 1. Hybrid data source strategy (client-side + API endpoint)

**Choice:** ScenariosPage extracts traces client-side from `RunResult.outputs`; GraphPage fetches via a new `GET /scenarios/{name}/trace/{node_name}` endpoint.

**Alternatives considered:**

- _API-only_: Simpler code but redundant for ScenariosPage which already holds the data
- _Client-only_: Would require GraphPage to fetch and store full run results for potentially many scenarios

**Rationale:** Each page gets data the most natural way. ScenariosPage avoids a round-trip; GraphPage stays lightweight by fetching only what's needed.

### 2. Trace endpoint response shape

**Choice:** Return `years`, `values` (first field or scalar), `fields` (list of sub-field names or null), and `field_values` (dict of field → values array).

**Rationale:** A single request returns everything needed to populate the sub-field dropdown and chart. No need for a separate "list fields" call. The `values` default gives an immediate chart without requiring field selection.

### 3. Shared component with external field control

**Choice:** `<NodeTraceChart>` accepts pre-extracted `traces` array and renders lines. Sub-field dropdown lives in the parent page, not the component.

**Rationale:** Keeps the chart component pure and reusable. ScenariosPage and GraphPage have different data sources (local state vs. API response), so field extraction logic belongs in each parent.

### 4. Multi-scenario overlay on GraphPage only

**Choice:** GraphPage supports selecting multiple scenarios to overlay on the same trace chart. ScenariosPage shows only the current scenario's trace.

**Rationale:** ScenariosPage is focused on a single scenario's lifecycle (configure → run → inspect). Cross-scenario comparison is the GraphPage's and ComparePage's domain.

## Risks / Trade-offs

- **In-memory result store** → If the server restarts, all traces are lost. This is a known limitation of the current architecture, not introduced by this change. Mitigation: not applicable here, addressed separately.
- **Large dict-valued nodes** → `field_values` returns all sub-fields in one response. For nodes with many fields this could be verbose. Mitigation: current nodes have at most ~6 sub-fields; acceptable for now.
- **GraphPage scenario list** → Need to know which scenarios have been run. Mitigation: attempt the trace fetch and handle 404 gracefully with a user-friendly message.
