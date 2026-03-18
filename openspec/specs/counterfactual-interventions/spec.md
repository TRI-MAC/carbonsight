## ADDED Requirements

### Requirement: Intervention Type Taxonomy

The system SHALL classify all interventions into exactly four categories: **policy**, **technology**, **behavioral**, and **grid/energy**. Each intervention definition MUST declare its category. The system SHALL reject any intervention that does not belong to a recognized category.

#### Scenario: Classify a new intervention by category

- **WHEN** a user defines a new intervention with category "policy"
- **THEN** the system SHALL accept the intervention and associate it with the policy category

#### Scenario: Reject an intervention with an invalid category

- **WHEN** a user defines an intervention with category "economic"
- **THEN** the system SHALL reject the definition and return an error indicating the valid categories

### Requirement: Policy Interventions

The system SHALL support the following policy intervention types: carbon pricing, CAFE standards adjustments, EV purchase subsidies, ZEV mandates, fuel tax changes, scrappage/cash-for-clunkers programs, and charging infrastructure investment. Each policy intervention MUST specify its parameters (e.g., carbon price in $/tonne, subsidy amount in $, mandate percentage) and the time profile over which it applies across the 10-year horizon.

#### Scenario: Define a carbon pricing intervention

- **WHEN** a user creates a policy intervention of type "carbon_pricing" with a price of $50/tonne CO2 starting in year 3
- **THEN** the system SHALL store the intervention with the specified price trajectory and apply it as a cost adder to fossil fuel consumption nodes in the DAG

#### Scenario: Define a CAFE standards intervention

- **WHEN** a user creates a policy intervention of type "cafe_standards" with a target of 55 mpg by year 5
- **THEN** the system SHALL store the intervention and propagate the efficiency requirement to new vehicle entry nodes affecting powertrain mix and per-vehicle fuel consumption

#### Scenario: Define a scrappage program intervention

- **WHEN** a user creates a policy intervention of type "scrappage_program" targeting vehicles older than 15 years with a $5,000 incentive for 3 years
- **THEN** the system SHALL accelerate scrappage rates for the targeted vehicle cohorts during the active period

### Requirement: Technology Interventions

The system SHALL support technology interventions including: battery energy density improvement trajectories, battery cost reduction curves, alternative battery chemistries (e.g., solid-state, sodium-ion), manufacturing decarbonization (reduced embodied carbon per vehicle), and vehicle lightweighting. Each technology intervention MUST specify a parameter trajectory over the 10-year horizon.

#### Scenario: Define a battery cost reduction intervention

- **WHEN** a user creates a technology intervention of type "battery_cost" with a target of $60/kWh by year 7
- **THEN** the system SHALL override the baseline battery cost trajectory and propagate the change to EV purchase price and powertrain adoption nodes

#### Scenario: Define a manufacturing decarbonization intervention

- **WHEN** a user creates a technology intervention of type "manufacturing_decarb" reducing embodied production emissions by 30% by year 10
- **THEN** the system SHALL apply the reduction to production-phase lifecycle emissions for new vehicles entering the fleet

### Requirement: Behavioral Interventions

The system SHALL support behavioral interventions including: VMT reduction (e.g., remote work, urban planning), PHEV charging behavior changes (increased home charging frequency), eco-driving adoption, remote work impact on commute patterns, and ride-sharing penetration. Each behavioral intervention MUST specify the affected population segment and magnitude.

#### Scenario: Define a VMT reduction intervention

- **WHEN** a user creates a behavioral intervention of type "vmt_reduction" with a 10% reduction for urban commuters starting in year 2
- **THEN** the system SHALL reduce annual VMT for the specified segment and propagate the effect to usage-phase emissions

#### Scenario: Define a PHEV charging behavior intervention

- **WHEN** a user creates a behavioral intervention of type "phev_charging" increasing the utility factor from 0.5 to 0.7
- **THEN** the system SHALL increase the electric-miles fraction for PHEVs, reducing their gasoline consumption and increasing their electricity consumption

### Requirement: Grid and Energy Interventions

The system SHALL support grid/energy interventions including: grid mix scenarios (e.g., coal retirement schedules, renewable penetration targets), renewable energy build-out rates, and smart charging (shifting EV charging to low-carbon grid periods). Each grid intervention MUST specify a year-by-year trajectory for the affected grid parameters.

#### Scenario: Define a grid decarbonization intervention

- **WHEN** a user creates a grid/energy intervention of type "grid_mix" with coal phase-out by year 8 and 60% renewable by year 10
- **THEN** the system SHALL override the baseline grid carbon intensity trajectory and propagate the change to EV usage-phase emissions

#### Scenario: Define a smart charging intervention

- **WHEN** a user creates a grid/energy intervention of type "smart_charging" with 50% fleet participation
- **THEN** the system SHALL reduce the effective grid carbon intensity for participating EVs by shifting consumption to lower-carbon time periods

### Requirement: Intervention Application to Scenarios

The system SHALL apply interventions by overriding the corresponding input nodes in the DAG. An intervention MUST NOT modify the graph structure; it SHALL only modify node input values or distribution parameters. When an intervention is applied to a scenario, the system SHALL re-execute the DAG with the overridden values and produce a complete ScenarioResult.

#### Scenario: Apply a single intervention to a scenario

- **WHEN** a user applies a carbon pricing intervention to the baseline scenario
- **THEN** the system SHALL create a new counterfactual scenario with the carbon price node overridden, execute the DAG, and return a ScenarioResult containing full outputs and provenance

#### Scenario: Intervention does not alter graph topology

- **WHEN** an intervention is applied
- **THEN** the set of nodes and edges in the DAG SHALL remain identical to the baseline; only node input values or distribution parameters SHALL differ

### Requirement: Scenario Differencing

The system SHALL compute the delta between a baseline scenario and one or more intervention scenarios. The differencing output MUST include: absolute difference, percentage difference, and per-year breakdown for all output nodes. The system SHALL attribute the total difference to the contributing interventions when multiple interventions are applied.

#### Scenario: Compute delta between baseline and single intervention

- **WHEN** a user requests a comparison between the baseline scenario and a carbon pricing scenario
- **THEN** the system SHALL return the year-by-year delta in cumulative GHG emissions, fleet composition, and other output nodes, expressed as both absolute and percentage differences

#### Scenario: Attribute differences across multiple interventions

- **WHEN** a user compares a scenario with three interventions against the baseline
- **THEN** the system SHALL decompose the total emission reduction into the contribution attributable to each individual intervention, accounting for interaction effects

### Requirement: Multi-Intervention Combinations

The system SHALL support applying multiple interventions simultaneously to a single scenario. When interventions affect overlapping nodes, the system SHALL apply them in a defined order (policy, then technology, then behavioral, then grid/energy) and MUST document any interaction effects. The system SHALL warn the user when interventions produce conflicting overrides on the same node.

#### Scenario: Combine policy and technology interventions

- **WHEN** a user applies both a carbon pricing intervention and a battery cost reduction intervention to the same scenario
- **THEN** the system SHALL apply both overrides, execute the DAG, and produce a ScenarioResult reflecting the combined effect

#### Scenario: Warn on conflicting interventions

- **WHEN** two interventions both override the same input node with different values
- **THEN** the system SHALL warn the user about the conflict and apply the interventions in the defined category order, documenting which value took precedence

#### Scenario: Interaction effects in multi-intervention scenarios

- **WHEN** a user applies EV subsidies and grid decarbonization interventions together
- **THEN** the system SHALL capture the interaction effect (more EVs on a cleaner grid) as a distinct component in the attribution breakdown, separate from each intervention's independent effect
