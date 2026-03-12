## ADDED Requirements

### Requirement: Fleet Inventory Representation
The system SHALL represent the vehicle fleet as a collection of cohorts, where each cohort is defined by age (0-49 years), powertrain type (ICEV, HEV, PHEV, BEV), and VMT bucket (high, low). The system SHALL track approximately 34 base cohorts (17 ages x 2 VMT buckets) across all 4 powertrains. Each vehicle cohort SHALL carry attributes including age, powertrain, mpg, mpge, battery_kwh, ev_range, and vmt.

#### Scenario: Initial fleet structure
- **WHEN** the simulation is initialized with default parameters
- **THEN** the fleet SHALL contain cohorts spanning ages 0 through 16 across 2 VMT buckets and 4 powertrain types (ICEV, HEV, PHEV, BEV), with each cohort carrying age, powertrain, mpg, mpge, battery_kwh, ev_range, and vmt attributes

#### Scenario: Cohort attribute completeness
- **WHEN** any vehicle cohort exists in the fleet inventory
- **THEN** the cohort SHALL have non-null values for age, powertrain, and vmt, and SHALL have powertrain-appropriate values for mpg (ICEV, HEV), mpge (PHEV, BEV), battery_kwh (PHEV, BEV), and ev_range (PHEV, BEV)

### Requirement: Vehicle Aging
The system SHALL age every vehicle cohort by exactly 1 year at each simulation time step. Aging SHALL be applied before scrappage and new vehicle entry within each annual step.

#### Scenario: Annual aging step
- **WHEN** a simulation time step is executed
- **THEN** every vehicle cohort's age SHALL increase by exactly 1 year

#### Scenario: Aging preserves cohort attributes
- **WHEN** a cohort ages from year N to year N+1
- **THEN** all non-age attributes (powertrain, mpg, mpge, battery_kwh, ev_range) SHALL be preserved, and vmt SHALL be updated according to the VMT-by-age assignment rule

### Requirement: Scrappage Model
The system SHALL apply scrappage using the Greene & Leard survival model to determine the fraction of each cohort that is removed from the fleet at each time step. Vehicles that exceed the maximum age of 50 years SHALL be unconditionally scrapped. The survival model SHALL accept age as input and return a survival probability for each cohort.

#### Scenario: Survival curve application
- **WHEN** scrappage is applied during a time step
- **THEN** the number of vehicles remaining in each cohort SHALL equal the prior count multiplied by the conditional survival probability for the cohort's current age, as defined by the Greene & Leard survival model

#### Scenario: Maximum age scrappage
- **WHEN** a vehicle cohort reaches age 50
- **THEN** the cohort SHALL be entirely removed from the fleet with zero surviving vehicles

#### Scenario: Young vehicles have high survival
- **WHEN** the Greene & Leard survival model is evaluated for vehicles aged 0-5 years
- **THEN** the conditional survival probability SHALL be greater than 0.95

### Requirement: New Vehicle Entry
The system SHALL introduce new vehicles into the fleet at each time step at a configurable renewal rate (default: 5% of current fleet size). New vehicles SHALL be distributed across powertrains according to configurable proportions that default to 82% ICEV, 9% HEV, 2% PHEV, and 7% BEV. New vehicles SHALL enter at age 0.

#### Scenario: Default new vehicle entry
- **WHEN** new vehicles enter the fleet with default parameters
- **THEN** the total number of new vehicles SHALL equal 5% of the current fleet size, distributed as 82% ICEV, 9% HEV, 2% PHEV, and 7% BEV, all at age 0

#### Scenario: Custom powertrain proportions
- **WHEN** a scenario overrides the powertrain proportions (e.g., 50% ICEV, 15% HEV, 5% PHEV, 30% BEV)
- **THEN** new vehicles SHALL be distributed according to the overridden proportions and the proportions SHALL sum to 100%

#### Scenario: Custom renewal rate
- **WHEN** a scenario overrides the renewal rate to a value other than 5%
- **THEN** the total number of new vehicles entering the fleet SHALL reflect the overridden rate applied to the current fleet size

### Requirement: VMT Assignment by Age
The system SHALL assign vehicle miles traveled (VMT) to each cohort based on the cohort's age and VMT bucket (high or low), using data derived from the NHTS 2017 survey. VMT SHALL decrease with vehicle age, and high-VMT-bucket vehicles SHALL have greater VMT than low-VMT-bucket vehicles of the same age.

