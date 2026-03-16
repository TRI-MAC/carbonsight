## ADDED Requirements

### Requirement: Compare trajectory chart uses real simulation data
The ComparePage trajectory chart SHALL display actual GHG values from completed simulation runs, fetched via the trace API endpoint, instead of hardcoded demo data.

#### Scenario: Comparison with run results available
- **WHEN** the user selects two scenarios that have been run and clicks Compare
- **THEN** the trajectory chart SHALL fetch `total_emissions` trace data for each scenario and plot the real GHG trajectories with correct year-by-year values

#### Scenario: Trace fetch fails for a scenario
- **WHEN** the trace API returns 404 for a selected scenario (not yet run)
- **THEN** the page SHALL display an error message indicating which scenario needs to be run first, and SHALL NOT fall back to fake data silently

#### Scenario: Demo mode fallback
- **WHEN** the API is entirely unreachable
- **THEN** the page SHALL use demo data with a visible "Demo Mode" indicator, same as other pages

### Requirement: Compare page shows scenario run status
The ComparePage SHALL indicate whether each listed scenario has been run, so users know which scenarios are available for comparison.

#### Scenario: Scenario has been run
- **WHEN** a scenario has stored results on the backend
- **THEN** the scenario's checkbox label SHALL show a visual indicator (e.g., green dot or "Ready" badge) confirming it can be compared

#### Scenario: Scenario has not been run
- **WHEN** a scenario has no stored results
- **THEN** the scenario's checkbox label SHALL show a visual indicator (e.g., grey dot or "Not run" text) and the Compare button SHALL be disabled if any selected scenario is not run

### Requirement: Intervention specs use correct parameter names
The ScenariosPage intervention builder SHALL map each intervention type to its actual API parameter names from the catalog, instead of using a hardcoded heuristic.

#### Scenario: Carbon pricing intervention
- **WHEN** the user adds a carbon pricing intervention with value 100
- **THEN** the saved intervention spec SHALL be `{type: "carbon_pricing", params: {price_per_tonne: 100}}`

#### Scenario: VMT reduction intervention
- **WHEN** the user adds a VMT reduction intervention with value 0.9
- **THEN** the saved intervention spec SHALL be `{type: "vmt_reduction", params: {factor: 0.9}}`

#### Scenario: EV subsidy intervention
- **WHEN** the user adds an EV subsidy intervention with value 0.15
- **THEN** the saved intervention spec SHALL be `{type: "ev_subsidy", params: {proportion_shift: {bev: 0.15}}}`
