## ADDED Requirements

### Requirement: Distribution Specification for Input Parameters

The system SHALL support specifying probability distributions for any input parameter in the DAG. Supported distribution types MUST include at minimum: normal, lognormal, uniform, triangular, and empirical (histogram-based). Each distribution specification MUST include its parameters (e.g., mean/std for normal, min/max for uniform) and an optional source citation. The system SHALL validate that distribution parameters are physically meaningful (e.g., no negative values for inherently positive quantities).

#### Scenario: Specify a normal distribution for grid carbon intensity

- **WHEN** a user sets the grid carbon intensity node to Normal(mean=369, std=20) g CO2/kWh
- **THEN** the system SHALL store the distribution and use it for sampling during Monte Carlo propagation

#### Scenario: Specify a triangular distribution for battery cost

- **WHEN** a user sets battery cost to Triangular(min=80, mode=100, max=150) $/kWh
- **THEN** the system SHALL store the distribution and sample from it during UQ runs

#### Scenario: Reject invalid distribution parameters

- **WHEN** a user specifies a normal distribution with a negative standard deviation
- **THEN** the system SHALL reject the specification and return a validation error

### Requirement: Monte Carlo Propagation Through DAG

The system SHALL propagate uncertainty through the DAG using Monte Carlo simulation as the primary method. For each sample, the system SHALL draw values from all input distributions, execute the full DAG, and collect the output values. The set of output samples SHALL form the empirical output distribution. The system MUST ensure that correlated inputs use the same sample index to preserve correlation structure.

#### Scenario: Propagate distributions through a linear chain

- **WHEN** the DAG contains nodes A -> B -> C with distributions on A
- **THEN** the system SHALL sample N values from A's distribution, compute B and C for each sample, and produce N output values for C that reflect the propagated uncertainty

#### Scenario: Preserve correlation across shared inputs

- **WHEN** two output nodes both depend on the same uncertain input node
- **THEN** the system SHALL use the same sampled value for that input in each Monte Carlo trial, preserving the correlation between the two outputs

### Requirement: Latin Hypercube Sampling Support

The system SHALL support Latin Hypercube Sampling (LHS) as an alternative to simple random sampling for Monte Carlo propagation. LHS SHALL be the default sampling strategy for all UQ runs. The system MUST ensure that LHS samples provide better coverage of the input space than simple random sampling at equivalent sample sizes.

#### Scenario: Use LHS for a 200-sample UQ run

- **WHEN** a user requests a UQ run with 200 samples and LHS enabled
- **THEN** the system SHALL generate 200 Latin Hypercube samples across all uncertain input dimensions and execute the DAG for each sample

#### Scenario: LHS produces stratified coverage

- **WHEN** the system generates N LHS samples for a uniform input
- **THEN** each of the N equal-probability strata of the input distribution SHALL contain exactly one sample

### Requirement: Confidence Interval Reporting on Outputs

The system SHALL compute and report confidence intervals for all output nodes after a UQ run. The system MUST report at minimum the 5th, 25th, 50th (median), 75th, and 95th percentiles. The system SHALL also report the mean and standard deviation of each output distribution. Confidence intervals MUST be available for each simulation year individually and for cumulative metrics.

#### Scenario: Report confidence intervals for cumulative GHG emissions

- **WHEN** a UQ run completes for a 10-year scenario
- **THEN** the system SHALL report the 5th, 25th, 50th, 75th, and 95th percentile values for cumulative GHG emissions, along with mean and standard deviation

#### Scenario: Report per-year confidence intervals

- **WHEN** a UQ run completes
- **THEN** the system SHALL provide confidence intervals for each of the 10 simulation years independently, enabling year-by-year uncertainty visualization

### Requirement: Variance-Based Sensitivity Analysis

The system SHALL compute variance-based sensitivity indices (first-order and total-order Sobol indices or equivalent) to quantify how much each uncertain input contributes to output variance. The system MUST use a validated algorithm (e.g., Saltelli's method) for computing Sobol indices. The system SHALL report both first-order indices (direct contribution) and total-order indices (including interactions) for each input parameter.

#### Scenario: Compute Sobol indices for cumulative emissions

- **WHEN** a user requests sensitivity analysis on cumulative GHG emissions with 10,000 samples
- **THEN** the system SHALL compute first-order and total-order Sobol indices for each uncertain input and return them sorted by total-order index descending

#### Scenario: Identify interaction effects via Sobol indices

- **WHEN** the sum of first-order Sobol indices is substantially less than 1.0
- **THEN** the system SHALL flag that significant interaction effects exist between input parameters and report the gap as the interaction contribution

### Requirement: Top-N Uncertainty Driver Identification

The system SHALL identify and rank the top-N input parameters that contribute most to output uncertainty, based on sensitivity analysis results. The default value of N SHALL be 10. The system MUST present the ranking with the parameter name, its sensitivity index, and a human-readable description of the parameter's role in the model.

#### Scenario: Identify top 5 uncertainty drivers

- **WHEN** a user requests the top 5 uncertainty drivers for cumulative GHG emissions
- **THEN** the system SHALL return the 5 input parameters with the highest total-order Sobol indices, each annotated with its name, index value, and description

#### Scenario: Default to top 10 drivers

- **WHEN** a user requests uncertainty drivers without specifying N
- **THEN** the system SHALL return the top 10 drivers by default

### Requirement: Deterministic Mode

The system SHALL support a deterministic execution mode that uses point estimates (distribution means or modes) instead of sampling. In deterministic mode, the DAG SHALL execute exactly once, producing a single value for each output node. Deterministic mode MUST produce results consistent with the median or mean of a UQ run (within numerical tolerance). The system SHALL default to deterministic mode for interactive scenario exploration unless the user explicitly requests UQ.

#### Scenario: Run in deterministic mode

- **WHEN** a user executes a scenario in deterministic mode
- **THEN** the system SHALL use point estimates for all input nodes, execute the DAG once, and return single-valued outputs with no confidence intervals

#### Scenario: Deterministic results are consistent with UQ median

- **WHEN** a user runs the same scenario in both deterministic mode and UQ mode
- **THEN** the deterministic output SHALL be within 5% of the UQ median for all output nodes (given sufficient sample size)

### Requirement: Sample Size Configuration

The system SHALL allow users to configure the number of Monte Carlo samples per UQ run. The system MUST support at minimum two preset modes: **interactive** (100-500 samples, optimized for speed) and **full analysis** (5,000+ samples, optimized for accuracy). Users SHALL also be able to specify a custom sample count. The system MUST warn the user when the requested sample size is insufficient for reliable Sobol index estimation.

#### Scenario: Run in interactive mode

- **WHEN** a user selects "interactive" UQ mode
- **THEN** the system SHALL use 200 samples (or a configurable default within the 100-500 range) and complete the 10-year simulation within 60 seconds

#### Scenario: Run in full analysis mode

- **WHEN** a user selects "full analysis" UQ mode
- **THEN** the system SHALL use 5,000 samples (or a configurable default of 5,000+) and report progress during execution

#### Scenario: Warn on insufficient samples for sensitivity analysis

- **WHEN** a user requests Sobol index computation with only 100 samples
- **THEN** the system SHALL warn that reliable Sobol indices typically require at least 1,000 * (number of inputs + 2) samples and offer to increase the sample count