#### Scenario: VMT decreases with age
- **WHEN** VMT is assigned to cohorts of the same powertrain and VMT bucket
- **THEN** cohorts with higher age SHALL have equal or lower VMT than cohorts with lower age

#### Scenario: VMT bucket differentiation
- **WHEN** two cohorts share the same age and powertrain but differ in VMT bucket
- **THEN** the high-VMT-bucket cohort SHALL have strictly greater VMT than the low-VMT-bucket cohort

#### Scenario: VMT updates on aging
- **WHEN** a cohort ages from year N to year N+1
- **THEN** its VMT SHALL be reassigned according to the NHTS-derived VMT table for the new age and its VMT bucket

### Requirement: Fleet Composition Tracking Over Time
The system SHALL record the full fleet composition at each simulation year across the 10-year horizon. The recorded composition SHALL include the count of vehicles by powertrain type, age distribution, and total fleet VMT. The system SHALL make year-over-year composition data available for downstream analysis and visualization.

#### Scenario: Annual composition snapshot
- **WHEN** a simulation year completes
- **THEN** the system SHALL record the total vehicle count, vehicle count by powertrain (ICEV, HEV, PHEV, BEV), age distribution, and total fleet VMT for that year

#### Scenario: 10-year trajectory
- **WHEN** a full 10-year simulation completes
- **THEN** the system SHALL provide composition data for each of the 10 years, enabling year-over-year comparison of powertrain shares, fleet size, and total VMT

#### Scenario: Powertrain share evolution
- **WHEN** new vehicle entry uses default proportions (7% BEV) and no interventions are applied
- **THEN** the BEV share of the total fleet SHALL increase over the 10-year horizon as new BEVs enter and older ICEVs are scrapped

### Requirement: Used Car Market Dynamics
The system SHALL model used car market reshuffling, where up to 15% of the fleet is circulable (eligible for redistribution) each year. Reshuffling SHALL allow vehicles to move between VMT buckets, reflecting changes in usage patterns as vehicles change owners in the secondary market.

#### Scenario: Reshuffling volume
- **WHEN** used car market dynamics are applied during a time step
- **THEN** the number of vehicles eligible for redistribution SHALL NOT exceed 15% of the current fleet size

#### Scenario: VMT bucket reassignment
- **WHEN** a vehicle is reshuffled through the used car market
- **THEN** the vehicle MAY be reassigned from its current VMT bucket (high or low) to the other bucket, while retaining all other attributes (age, powertrain, mpg, mpge, battery_kwh, ev_range)

#### Scenario: Fleet size conservation
- **WHEN** used car market reshuffling is applied
- **THEN** the total fleet size SHALL remain unchanged -- reshuffling redistributes vehicles but does not add or remove them

### Requirement: Data Validation
The system SHALL validate all fleet dynamics input data on ingest. Survival curves SHALL contain probabilities between 0 and 1 that are monotonically non-increasing with age. VMT tables SHALL contain positive values for all age and bucket combinations. Powertrain proportions for new vehicle entry SHALL sum to 1.0 (within floating-point tolerance). The system SHALL raise a clear error if any validation rule is violated.

#### Scenario: Invalid survival curve
- **WHEN** a survival curve is loaded with a probability value less than 0 or greater than 1
- **THEN** the system SHALL reject the data and raise a validation error identifying the invalid value and its position

#### Scenario: Non-monotonic survival curve
- **WHEN** a survival curve is loaded where the survival probability increases at any age step
- **THEN** the system SHALL reject the data and raise a validation error indicating the non-monotonic age transition

#### Scenario: VMT table missing entries
- **WHEN** a VMT table is loaded that lacks a value for any required age-bucket combination
- **THEN** the system SHALL reject the data and raise a validation error identifying the missing entry

#### Scenario: Powertrain proportions do not sum to one
- **WHEN** powertrain proportions are provided that sum to a value outside the range 0.999 to 1.001
- **THEN** the system SHALL reject the configuration and raise a validation error reporting the actual sum

#### Scenario: Negative VMT values
- **WHEN** a VMT table contains a zero or negative value for any age-bucket combination
- **THEN** the system SHALL reject the data and raise a validation error identifying the invalid entry
