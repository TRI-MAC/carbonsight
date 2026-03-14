## ADDED Requirements

### Requirement: GREET lifecycle spot-check for ICEV
The system SHALL compare CarbonSight's per-vehicle ICEV lifecycle emissions against GREET 2024 published values.

#### Scenario: ICEV production emissions in GREET range
- **WHEN** production emissions are computed for a new ICEV (body + ICE powertrain)
- **THEN** per-vehicle production GHG SHALL be within 20% of GREET's ~5,600 kg CO2e (body 4,200 + ICE 1,400)

#### Scenario: ICEV annual usage emissions reasonable
- **WHEN** usage emissions are computed for a single ICEV at average VMT (~12,000 mi/yr) and 25 mpg
- **THEN** annual usage GHG SHALL be within 20% of GREET's ~4,300 kg CO2e/year

### Requirement: GREET lifecycle spot-check for BEV
The system SHALL compare CarbonSight's per-vehicle BEV lifecycle emissions against GREET 2024 published values.

#### Scenario: BEV production emissions in GREET range
- **WHEN** production emissions are computed for a new BEV with 75 kWh battery
- **THEN** per-vehicle production GHG SHALL be within 20% of GREET's ~11,700 kg CO2e (body 4,200 + battery 75*100)

#### Scenario: BEV annual usage emissions reasonable
- **WHEN** usage emissions are computed for a single BEV at average VMT and 100 MPGe on US average grid (0.369 kg/kWh)
- **THEN** annual usage GHG SHALL be within 20% of GREET's ~1,500 kg CO2e/year

### Requirement: VISION fleet composition spot-check
The system SHALL compare CarbonSight's fleet composition trajectory against VISION reference case projections.

#### Scenario: BEV share growth direction
- **WHEN** the 10-year baseline simulation completes
- **THEN** BEV share in the final year SHALL be higher than in year 0

#### Scenario: Total fleet size in VISION range
- **WHEN** the baseline simulation runs
- **THEN** total fleet size SHALL remain between 270M and 300M vehicles throughout the 10-year horizon, consistent with VISION reference case
