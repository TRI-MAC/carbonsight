## MODIFIED Requirements

### Requirement: Scenario Comparison View

The system SHALL provide a view for comparing two or more scenarios. The comparison view MUST display: a trajectory chart with shaded delta areas between scenarios, and summary cards showing key metric deltas (Total GHG, Gas Usage, Electric Usage, Production Emissions, Grid Intensity). The flat per-node delta table is removed. Users MUST be able to expand summary cards to see year-by-year detail for each metric.

#### Scenario: Compare baseline and intervention scenarios

- **WHEN** a user selects the baseline scenario and an intervention scenario for comparison
- **THEN** the system SHALL display the trajectory chart with shaded delta area and 5 summary cards showing final-year deltas with sparkline trends

#### Scenario: Compare three or more scenarios

- **WHEN** a user selects three scenarios for comparison
- **THEN** the system SHALL display all three on the trajectory chart with distinct visual encoding (color, line style) and summary cards comparing each intervention against the first-selected (baseline) scenario
