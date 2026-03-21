## ADDED Requirements

### Requirement: Unified scenario dashboard page

The system SHALL provide a single page that combines scenario overview and comparison functionality. The page MUST include a scenario selector dropdown and tab-based navigation between "Overview" and "Compare" modes.

#### Scenario: User lands on the page

- **WHEN** a user navigates to the dashboard
- **THEN** the system SHALL display the "Overview" tab with the baseline scenario selected by default

#### Scenario: User switches scenario in dropdown

- **WHEN** a user selects a different scenario from the dropdown
- **THEN** the Overview tab SHALL update to show that scenario's metrics, trajectory, and composition charts

### Requirement: Overview tab shows single-scenario dashboard

The Overview tab SHALL display headline metrics (fleet size, annual GHG, BEV share, total VMT), a GHG trajectory chart broken down by component (production, usage, disposal), and a fleet composition stacked area chart for the selected scenario.

#### Scenario: Viewing baseline scenario

- **WHEN** the selected scenario is "baseline"
- **THEN** the system SHALL fetch data from the `/dashboard` endpoint and display headline metrics, GHG trajectory by component, and fleet composition

#### Scenario: Viewing a non-baseline scenario

- **WHEN** the selected scenario is not "baseline"
- **THEN** the system SHALL fetch trace data for `total_emissions` and `fleet_snapshot` and reconstruct the same dashboard charts

### Requirement: Compare tab shows delta analysis

The Compare tab SHALL allow the user to select a second scenario and display the trajectory chart with delta shading, crossover/final-year annotations, and 5 summary delta cards. The scenario selected in the top dropdown SHALL be used as the baseline for comparison.

#### Scenario: User switches to Compare tab

- **WHEN** the user clicks the "Compare" tab
- **THEN** the system SHALL show a second scenario picker and, once a second scenario is selected, display the trajectory with delta shading and summary cards

#### Scenario: User changes the top-level scenario while in Compare tab

- **WHEN** the user changes the scenario in the top dropdown while on the Compare tab
- **THEN** the comparison SHALL re-run with the newly selected scenario as baseline
