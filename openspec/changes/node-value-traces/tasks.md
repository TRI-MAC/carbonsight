## 1. Backend — Trace Endpoint

- [x] 1.1 Add `GET /scenarios/{name}/trace/{node_name}` endpoint to `api.py` that extracts year-by-year values from `_results_store`, handles scalar vs dict-valued nodes, returns `scenario`, `node`, `years`, `values`, `fields`, `field_values`
- [x] 1.2 Return 404 if scenario has no stored results or node not found in outputs
- [x] 1.3 Add backend test for trace endpoint (scalar node, dict node, 404 cases)

## 2. Frontend Types and API Client

- [x] 2.1 Add `TraceResponse` interface to `types/index.ts`
- [x] 2.2 Add `api.getTrace(scenario, nodeName)` method to `api/client.ts`

## 3. Shared Component

- [x] 3.1 Create `components/NodeTraceChart.tsx` — recharts LineChart accepting `traces` array, `nodeName`, optional `fieldName`; single line without legend, multi-line with legend, dark theme styling
- [x] 3.2 Add test for NodeTraceChart (single trace, multi-trace, empty state)

## 4. ScenariosPage Integration

- [x] 4.1 Add node list card below run summary showing all output node names from RunResult
- [x] 4.2 On node click, extract year-by-year values client-side and render NodeTraceChart
- [x] 4.3 Add sub-field dropdown for dict-valued nodes, defaulting to first field
- [x] 4.4 Update ScenariosPage test to verify node list and trace chart render after run

## 5. GraphPage Integration

- [x] 5.1 Add "Value Trace" section to the detail panel below upstream/downstream connections
- [x] 5.2 Add scenario multi-select control (populated by attempting trace fetches, handling 404)
- [x] 5.3 Fetch traces via `api.getTrace()` for selected scenarios, render overlaid on NodeTraceChart
- [x] 5.4 Add sub-field dropdown when trace response includes fields
- [x] 5.5 Show "Run a scenario to see value traces" when no scenarios have results
- [x] 5.6 Update GraphPage test to verify trace section renders in detail panel
