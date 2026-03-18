## ADDED Requirements

### Requirement: Node Definition and Typing

The simulation engine SHALL support typed node definitions. Each node MUST declare one of the following types: `scalar`, `timeseries`, `distribution`, or `dataframe`. The engine SHALL reject node registration when a node does not declare a valid type. Distribution-typed nodes MUST be capable of holding either a point value or a probability distribution. Compute functions SHALL auto-wire their inputs by matching parameter names to upstream node names in the DAG.

#### Scenario: Register a valid typed node

- **WHEN** a user registers a node with name `fleet_size` and type `scalar`
- **THEN** the engine SHALL accept the node and store it with the declared type

#### Scenario: Reject a node with an invalid type

- **WHEN** a user registers a node with type `matrix`
- **THEN** the engine SHALL raise a validation error indicating the type is not one of `scalar`, `timeseries`, `distribution`, or `dataframe`

#### Scenario: Distribution node holds a point value

- **WHEN** a user registers a distribution-typed node and assigns it a single numeric value
- **THEN** the engine SHALL store the value as a degenerate (point) distribution and treat it as valid

#### Scenario: Auto-wire compute function inputs

- **WHEN** a compute function is registered with parameters named `fleet_size` and `renewal_rate`
- **THEN** the engine SHALL automatically resolve those parameters to the upstream nodes named `fleet_size` and `renewal_rate`

### Requirement: DAG Construction and Validation

