## ADDED Requirements

### Requirement: Causal Graph Visualization

The system SHALL provide an interactive DAG visualization showing all nodes and edges in the causal graph. Users MUST be able to click on any node to view its details (current value, distribution, data source, assumptions). The visualization SHALL highlight the causal path from any selected node to its upstream inputs and downstream outputs. The graph layout MUST be readable with the full CarbonSight node set (approximately 30-50 nodes) without manual arrangement.

#### Scenario: View the full causal graph

- **WHEN** a user navigates to the causal graph view
- **THEN** the system SHALL render an interactive DAG with all nodes and edges, using an automatic layout algorithm that avoids overlapping nodes

#### Scenario: Inspect a node's details

- **WHEN** a user clicks on the "grid_carbon_intensity" node in the graph view
- **THEN** the system SHALL display a panel showing the node's current value or distribution, its data source, its assumptions, and its upstream/downstream connections

#### Scenario: Highlight causal path

- **WHEN** a user selects a node and requests "show causal path"
- **THEN** the system SHALL visually highlight all upstream ancestor nodes and all downstream descendant nodes, dimming unrelated nodes

### Requirement: Scenario Configuration UI

The system SHALL provide a user interface for creating and editing scenarios. Users MUST be able to: create a new scenario from the baseline defaults, select and configure interventions from the available taxonomy, override individual input node values or distributions, name and save scenarios for later comparison. The UI SHALL validate intervention parameters before accepting them.

#### Scenario: Create a new scenario with interventions

- **WHEN** a user creates a new scenario named "Aggressive EV Policy" and adds a $10,000 EV subsidy intervention and a ZEV mandate of 50% by year 7
- **THEN** the system SHALL store the scenario configuration and make it available for execution and comparison

#### Scenario: Edit an existing scenario

- **WHEN** a user modifies the EV subsidy amount in a saved scenario from $10,000 to $7,500
- **THEN** the system SHALL update the scenario configuration and mark any cached results as stale

#### Scenario: Validate intervention parameters

- **WHEN** a user enters a negative value for carbon price
- **THEN** the UI SHALL display a validation error and prevent the scenario from being saved

### Requirement: Scenario Comparison View

The system SHALL provide a view for comparing two or more scenarios. The comparison view MUST display: a trajectory chart with shaded delta areas between scenarios, and summary cards showing key metric deltas (Total GHG, Gas Usage, Electric Usage, Production Emissions, Grid Intensity). The flat per-node delta table is removed. Users MUST be able to expand summary cards to see year-by-year detail for each metric.

#### Scenario: Compare baseline and intervention scenarios

- **WHEN** a user selects the baseline scenario and an intervention scenario for comparison
- **THEN** the system SHALL display the trajectory chart with shaded delta area and 5 summary cards showing final-year deltas with sparkline trends

#### Scenario: Compare three or more scenarios

- **WHEN** a user selects three scenarios for comparison
- **THEN** the system SHALL display all three on the trajectory chart with distinct visual encoding (color, line style) and summary cards comparing each intervention against the first-selected (baseline) scenario

### Requirement: Cumulative GHG Trajectory Chart

The system SHALL display a 10-year line chart of cumulative GHG emissions as the primary output visualization. The chart MUST show confidence bands (e.g., 5th-95th percentile shading) when UQ results are available. The chart SHALL support overlaying multiple scenarios. The x-axis SHALL represent simulation years and the y-axis SHALL represent cumulative GHG in Mt CO2e with clear axis labels and units.

#### Scenario: Display GHG trajectory with confidence bands

- **WHEN** a UQ run completes for a scenario
- **THEN** the system SHALL render a line chart with the median trajectory as a solid line, the 25th-75th percentile range as a dark shaded band, and the 5th-95th percentile range as a light shaded band

#### Scenario: Overlay baseline and intervention trajectories

