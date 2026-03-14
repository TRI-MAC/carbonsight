## ADDED Requirements

### Requirement: VMT adjustment modulates fleet VMT
The `vmt_adjustment` macro driver output SHALL scale the VMT assigned to vehicles in the fleet dynamics pipeline. When oil prices rise, VMT decreases according to the elasticity-based adjustment factor.

#### Scenario: Rising oil prices reduce fleet VMT
- **WHEN** oil_price increases from $75 to $96/bbl over 10 years (default trajectory)
- **THEN** fleet VMT in year 10 is approximately 5-6% lower than year 1 (vmt_adjustment ~0.944)

#### Scenario: Flat oil prices produce no VMT change
- **WHEN** oil_price_trajectory is flat at $75/bbl
- **THEN** vmt_adjustment remains 1.0 for all years and fleet VMT is unaffected

### Requirement: Powertrain preference shift modulates new vehicle mix
The `powertrain_preference_shift` macro driver output SHALL adjust the powertrain proportions used for new vehicle entry. A shift >1.0 increases BEV proportion; <1.0 decreases it.

#### Scenario: Rising oil prices shift preference toward BEV
- **WHEN** oil prices rise over the simulation horizon
- **THEN** BEV share of new vehicles increases relative to the base powertrain_proportions, and ICEV share decreases proportionally

#### Scenario: Preference shift preserves proportion sum
- **WHEN** powertrain_preference_shift is applied to powertrain_proportions
- **THEN** the adjusted proportions still sum to 1.0

### Requirement: Macro driver nodes integrate into full simulation graph
The macro driver nodes SHALL be included in the standard simulation graph alongside fleet and emissions nodes, so that oil_price, electricity_price, vmt_adjustment, and powertrain_preference_shift are computed and available as outputs.

#### Scenario: Full graph includes macro driver outputs
- **WHEN** a 10-year simulation runs with the full graph
- **THEN** year results include oil_price, electricity_price, vmt_adjustment, and powertrain_preference_shift with values varying per year according to trajectories
