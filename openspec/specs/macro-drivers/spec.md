## ADDED Requirements

### Requirement: Oil Price Trajectory Input

The system SHALL accept oil price trajectories as exogenous timeseries input nodes in the DAG, covering the full 10-year simulation horizon. Oil price trajectories MUST be specified as annual price-per-barrel values (nominal or real dollars, with the basis documented). The system SHALL support user-supplied custom trajectories as well as built-in reference trajectories derived from EIA Annual Energy Outlook data.

#### Scenario: Load EIA reference oil price trajectory

- **WHEN** a scenario is configured with oil price source set to "eia-reference"
- **THEN** the system SHALL load the EIA Annual Energy Outlook reference case oil price trajectory for the 10-year horizon
- **AND** the trajectory SHALL be represented as an exogenous timeseries node in the DAG with one value per simulation year

#### Scenario: User-supplied custom oil price trajectory

- **WHEN** a user provides a custom oil price trajectory as an array of annual values
- **THEN** the system SHALL validate that the trajectory length matches the simulation horizon
- **AND** the system SHALL use the custom trajectory in place of any built-in trajectory

#### Scenario: Oil price propagates to downstream nodes

- **WHEN** an oil price trajectory is loaded into the DAG
- **THEN** the system SHALL propagate oil price effects to VMT, powertrain preference, and used car market value nodes via causal edges

### Requirement: Electricity Price Trajectory Input

The system SHALL accept electricity price trajectories as exogenous timeseries input nodes in the DAG, covering the full 10-year simulation horizon. Electricity prices MUST be specified as annual cents-per-kWh values. The system SHALL support both built-in EIA-derived trajectories and user-supplied custom trajectories.

#### Scenario: Load EIA reference electricity price trajectory

- **WHEN** a scenario is configured with electricity price source set to "eia-reference"
- **THEN** the system SHALL load the EIA Annual Energy Outlook reference case electricity price trajectory for the 10-year horizon
- **AND** the trajectory SHALL be represented as an exogenous timeseries node in the DAG

#### Scenario: Electricity price affects EV operating cost advantage

- **WHEN** the electricity price trajectory is loaded and the DAG is executed
- **THEN** the system SHALL compute the EV operating cost advantage relative to gasoline vehicles using the electricity price and oil price trajectories
- **AND** the operating cost advantage SHALL propagate to powertrain preference nodes

#### Scenario: Electricity price affects charging behavior

- **WHEN** the electricity price trajectory changes between scenarios
- **THEN** the system SHALL adjust charging behavior parameters (e.g., home vs. public charging mix, charging timing) based on the price signal

### Requirement: Consumer Preference Parameters

The system SHALL model consumer preference parameters as exogenous input nodes in the DAG, including willingness to pay for EVs and range anxiety thresholds. These parameters MUST be configurable per scenario and SHALL causally influence powertrain adoption rates.

#### Scenario: Willingness-to-pay parameter affects EV adoption

- **WHEN** the willingness-to-pay-for-EV parameter is set to a given dollar value
- **THEN** the system SHALL use this value in the powertrain preference transfer function to determine the share of new vehicle purchases selecting EVs
- **AND** increasing the willingness-to-pay value SHALL increase the EV adoption share, all else being equal

#### Scenario: Range anxiety threshold affects EV adoption

- **WHEN** the range anxiety threshold parameter is set (in miles)
- **THEN** the system SHALL reduce EV adoption probability for consumers whose driving patterns exceed the threshold
- **AND** the threshold SHALL interact with available EV range data from the fleet model

#### Scenario: Consumer preferences vary over the simulation horizon

- **WHEN** consumer preference parameters are specified as timeseries (one value per year)
- **THEN** the system SHALL apply the year-specific value at each simulation time step
- **AND** if a scalar value is provided instead, the system SHALL hold it constant across all years

### Requirement: Policy Parameter Inputs

The system SHALL model policy parameters as exogenous input nodes in the DAG, including carbon pricing, CAFE standards, EV purchase subsidies, and ZEV mandate levels. Each policy parameter MUST be specifiable as a timeseries over the simulation horizon and SHALL propagate causally to affected downstream nodes.

#### Scenario: Carbon price affects fuel cost and VMT

- **WHEN** a carbon price trajectory is specified (dollars per ton CO2)
- **THEN** the system SHALL add the carbon cost to the effective per-gallon fuel price
- **AND** the increased effective fuel price SHALL propagate through the oil price causal links to affect VMT and powertrain preferences

#### Scenario: CAFE standards affect fleet efficiency

- **WHEN** CAFE standard targets are specified as a timeseries of fleet-average mpg requirements
- **THEN** the system SHALL constrain new vehicle fleet-average efficiency to meet or exceed the standard
- **AND** the standards SHALL influence the powertrain mix of new vehicle entries in the fleet dynamics model

#### Scenario: EV subsidies affect purchase price

- **WHEN** EV purchase subsidy amounts are specified (dollars per vehicle, potentially varying by year)
- **THEN** the system SHALL reduce the effective EV purchase price by the subsidy amount in powertrain preference calculations
- **AND** changes to subsidy levels SHALL propagate to EV adoption rates

#### Scenario: ZEV mandates affect powertrain mix

