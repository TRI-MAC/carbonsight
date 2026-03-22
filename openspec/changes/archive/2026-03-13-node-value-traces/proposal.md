## Why

There is no way to inspect how individual graph node values evolve over a simulation's 10-year horizon. After running a scenario, users can only see aggregate metrics (fleet size, total GHG) and pre-built charts. Decision-makers need to drill into specific nodes — e.g., how does `usage_emissions` change year-over-year under a high EV adoption scenario vs. baseline — to understand causal drivers and validate model behavior.

## What Changes

- New backend endpoint `GET /scenarios/{name}/trace/{node_name}` returning year-by-year values for a single node, with sub-field support for dict-valued nodes
- New `api.getTrace()` method in the frontend API client
- New shared `<NodeTraceChart>` component rendering a recharts LineChart with multi-scenario overlay support
- ScenariosPage: node list and trace card below run results, with client-side extraction from existing `RunResult` (no API call needed)
- GraphPage: "Value Trace" section in the node detail panel, with scenario multi-select and sub-field dropdown, fetching via the trace endpoint

## Capabilities

### New Capabilities

- `node-trace-endpoint`: Backend endpoint returning per-node year-by-year time series with sub-field enumeration for dict-valued outputs
- `node-trace-visualization`: Shared frontend component and page integrations for viewing node value traces on both ScenariosPage and GraphPage

### Modified Capabilities

## Impact

- **Backend**: New endpoint in `app/api.py`, reads from existing `_results_store`
- **Frontend API client**: New `getTrace` method in `api/client.ts`, new `TraceResponse` type
- **Frontend components**: New `NodeTraceChart` component in `components/`
- **ScenariosPage**: Additional card/section after run results
- **GraphPage**: Additional section in detail panel
- **Tests**: New backend test for trace endpoint, frontend tests for component and page integrations
