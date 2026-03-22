### Requirement: VMT adjustment modulates fleet VMT

The `vmt_adjustment` macro driver output SHALL scale the VMT assigned to vehicles in the fleet dynamics pipeline. When oil prices rise, VMT decreases according to the elasticity-based adjustment factor.

#### Scenario: Rising oil prices reduce fleet VMT

- **WHEN** oil_price increases from $75 to $96/bbl over 10 years (default trajectory)
- **THEN** fleet VMT in year 10 is approximately 5-6% lower than year 1 (vmt_adjustment ~0.944)

#### Scenario: Flat oil prices produce no VMT change

- **WHEN** oil_price_trajectory is flat at $75/bbl
- **THEN** vmt_adjustment remains 1.0 for all years and fleet VMT is unaffected

### Requirement: Powertrain preference shift modulates new vehicle mix

The `powertrain_preference_shift` macro driver output SHALL adjust the powertrain proportions used for new vehicle entry. The shift combines the effects of oil price and electricity price via independent elasticities. A shift >1.0 increases BEV proportion; <1.0 decreases it.

#### Scenario: Rising oil prices shift preference toward BEV

- **WHEN** oil prices rise over the simulation horizon
- **THEN** BEV share of new vehicles increases relative to the base powertrain_proportions, and ICEV share decreases proportionally

#### Scenario: Preference shift preserves proportion sum

- **WHEN** powertrain_preference_shift is applied to powertrain_proportions
- **THEN** the adjusted proportions still sum to 1.0

#### Scenario: Rising electricity prices dampen BEV preference

- **WHEN** electricity price increases from baseline over the simulation horizon
- **THEN** the powertrain preference shift decreases (closer to or below 1.0), reducing BEV share relative to what oil price alone would produce

#### Scenario: Flat electricity prices produce no electricity effect

- **WHEN** electricity_price_trajectory is flat at its baseline value
- **THEN** the electricity component contributes a factor of 1.0 and powertrain_preference_shift equals the oil-only effect

#### Scenario: Combined oil and electricity effects

- **WHEN** oil prices rise (favoring BEV) and electricity prices also rise (disfavoring BEV)
- **THEN** the powertrain preference shift is the product of both effects: `oil_effect * electricity_effect`

### Requirement: Macro driver nodes integrate into full simulation graph

The macro driver nodes SHALL be included in the standard simulation graph alongside fleet and emissions nodes, so that oil_price, electricity_price, vmt_adjustment, and powertrain_preference_shift are computed and available as outputs.

#### Scenario: Full graph includes macro driver outputs

- **WHEN** a 10-year simulation runs with the full graph
- **THEN** year results include oil_price, electricity_price, vmt_adjustment, and powertrain_preference_shift with values varying per year according to trajectories

### Requirement: EV electricity price elasticity input node

The macro driver system SHALL include an `ev_elec_price_elasticity` input node (scalar, default -0.05, adjustable) that controls how strongly electricity price changes affect BEV adoption preference.

#### Scenario: Default elasticity value

- **WHEN** `create_macro_driver_nodes()` is called with defaults
- **THEN** the `ev_elec_price_elasticity` node has value -0.05

#### Scenario: Custom elasticity value

- **WHEN** `create_macro_driver_nodes()` is called with a custom `MacroDriverDefaults` specifying `ev_elec_price_elasticity=0.0`
- **THEN** electricity price has no effect on powertrain preference shift
