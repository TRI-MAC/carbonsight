## ADDED Requirements

### Requirement: Trace endpoint returns year-by-year node values
The system SHALL expose `GET /scenarios/{name}/trace/{node_name}` that returns the time series of a node's output values from a completed simulation run.

#### Scenario: Scalar node trace
- **WHEN** a scenario has been run and the client requests `/scenarios/Baseline/trace/fleet_snapshot`
- **THEN** the response SHALL include `scenario`, `node`, `years` (array of ints), `values` (array of numbers), and `fields` set to null

#### Scenario: Dict-valued node trace
- **WHEN** a scenario has been run and the client requests `/scenarios/Baseline/trace/total_emissions`
- **THEN** the response SHALL include `fields` (array of sub-field names), `field_values` (dict mapping each field name to an array of numbers), and `values` defaulting to the first field's values

#### Scenario: Scenario not yet run
- **WHEN** the client requests a trace for a scenario that has no stored results
- **THEN** the endpoint SHALL return HTTP 404 with detail message "No results for '{name}'. Run it first."

#### Scenario: Node not found in results
- **WHEN** the client requests a trace for a node name that does not exist in the run outputs
- **THEN** the endpoint SHALL return HTTP 404 with detail message "Node '{node_name}' not found in results for '{name}'"

### Requirement: API client exposes getTrace method
The frontend API client SHALL provide `api.getTrace(scenario: string, nodeName: string)` returning a typed `TraceResponse` matching the endpoint's response shape.

#### Scenario: Successful fetch
- **WHEN** the frontend calls `api.getTrace("Baseline", "total_emissions")`
- **THEN** it SHALL return a `TraceResponse` object with `scenario`, `node`, `years`, `values`, `fields`, and `field_values` properties

### Requirement: TraceResponse type definition
The frontend SHALL define a `TraceResponse` interface in `types/index.ts` with fields: `scenario: string`, `node: string`, `years: number[]`, `values: number[]`, `fields: string[] | null`, `field_values: Record<string, number[]> | null`.

#### Scenario: Type matches endpoint
- **WHEN** the trace endpoint returns a response
- **THEN** the response SHALL be assignable to the `TraceResponse` interface without type errors
