## ADDED Requirements

### Requirement: Three-column scenario builder layout

The system SHALL provide a scenario builder page with three columns: a scenario list sidebar (left), intervention controls panel (center), and a live impact preview panel (right).

#### Scenario: User navigates to scenarios page

- **WHEN** a user navigates to the scenarios page
- **THEN** the system SHALL display a three-column layout with the scenario list on the left, intervention controls in the center, and an impact preview panel on the right

#### Scenario: User selects a scenario from the list

- **WHEN** a user clicks a scenario in the left sidebar
- **THEN** the center panel SHALL populate with that scenario's intervention settings and the right panel SHALL show the impact preview if the scenario has interventions

### Requirement: Accordion-based intervention controls with sliders

The intervention controls panel SHALL display all intervention categories as expandable accordion sections. Each intervention SHALL show a checkbox to enable/disable it, and when enabled, range sliders paired with numeric inputs for every parameter. Parameters SHALL use human-readable labels.

#### Scenario: User enables an intervention and adjusts a parameter

- **WHEN** a user checks the "EV subsidy" checkbox and drags the BEV Purchase Shift slider to 0.20
- **THEN** the intervention SHALL be marked active with the slider and numeric input both reflecting 0.20

#### Scenario: Multi-parameter intervention

- **WHEN** a user enables the "Scrappage program" intervention
- **THEN** the system SHALL display sliders for all 4 parameters: Age Threshold, Acceleration Factor, Duration (Years), and Start Year

### Requirement: Causal path annotations

Each active intervention SHALL display a causal path annotation below its controls, showing the chain of DAG nodes from the intervention's target node to `total_emissions` as a sequence of labeled pill chips.

#### Scenario: User enables EV subsidy

- **WHEN** the user enables the EV subsidy intervention
- **THEN** the system SHALL display a causal path such as: Powertrain Proportions -> Fleet With New Sales -> ... -> Total Emissions

### Requirement: Live impact preview with auto-run

The impact preview panel SHALL automatically run a deterministic simulation after the user adjusts any intervention parameter, with an 800ms debounce. The preview SHALL compare the current scenario against baseline and display: a GHG trajectory chart (baseline dashed, current solid, with delta shading), 4 compact delta metric cards (Total GHG, BEV Share, Fleet Size, Grid Intensity), and a fleet composition stacked area chart.

#### Scenario: User adjusts a slider

- **WHEN** the user moves a slider and 800ms elapses without further changes
- **THEN** the system SHALL auto-save the scenario, run a deterministic simulation, fetch trace data, and update the preview panel with trajectory, delta cards, and composition charts

#### Scenario: User adjusts slider during an in-flight run

- **WHEN** the user changes a slider while a previous auto-run is still in progress
- **THEN** the system SHALL discard the in-flight result and start a new debounce cycle

#### Scenario: Baseline scenario selected

- **WHEN** the selected scenario is "baseline"
- **THEN** the preview panel SHALL display a message indicating that an intervention scenario must be selected to see impact preview
