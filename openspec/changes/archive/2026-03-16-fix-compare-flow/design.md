## Context

The ComparePage and ScenariosPage were built with demo fallbacks but never fully connected to the live API for the comparison workflow. The trace endpoint (`GET /scenarios/{name}/trace/{node_name}`) already exists and returns year-by-year values for any node. The comparison endpoint (`POST /compare`) returns delta values but not full trajectories — so the trajectory chart needs trace data fetched separately.

Key files:

- `frontend/src/pages/ComparePage.tsx` — trajectory chart, delta table, scenario selection
- `frontend/src/pages/ScenariosPage.tsx` — intervention builder, scenario CRUD, run execution
- `frontend/src/api/client.ts` — `api.getTrace()` already exists
- `carbonsight/app/api.py` — trace endpoint at line 470, returns `TraceResponse`

## Goals / Non-Goals

**Goals:**

- Trajectory chart shows real data from completed runs
- Users can tell at a glance which scenarios are runnable/comparable
- Interventions created through the UI actually work when run

**Non-Goals:**

- New backend endpoints (everything needed already exists)
- Redesigning the Compare page layout
- Adding UQ confidence bands to the comparison chart (future work)

## Decisions

### 1. Fetch trace data per-scenario after comparison succeeds

**Decision**: After `api.compare()` succeeds, fetch `api.getTrace(name, "total_emissions")` for each selected scenario. Extract the `field_values.total_ghg` array (or `field_values.usage_ghg_total` etc.) for charting. This replaces the `generateDemoData()` call entirely.

**Rationale**: The trace endpoint already returns exactly the data we need. The comparison endpoint returns deltas (useful for the table) but not full trajectories. Fetching traces for 2-3 scenarios is fast (~50ms each since results are cached in memory).

**Alternative**: Add trajectory data to the comparison endpoint response — rejected because it would duplicate trace endpoint logic and the current approach works with no backend changes.

### 2. Probe run status via trace endpoint 404

**Decision**: For each scenario in the list, attempt `api.getTrace(name, "total_emissions")` and mark it as "ready" (200) or "not run" (404). Cache the result in component state.

**Rationale**: There's no dedicated "has been run" endpoint, but the trace endpoint returns 404 with a clear message for unrun scenarios. This avoids adding a new backend endpoint for a simple boolean check.

**Alternative**: Add `GET /scenarios/{name}/status` endpoint — rejected as over-engineering for this use case.

### 3. Use catalog param metadata for intervention spec building

**Decision**: Store the full `params` array from the intervention catalog alongside each category item. When building the intervention spec, use `params[0].name` as the key (not a hardcoded heuristic). For `ev_subsidy` which expects a dict param, special-case it based on `params[0].type === "dict"`.

**Rationale**: The catalog already describes the exact parameter schema. The current heuristic (`iv.name === "vmt_reduction" ? "factor" : "value"`) is wrong for 5 out of 7 intervention types.

## Risks / Trade-offs

- **[N+1 trace fetches]** Fetching traces for each scenario adds latency proportional to scenario count. → Acceptable for 2-4 scenarios; if we need 10+, add a batch endpoint later.
- **[Status probe on mount]** Checking run status for all scenarios on page load could be slow with many scenarios. → Limit to first 20; scenarios page already shows status.
