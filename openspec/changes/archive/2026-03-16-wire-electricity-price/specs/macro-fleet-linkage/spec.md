## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: EV electricity price elasticity input node
The macro driver system SHALL include an `ev_elec_price_elasticity` input node (scalar, default -0.05, adjustable) that controls how strongly electricity price changes affect BEV adoption preference.

#### Scenario: Default elasticity value
- **WHEN** `create_macro_driver_nodes()` is called with defaults
- **THEN** the `ev_elec_price_elasticity` node has value -0.05

#### Scenario: Custom elasticity value
- **WHEN** `create_macro_driver_nodes()` is called with a custom `MacroDriverDefaults` specifying `ev_elec_price_elasticity=0.0`
- **THEN** electricity price has no effect on powertrain preference shift