- **WHEN** ZEV mandate percentages are specified as a timeseries
- **THEN** the system SHALL enforce a minimum zero-emission vehicle share in new vehicle sales for each year
- **AND** the mandate SHALL act as a floor on ZEV adoption independent of consumer preference calculations

### Requirement: Elasticity-Based Causal Propagation

The system SHALL use elasticity-based transfer functions to propagate macro driver effects to downstream nodes in the DAG. Elasticities MUST distinguish between short-run and long-run responses, consistent with transportation economics literature.

#### Scenario: Oil price to VMT propagation with short-run elasticity

- **WHEN** the oil price increases by 10% in a single year relative to the previous year
- **THEN** the system SHALL apply the short-run price elasticity of VMT demand (default approximately -0.2) to compute the VMT response
- **AND** the VMT change SHALL be approximately -2% in that year, all else being equal

#### Scenario: Oil price to VMT propagation with long-run elasticity

- **WHEN** the oil price has been sustained at a higher level for multiple years
- **THEN** the system SHALL transition from short-run to long-run elasticity (default approximately -0.6) using a partial adjustment model
- **AND** the cumulative VMT response SHALL converge toward the long-run elasticity over time

#### Scenario: Multiple causal links from a single driver

- **WHEN** the oil price node is connected to VMT, powertrain preference, and used car market value nodes
- **THEN** the system SHALL apply the appropriate elasticity-based transfer function independently on each causal edge
- **AND** each downstream node SHALL receive the propagated effect specific to its own elasticity parameter

### Requirement: Configurable Elasticity Values

The system SHALL allow users to override default elasticity values as scenario parameters. Default elasticity values MUST be sourced from transportation economics literature and documented with citations. Users MUST be able to set custom elasticity values for any causal link without modifying the underlying model code.

#### Scenario: Override short-run VMT elasticity

- **WHEN** a user specifies a custom short-run VMT price elasticity value in the scenario configuration
- **THEN** the system SHALL use the user-provided value instead of the literature default for the oil-price-to-VMT causal link
- **AND** the default value and its literature source SHALL remain accessible for reference

#### Scenario: Default elasticities are used when no override is provided

- **WHEN** a scenario does not specify custom elasticity values
- **THEN** the system SHALL use the literature-derived default values for all causal links
- **AND** the provenance record SHALL document which default values and sources were used

#### Scenario: Elasticity override applies only to the specified scenario

- **WHEN** a user overrides an elasticity value in scenario A but not in scenario B
- **THEN** scenario A SHALL use the custom value and scenario B SHALL use the default
- **AND** comparing the two scenarios SHALL correctly reflect the difference in elasticity assumptions

### Requirement: EIA Reference High and Low Scenario Support

The system SHALL provide built-in energy price trajectories corresponding to the EIA Annual Energy Outlook reference, high price, and low price scenarios. Users MUST be able to select among these scenarios as a shorthand for configuring oil and electricity price trajectories.

#### Scenario: Select EIA high oil price scenario

- **WHEN** a user selects the EIA "high" oil price scenario
- **THEN** the system SHALL load the EIA Annual Energy Outlook high oil price case trajectory
- **AND** the trajectory values SHALL match the published EIA projection for the corresponding outlook edition

#### Scenario: Select EIA low oil price scenario

- **WHEN** a user selects the EIA "low" oil price scenario
- **THEN** the system SHALL load the EIA Annual Energy Outlook low oil price case trajectory
- **AND** the trajectory values SHALL match the published EIA projection for the corresponding outlook edition

#### Scenario: EIA scenarios set both oil and electricity prices coherently

- **WHEN** a user selects an EIA scenario label (reference, high, or low)
- **THEN** the system SHALL load both the oil price and electricity price trajectories from the same EIA scenario case
- **AND** the two trajectories SHALL be internally consistent as published by EIA

#### Scenario: EIA scenario can be partially overridden

- **WHEN** a user selects an EIA scenario but also provides a custom electricity price trajectory
- **THEN** the system SHALL use the EIA oil price trajectory from the selected scenario
- **AND** the system SHALL use the user-provided custom electricity price trajectory, overriding only that component

### Requirement: Causal Link Documentation

The system SHALL maintain machine-readable documentation of all causal links between macro driver nodes and downstream nodes. Each causal link MUST specify the source node, target node, transfer function type, default parameter values, and literature citation for the default values.

#### Scenario: Query causal links for a macro driver

- **WHEN** a user or system component queries the causal links originating from the oil price node
- **THEN** the system SHALL return a list of all downstream nodes connected by causal edges
- **AND** each link SHALL include the transfer function type (e.g., elasticity-based), default parameter values, and a literature citation

#### Scenario: Causal link registry is consistent with DAG structure

- **WHEN** the DAG is constructed for a scenario
- **THEN** every causal link in the documentation registry SHALL correspond to an actual edge in the DAG
- **AND** every macro-driver-to-downstream edge in the DAG SHALL have a corresponding entry in the documentation registry

#### Scenario: Causal link documentation supports explainability

- **WHEN** the explainability layer traces the provenance of a downstream node value (e.g., VMT)
- **THEN** the trace SHALL include the causal link metadata from the documentation registry
- **AND** the trace SHALL show which macro driver influenced the value, through which transfer function, and with which parameter values
