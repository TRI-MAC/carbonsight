## ADDED Requirements

### Requirement: Provenance Recording During Graph Execution

The system SHALL record a provenance record for every node computation during graph execution. Each provenance record MUST include: the node identifier, the input values (or distribution parameters) received, the data source references for those inputs, the active assumptions, the compute function version or hash, the timestamp of computation, and the scenario identifier. Provenance records SHALL be stored as structured metadata alongside the ScenarioResult and MUST NOT be reconstructed after the fact.

#### Scenario: Record provenance for a single node execution

- **WHEN** the DAG executes the "fleet_composition" node during a scenario run
- **THEN** the system SHALL produce a provenance record containing the node ID, all input values received from upstream nodes, the data source for each input, and the compute function version

#### Scenario: Provenance is recorded for every node in the graph

- **WHEN** a full scenario execution completes
- **THEN** every node in the DAG SHALL have an associated provenance record in the ScenarioResult metadata

#### Scenario: Provenance is stored with results, not reconstructed

- **WHEN** a user queries provenance for a completed scenario
- **THEN** the system SHALL return the stored provenance records directly, without re-executing or reconstructing the computation trace

### Requirement: Input-to-Output Traceability

The system SHALL support provenance chain queries that trace any output value back to its contributing input nodes. Given an output node, the system MUST return the complete chain of intermediate computations, input values, and data sources that produced it. The provenance chain SHALL be navigable in both directions: forward (input to output) and backward (output to input). A user MUST be able to trace any output to its data sources and assumptions in three or fewer navigation steps.

#### Scenario: Trace cumulative GHG output back to inputs

- **WHEN** a user queries the provenance chain for the "cumulative_ghg" output node
- **THEN** the system SHALL return the ordered chain of nodes from inputs through intermediates to the output, with each node's input values and data sources

#### Scenario: Forward trace from an input node

- **WHEN** a user queries which outputs are affected by the "oil_price" input node
- **THEN** the system SHALL return all downstream nodes and output nodes that depend on "oil_price", with the causal path for each

#### Scenario: Three-click traceability

- **WHEN** a user starts at a top-level output (e.g., cumulative GHG) in the interface
- **THEN** the user SHALL be able to reach the underlying data sources and assumptions within three navigation steps

### Requirement: Intervention Attribution

The system SHALL decompose the total effect of a counterfactual scenario into per-intervention contributions. For each intervention applied, the system MUST quantify its individual contribution to the change in each output node relative to the baseline. The attribution MUST account for interaction effects when multiple interventions are applied simultaneously. The sum of attributed contributions plus interaction terms MUST equal the total observed difference (within numerical tolerance).

#### Scenario: Attribute emission reduction to a single intervention

- **WHEN** a scenario with one carbon pricing intervention is compared to the baseline
- **THEN** the system SHALL attribute 100% of the emission delta to the carbon pricing intervention

#### Scenario: Decompose effects of multiple interventions

- **WHEN** a scenario with carbon pricing, EV subsidies, and grid decarbonization is compared to the baseline
- **THEN** the system SHALL report the emission reduction attributable to each intervention individually, plus any interaction terms, and the sum SHALL equal the total reduction

#### Scenario: Interaction effects are explicitly reported

- **WHEN** two interventions have synergistic effects (e.g., EV subsidies + clean grid)
- **THEN** the system SHALL report the interaction effect as a separate attribution component, distinct from each intervention's independent effect

### Requirement: Data Source Lineage

The system SHALL track which external data sources produced which input values in the model. Each input node MUST declare its data source(s) with at minimum: source name, publication date, version or vintage, URL or DOI where applicable, and any transformations applied to derive the input value from the raw data. The system SHALL make data source lineage queryable for any node in the graph.

#### Scenario: Query data source for a specific input node

- **WHEN** a user queries the data source for the "survival_curve" input node
- **THEN** the system SHALL return the source metadata including source name, publication date, DOI, and any transformations applied

#### Scenario: List all nodes sourced from a specific dataset

- **WHEN** a user queries which nodes use data from "EPA Fuel Economy Guide 2024"
- **THEN** the system SHALL return all input nodes that cite that dataset as a source, along with the specific fields used

### Requirement: Assumption Documentation Per Node

Every node in the DAG SHALL have documented assumptions that describe the modeling choices, simplifications, and parameter selections made for that node's computation. Assumptions MUST be stored as structured metadata on the node definition (not in external documents). Each assumption MUST include: a human-readable description, a rationale, and a confidence level (high, medium, low). The system SHALL include active assumptions in provenance records.

#### Scenario: Query assumptions for a node

- **WHEN** a user queries the assumptions for the "phev_utility_factor" node
- **THEN** the system SHALL return the documented assumptions including description, rationale, and confidence level

#### Scenario: Assumptions are included in provenance

- **WHEN** a provenance record is generated for a node execution
- **THEN** the record SHALL include all active assumptions for that node at the time of execution

#### Scenario: Assumptions are editable per scenario

- **WHEN** a user overrides an assumption for a specific scenario (e.g., changes PHEV home charging availability from 100% to 70%)
- **THEN** the system SHALL record the overridden assumption in the scenario's provenance and use the modified parameter in computation

### Requirement: Human-Readable Provenance Reports

The system SHALL generate human-readable provenance reports that summarize how a specific output was produced. The report MUST be understandable by non-technical decision-makers and SHALL include: the output value with confidence interval, the key input drivers (top contributing inputs), the data sources used, the assumptions made, and any interventions applied. The report format MUST support export as PDF or HTML.

#### Scenario: Generate a provenance report for cumulative GHG

- **WHEN** a user requests a provenance report for cumulative GHG emissions in a counterfactual scenario
- **THEN** the system SHALL produce a report containing the GHG value with 90% confidence interval, the top 5 input drivers, the data sources for each driver, the key assumptions, and the interventions applied with their attributed effects

#### Scenario: Report is understandable by non-technical readers

- **WHEN** a provenance report is generated
- **THEN** the report SHALL use plain language (no code, no variable names), include units on all values, and provide brief explanations of technical terms

#### Scenario: Export report as PDF

- **WHEN** a user requests a provenance report with format "pdf"
- **THEN** the system SHALL generate and return a formatted PDF document containing the full provenance report
