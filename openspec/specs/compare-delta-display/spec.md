## ADDED Requirements

### Requirement: Summary cards display key metric deltas

The Compare page SHALL display summary cards for 5 key metrics after a comparison completes: Total GHG, Gas Usage Emissions, Electric Usage Emissions, Production Emissions, and Grid Carbon Intensity. Each card SHALL show the metric name, the final-year absolute delta, the final-year percentage delta, and a sparkline of the 10-year delta trajectory.

#### Scenario: Successful comparison with both scenarios run

- **WHEN** the user compares two scenarios that have been run
- **THEN** 5 summary cards SHALL appear, each showing the final-year delta value, percentage change, and a sparkline trend line

#### Scenario: Positive delta (intervention increases metric)

- **WHEN** a metric's intervention value exceeds the baseline value
- **THEN** the card SHALL display the delta in red with an upward arrow

#### Scenario: Negative delta (intervention decreases metric)

- **WHEN** a metric's intervention value is less than the baseline value
- **THEN** the card SHALL display the delta in green with a downward arrow

### Requirement: Summary cards expand to show year-by-year detail

Each summary card SHALL be clickable to expand an accordion panel showing the year-by-year breakdown for that metric.

#### Scenario: User clicks a summary card

- **WHEN** the user clicks a summary card
- **THEN** the card SHALL expand to show a table with columns: Year, Baseline, Intervention, Delta
- **AND** any other expanded card SHALL collapse (accordion behavior)

#### Scenario: User clicks an already-expanded card

- **WHEN** the user clicks a card that is already expanded
- **THEN** the card SHALL collapse

### Requirement: Trajectory chart shows shaded delta area

The GHG trajectory chart SHALL display a shaded area between the baseline and intervention lines, colored to indicate whether the intervention reduces or increases emissions.

#### Scenario: Intervention reduces emissions

- **WHEN** the intervention line is below the baseline line for a given year range
- **THEN** the area between the lines SHALL be shaded green (with low opacity)

#### Scenario: Intervention increases emissions

- **WHEN** the intervention line is above the baseline line for a given year range
- **THEN** the area between the lines SHALL be shaded red (with low opacity)

#### Scenario: Crossover point exists

- **WHEN** the intervention transitions from above to below the baseline (or vice versa)
- **THEN** the chart SHALL display a text annotation at the crossover year indicating "Crossover: {year}"

### Requirement: Trajectory chart shows final-year annotation

The trajectory chart SHALL display a text annotation at the final year showing the cumulative delta.

#### Scenario: Comparison completes

- **WHEN** a comparison is displayed
- **THEN** the chart SHALL show an annotation at the rightmost data point indicating the final-year percentage delta (e.g., "−3.5% by 2033")

### Requirement: Flat delta table is removed

The Compare page SHALL NOT display the raw node × year delta table.

#### Scenario: Comparison displayed

- **WHEN** a comparison result is shown
- **THEN** no flat table of per-node deltas SHALL be rendered
