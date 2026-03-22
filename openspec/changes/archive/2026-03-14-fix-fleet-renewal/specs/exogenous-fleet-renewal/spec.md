## ADDED Requirements

### Requirement: New vehicle sales volume is exogenous

The fleet renewal system SHALL use a fixed annual sales volume (not derived from current fleet size) to determine how many new vehicles enter the fleet each year. The default value SHALL be 15,500,000 vehicles/year based on the 2019-2024 US average.

#### Scenario: Baseline renewal with default sales volume

- **WHEN** a simulation year executes with no overrides
- **THEN** the system adds exactly `annual_sales_volume` new vehicles (default 15,500,000), distributed across powertrains by `powertrain_proportions` and split 50/50 between high/low VMT buckets

#### Scenario: Sales volume is overridable

- **WHEN** a scenario specifies `annual_sales_volume` as an override (e.g., 14,000,000)
- **THEN** the system uses the overridden value for new vehicle entry that year

#### Scenario: Sales volume does not depend on fleet size

- **WHEN** the fleet shrinks due to elevated scrappage (e.g., from an intervention)
- **THEN** the number of new vehicles added remains equal to `annual_sales_volume`, unaffected by fleet size changes

### Requirement: Annual sales growth rate

The system SHALL support an optional annual growth rate applied to the base sales volume, compounding each simulation year.

#### Scenario: Zero growth rate (default)

- **WHEN** `sales_growth_rate` is 0.0 (default)
- **THEN** the sales volume remains constant at `annual_sales_volume` for all simulation years

#### Scenario: Positive growth rate

- **WHEN** `sales_growth_rate` is 0.005 (0.5%/year) and `annual_sales_volume` is 15,500,000
- **THEN** year 0 adds 15,500,000, year 1 adds 15,577,500, year 5 adds 15,890,481 (compounding)

### Requirement: Fleet trajectory matches VISION reference range

Under baseline conditions (no interventions, default parameters), the fleet size SHALL remain within the VISION reference range of 260,000,000 to 300,000,000 over a 10-year simulation.

#### Scenario: Baseline fleet stays in VISION range

- **WHEN** a 10-year baseline simulation runs with default parameters
- **THEN** fleet size in every year falls within 260M-300M

#### Scenario: Fleet does not shrink unrealistically

- **WHEN** a 10-year baseline simulation runs with default parameters
- **THEN** the fleet size in year 9 is greater than or equal to the fleet size in year 0
