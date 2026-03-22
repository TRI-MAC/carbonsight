## ADDED Requirements

### Requirement: Regression test against Ekiden v1 Total GHG trajectory

The system SHALL include an automated test that runs a 10-year CarbonSight baseline simulation with macro drivers neutralized and compares the per-year Total GHG output against Ekiden v1's known baseline trajectory.

#### Scenario: Baseline Total GHG within tolerance

- **WHEN** a 10-year deterministic baseline simulation is run with `vmt_adjustment=1.0` and `powertrain_preference_shift=1.0`
- **THEN** each year's Total GHG SHALL be within 5% of the corresponding Ekiden v1 value (Year 0: ~1,243 Mt, declining to Year 9: ~1,047 Mt)

#### Scenario: Informative failure message on regression break

- **WHEN** a year's Total GHG exceeds the 5% tolerance
- **THEN** the test failure message SHALL report the year, expected value, actual value, and percentage deviation

### Requirement: Regression test for fleet size consistency

The system SHALL verify that the starting fleet size matches Ekiden v1's ~280 million vehicles and that fleet size evolution is within 1% per year.

#### Scenario: Fleet size at year 0

- **WHEN** the baseline simulation starts
- **THEN** total fleet vehicle count SHALL be within 1% of 280 million

#### Scenario: Fleet size trajectory

- **WHEN** the 10-year simulation completes
- **THEN** each year's total fleet count SHALL be within 1% of the Ekiden v1 reference value

### Requirement: Regression test for powertrain mix at year 0

The system SHALL verify the initial powertrain distribution matches the shared input data.

#### Scenario: Starting powertrain shares

- **WHEN** the baseline simulation starts
- **THEN** ICEV share SHALL be ~79%, HEV ~10%, PHEV ~2%, BEV ~7% (within 2 percentage points each)