- **WHEN** a user selects two scenarios for the GHG trajectory chart
- **THEN** the system SHALL display both trajectories on the same chart with distinct colors and their respective confidence bands

### Requirement: Uncertainty Visualization

The system SHALL provide dedicated uncertainty visualizations including: confidence interval displays on all output charts, fan charts showing how uncertainty evolves over the simulation horizon, and distribution plots for individual output nodes. The system MUST clearly communicate the degree of uncertainty to non-technical users through visual design (e.g., wider bands = more uncertain).

#### Scenario: Display a fan chart for fleet emissions

- **WHEN** a user views the uncertainty visualization for annual fleet emissions
- **THEN** the system SHALL render a fan chart with nested percentile bands (e.g., 10th-90th, 25th-75th, median) that visually conveys the range and shape of uncertainty over time

#### Scenario: Show distribution for a single output in a single year

- **WHEN** a user clicks on a specific year in the GHG trajectory chart
- **THEN** the system SHALL display a histogram or density plot of the Monte Carlo output distribution for that year

### Requirement: Sensitivity Analysis Display

The system SHALL visualize sensitivity analysis results as a tornado chart or horizontal bar chart showing the top uncertainty drivers ranked by their contribution to output variance. Each bar MUST be labeled with the parameter name and its Sobol index value. The chart SHALL support toggling between first-order and total-order indices. The display MUST be interpretable by non-technical users with clear labeling (e.g., "Battery cost uncertainty explains 23% of output variance").

#### Scenario: Display tornado chart of top drivers

- **WHEN** a sensitivity analysis completes and the user views the results
- **THEN** the system SHALL render a horizontal bar chart with the top 10 uncertainty drivers ranked by total-order Sobol index, each labeled with its name and percentage contribution

#### Scenario: Toggle between first-order and total-order indices

- **WHEN** a user toggles from total-order to first-order Sobol indices
- **THEN** the chart SHALL re-render with first-order indices, and the ranking may change accordingly

### Requirement: Intervention Attribution View

The system SHALL provide a waterfall or stacked bar chart that decomposes the total emission change between baseline and counterfactual into per-intervention contributions. Each segment MUST be labeled with the intervention name and its attributed contribution (absolute and percentage). Interaction effects MUST be shown as a distinct segment. The chart SHALL clearly show whether each intervention increases or decreases emissions relative to baseline.

#### Scenario: Display waterfall chart for a multi-intervention scenario

- **WHEN** a user views the attribution for a scenario with carbon pricing, EV subsidies, and grid decarbonization
- **THEN** the system SHALL render a waterfall chart starting from the baseline GHG value, with each intervention's contribution as a labeled step, plus an interaction term, ending at the counterfactual GHG value

#### Scenario: Distinguish positive and negative contributions

- **WHEN** an intervention (e.g., increased VMT) increases emissions while others decrease them
- **THEN** the system SHALL display the increasing contribution in a visually distinct style (e.g., red/upward) versus decreasing contributions (e.g., green/downward)

### Requirement: Export Capability

The system SHALL support exporting visualizations and data. Charts MUST be exportable as PNG and SVG image formats. Underlying data MUST be exportable as CSV files. Scenario configurations MUST be exportable as JSON or YAML. The export function SHALL be accessible from each chart and from a centralized export page.

#### Scenario: Export a chart as PNG

- **WHEN** a user clicks the export button on the GHG trajectory chart and selects PNG
- **THEN** the system SHALL generate and download a publication-quality PNG image of the chart with labels, legend, and title

#### Scenario: Export underlying data as CSV

- **WHEN** a user clicks the export button on the scenario comparison view and selects CSV
- **THEN** the system SHALL generate and download a CSV file containing the year-by-year values for all compared scenarios and metrics

#### Scenario: Export scenario configuration as YAML

- **WHEN** a user exports a saved scenario configuration
- **THEN** the system SHALL generate and download a YAML file containing all input node overrides, intervention definitions, and metadata for the scenario
