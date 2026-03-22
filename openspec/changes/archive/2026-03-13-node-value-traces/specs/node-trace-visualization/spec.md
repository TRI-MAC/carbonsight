## ADDED Requirements

### Requirement: Shared NodeTraceChart component

The system SHALL provide a `<NodeTraceChart>` component that renders a recharts LineChart displaying node value traces over simulation years.

#### Scenario: Single scenario trace

- **WHEN** the component receives one trace with `scenario: "Baseline"`, `years: [2024..2033]`, and `values: [...]`
- **THEN** it SHALL render a single line with no legend, using the existing dark theme tooltip styling

#### Scenario: Multi-scenario overlay

- **WHEN** the component receives multiple traces with different scenario names
- **THEN** it SHALL render one line per scenario using distinct colors from the chart palette, with a legend showing scenario names

#### Scenario: Empty traces

- **WHEN** the component receives an empty traces array
- **THEN** it SHALL render a message "No trace data available"

### Requirement: ScenariosPage node trace integration

After a scenario run completes, the ScenariosPage SHALL display a list of output node names and a trace chart for the selected node.

#### Scenario: Node list after run

- **WHEN** a scenario run completes successfully
- **THEN** the page SHALL display a scrollable list of node names extracted from the run result outputs

#### Scenario: Selecting a node shows trace

- **WHEN** the user clicks a node name in the list
- **THEN** the page SHALL render the `<NodeTraceChart>` showing that node's values across all simulation years, extracted client-side from the RunResult

#### Scenario: Sub-field dropdown for dict nodes

- **WHEN** the selected node's output is a dict (has sub-fields)
- **THEN** the page SHALL display a dropdown listing available sub-fields, defaulting to the first field, and update the chart when a different field is selected

### Requirement: GraphPage node trace integration

The GraphPage detail panel SHALL include a "Value Trace" section that fetches and displays node traces via the trace endpoint.

#### Scenario: Trace section in detail panel

- **WHEN** a user clicks a node in the graph
- **THEN** the detail panel SHALL include a "Value Trace" section below the existing connection lists

#### Scenario: Scenario multi-select

- **WHEN** the "Value Trace" section is visible
- **THEN** it SHALL display a multi-select control for choosing which completed scenarios to overlay on the chart

#### Scenario: Fetching and displaying traces

- **WHEN** the user selects one or more scenarios for a node
- **THEN** the page SHALL fetch traces via `api.getTrace()` for each selected scenario and render them as overlaid lines on the `<NodeTraceChart>`

#### Scenario: Sub-field dropdown for dict nodes on GraphPage

- **WHEN** the trace response includes `fields` (non-null)
- **THEN** the page SHALL display a sub-field dropdown and re-render the chart when the selection changes

#### Scenario: No scenarios run yet

- **WHEN** no scenarios have been run (all trace fetches return 404)
- **THEN** the section SHALL display "Run a scenario to see value traces"