The engine SHALL construct a directed acyclic graph from registered nodes and their dependencies. The engine MUST distinguish between two edge types: **within-step edges** (current time step dependencies) and **temporal edges** (dependencies on a node's value from the previous time step). The engine MUST reject any graph that contains a cycle among within-step edges, raising a validation error that identifies the offending nodes. Temporal edges SHALL be excluded from cycle detection since they reference prior-year values and cannot create within-step circular dependencies. The engine SHALL validate type compatibility between connected nodes at construction time; an edge from a `scalar` node to a compute function expecting a `dataframe` input MUST be rejected with a descriptive type-mismatch error.

#### Scenario: Construct a valid DAG

- **WHEN** nodes A, B, and C are registered such that C depends on A and B via within-step edges, and no cycles exist among within-step edges
- **THEN** the engine SHALL successfully construct the DAG with three nodes and two edges

#### Scenario: Reject a cyclic graph among within-step edges

- **WHEN** node A depends on B and node B depends on A via within-step edges
- **THEN** the engine SHALL raise a cycle-detection error naming nodes A and B

#### Scenario: Accept temporal edges that would form a cycle if treated as within-step

- **WHEN** node A depends on B via a within-step edge and node B depends on A via a temporal edge (previous year's value)
- **THEN** the engine SHALL accept the graph as valid because the temporal edge does not create a within-step cycle

#### Scenario: Reject type-incompatible edges

- **WHEN** a `scalar`-typed node is wired to a compute function parameter annotated as `dataframe`
- **THEN** the engine SHALL raise a type-compatibility error identifying the mismatched edge

### Requirement: Topological Execution

The engine SHALL execute nodes in topological order such that every node's dependencies are fully resolved before the node's compute function is invoked. The engine MUST record provenance for each node execution, capturing the node name, execution timestamp, and the identities of upstream inputs consumed.

#### Scenario: Execute nodes in dependency order

- **WHEN** the DAG contains nodes A -> B -> C
- **THEN** the engine SHALL execute A before B and B before C

#### Scenario: Record provenance per node

- **WHEN** node B is executed with inputs from node A
- **THEN** the engine SHALL produce a provenance record for B containing the execution timestamp, the node name `B`, and an input reference to `A`

### Requirement: Temporal Edges and Lagged Dependencies

The engine SHALL support **temporal edges** that allow a compute function to depend on another node's value from the previous time step. Temporal parameters MUST be declared explicitly in the compute function signature (e.g., via a naming convention like `prev_<node_name>` or a decorator). The engine SHALL resolve temporal parameters by reading from the prior year's output store. For the first time step (year 0 / 2024), temporal dependencies MUST be resolved using declared initial/default values. The engine MUST reject a temporal edge if no initial value is provided for the referenced node. Provenance records MUST distinguish temporal edges from within-step edges, recording the source year of any temporally-referenced value.

#### Scenario: Declare and resolve a temporal dependency

- **WHEN** a compute function for `powertrain_preference` declares a temporal parameter `prev_fleet_composition`
- **THEN** the engine SHALL resolve `prev_fleet_composition` to the `fleet_composition` node's output from the previous year

#### Scenario: Resolve temporal dependency in the first year using initial values

- **WHEN** the simulation is in year 0 (2024) and a compute function references `prev_fleet_composition`
- **THEN** the engine SHALL resolve the temporal parameter to the declared initial/default value for `fleet_composition`

#### Scenario: Reject temporal edge with no initial value

- **WHEN** a compute function declares a temporal parameter `prev_ev_market_share` but no initial value is provided for `ev_market_share`
- **THEN** the engine SHALL raise a validation error indicating that temporal dependencies require initial values

#### Scenario: Provenance records temporal edge source year

- **WHEN** node B in year 2027 receives a temporal input from node A's year 2026 output
- **THEN** the provenance record for B SHALL indicate that the input from A was a temporal reference to year 2026, distinct from a within-step edge

#### Scenario: Feedback loop via temporal edges produces year-over-year dynamics

- **WHEN** `fleet_composition` depends on `powertrain_preference` (within-step) and `powertrain_preference` depends on `prev_fleet_composition` (temporal)
- **THEN** the engine SHALL execute without cycle errors, and changes to fleet composition in year N SHALL influence powertrain preference in year N+1

### Requirement: Year-by-Year Time Stepping

The engine SHALL execute the simulation over 10 discrete year steps from 2024 through 2033 inclusive. At each year step, the engine MUST apply a 5% fleet renewal rate to the modeled vehicle fleet. The engine SHALL make the outputs of year N available as inputs to year N+1, both for explicit output chaining and for resolving temporal edges. Each year step MUST be identifiable in the output by its calendar year. The engine MUST maintain a year-indexed output store so that temporal edges can reference any prior year's values.

#### Scenario: Execute a full 10-year horizon

- **WHEN** a simulation is run with default time-stepping configuration
- **THEN** the engine SHALL produce outputs for exactly 10 year steps labeled 2024 through 2033

#### Scenario: Apply fleet renewal rate each year

- **WHEN** the simulation advances from year 2024 to year 2025 with an initial fleet of 1000 vehicles
- **THEN** the engine SHALL model 50 vehicles (5% of 1000) as renewed in year 2025

#### Scenario: Chain year-step outputs

- **WHEN** the simulation completes year 2026
- **THEN** the outputs of year 2026 SHALL be available as inputs to the computation of year 2027, including resolution of temporal edges referencing year 2026 values

### Requirement: Deterministic and UQ Execution Modes

The engine SHALL support two execution modes: deterministic and uncertainty-quantification (UQ). In deterministic mode, all distribution-typed nodes MUST be collapsed to their point estimates before compute functions execute. In UQ mode, the engine SHALL propagate full distributions through the DAG. The execution mode MUST be specified at simulation launch time and SHALL apply uniformly to all nodes in the run.

#### Scenario: Deterministic mode collapses distributions

- **WHEN** a simulation is launched in deterministic mode and a distribution node holds a normal distribution with mean 100 and standard deviation 10
- **THEN** the engine SHALL pass the point estimate 100 to downstream compute functions

#### Scenario: UQ mode propagates distributions

- **WHEN** a simulation is launched in UQ mode and a distribution node holds a normal distribution
- **THEN** the engine SHALL propagate the full distribution object to downstream compute functions

#### Scenario: Reject mode change mid-execution

- **WHEN** a simulation is already executing in deterministic mode and a caller attempts to switch to UQ mode
- **THEN** the engine SHALL raise an error indicating the execution mode is immutable for the active run

### Requirement: Scenario Definition and Management

The engine SHALL support named scenarios, where each scenario is a configuration of input-node value overrides. The engine MUST allow creation, retrieval, update, and deletion of named scenarios. Scenario names MUST be unique within a simulation context. Each scenario SHALL be fully defined by its name and a mapping of node names to override values.

#### Scenario: Create and retrieve a named scenario

- **WHEN** a user creates a scenario named `ev_subsidy` with an override setting `subsidy_amount` to 7500
- **THEN** the engine SHALL store the scenario and return it unchanged upon retrieval by name

#### Scenario: Reject duplicate scenario names

- **WHEN** a scenario named `ev_subsidy` already exists and a user attempts to create another scenario with the same name
- **THEN** the engine SHALL raise a uniqueness error

#### Scenario: Update an existing scenario

- **WHEN** a user updates the `ev_subsidy` scenario to change `subsidy_amount` from 7500 to 10000
- **THEN** the engine SHALL persist the updated override value and return 10000 on subsequent retrieval

#### Scenario: Delete a scenario

- **WHEN** a user deletes the scenario named `ev_subsidy`
- **THEN** the engine SHALL remove it and any subsequent retrieval by that name SHALL indicate the scenario does not exist

### Requirement: Scenario Comparison

The engine SHALL support baseline-versus-counterfactual comparison. The engine MUST execute both the baseline scenario and the intervention scenario over the full time horizon and produce a difference report. The difference report SHALL contain, for each output node, the per-year delta between the baseline and intervention values. For distribution-typed outputs, the comparison MUST report deltas on summary statistics (mean, median, 5th and 95th percentiles).

#### Scenario: Compare baseline and intervention

- **WHEN** the baseline scenario produces cumulative emissions of 500 MtCO2 in year 2030 and the `ev_subsidy` intervention produces 450 MtCO2 in year 2030
- **THEN** the difference report SHALL show a delta of -50 MtCO2 for cumulative emissions in year 2030

#### Scenario: Compare distribution outputs

- **WHEN** the baseline and intervention both produce distribution-typed outputs for a node
- **THEN** the difference report SHALL include deltas for mean, median, 5th percentile, and 95th percentile of that node for each year

### Requirement: Execution Performance

The engine SHALL complete a full 10-year scenario run including uncertainty quantification in under 60 seconds on the reference hardware. The engine MUST report wall-clock execution time upon run completion. If a run exceeds the 60-second target, the engine SHALL emit a performance warning in the run metadata.

#### Scenario: Complete a UQ run within time budget

- **WHEN** a full 10-year simulation is executed in UQ mode on reference hardware
- **THEN** the engine SHALL complete in fewer than 60 wall-clock seconds and record the elapsed time in run metadata

#### Scenario: Warn on performance budget exceeded

- **WHEN** a simulation run completes in 72 seconds
- **THEN** the engine SHALL include a performance warning in the run metadata indicating the 60-second target was exceeded by 12 seconds
