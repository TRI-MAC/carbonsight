## ADDED Requirements

### Requirement: Production Emissions

The system SHALL calculate production-phase GHG emissions as the sum of three components: body production, powertrain production, and battery production. Body production emissions SHALL default to approximately 4200 kg CO2e per vehicle. ICE powertrain production emissions SHALL default to approximately 1400 kg CO2e per vehicle. Battery production emissions SHALL be calculated as approximately 100 kg CO2e per kWh of battery capacity. Each component value MUST be represented as a distribution, not a point estimate.

#### Scenario: BEV production emissions

- **WHEN** a battery electric vehicle is added to the fleet with a 75 kWh battery pack
- **THEN** the system calculates production GHG as the sum of body (~4200 kg CO2e), powertrain (electric motor, lower than ICE default), and battery (75 * ~100 = ~7500 kg CO2e), each drawn from their respective uncertainty distributions

#### Scenario: ICE vehicle production emissions

- **WHEN** a conventional ICE vehicle is added to the fleet with no battery
- **THEN** the system calculates production GHG as the sum of body (~4200 kg CO2e) and ICE powertrain (~1400 kg CO2e), with battery contribution of zero

#### Scenario: PHEV production emissions

- **WHEN** a plug-in hybrid vehicle is added to the fleet with a 15 kWh battery
- **THEN** the system calculates production GHG as the sum of body, ICE powertrain, and battery (15 * ~100 = ~1500 kg CO2e) components

### Requirement: Usage Emissions - Gasoline

The system SHALL calculate usage-phase GHG emissions from gasoline consumption using the vehicle's fuel economy (MPG), vehicle miles traveled (VMT), and a gasoline carbon intensity factor. The default gasoline carbon intensity SHALL be 8.89 kg CO2 per gallon. The gasoline carbon intensity MUST support variation over time to model biofuel blending scenarios.

#### Scenario: Annual gasoline emissions for an ICE vehicle

- **WHEN** an ICE vehicle with 30 MPG drives 12,000 miles in a given year
- **THEN** the system calculates gasoline usage emissions as (12000 / 30) * 8.89 = approximately 3556 kg CO2 for that year

#### Scenario: Gasoline emissions with biofuel blending

- **WHEN** the gasoline carbon intensity is reduced by 10% in a future year due to biofuel blending policy
- **THEN** the system uses the reduced carbon intensity factor (approximately 8.00 kg CO2/gallon) for that year's gasoline emissions calculation

### Requirement: Usage Emissions - Electricity

The system SHALL calculate usage-phase GHG emissions from electricity consumption using the vehicle's electrical efficiency (kWh per mile), vehicle miles traveled on electricity, and a grid carbon intensity factor. The default grid carbon intensity SHALL be approximately 369 g CO2 per kWh. The grid carbon intensity MUST vary over time to model grid decarbonization trajectories.

#### Scenario: Annual electricity emissions for a BEV

- **WHEN** a BEV consuming 0.30 kWh/mile drives 12,000 miles in a given year with grid intensity of 369 g CO2/kWh
- **THEN** the system calculates electricity usage emissions as 12000 * 0.30 * 0.369 = approximately 1329 kg CO2 for that year

#### Scenario: Electricity emissions under grid decarbonization

- **WHEN** the grid carbon intensity declines from 369 g CO2/kWh in year 1 to 250 g CO2/kWh in year 10 following a decarbonization trajectory
- **THEN** the system uses the year-specific grid carbon intensity for each year's electricity emissions calculation, resulting in declining per-mile electricity emissions over the simulation horizon

### Requirement: PHEV Utility Factor

The system SHALL calculate a PHEV utility factor that determines the fraction of miles driven on electricity versus gasoline. The utility factor SHALL be derived from a polynomial fit based on battery size and MPGe. The remaining fraction (1 - utility factor) SHALL determine the share of miles driven on gasoline. The utility factor MUST be applied when splitting PHEV VMT between electric and gasoline usage emissions.

#### Scenario: PHEV with moderate battery

- **WHEN** a PHEV has a 15 kWh battery and the polynomial utility factor model yields a factor of 0.45
- **THEN** 45% of that vehicle's VMT is attributed to electric drive (subject to electricity emissions) and 55% is attributed to gasoline drive (subject to gasoline emissions)

#### Scenario: PHEV with large battery

- **WHEN** a PHEV has a 30 kWh battery yielding a higher utility factor of 0.75
- **THEN** 75% of VMT is attributed to electric drive and 25% to gasoline drive, reflecting the larger battery's ability to cover more daily driving on electricity

### Requirement: Disposal Emissions

The system SHALL calculate end-of-life disposal GHG emissions for each vehicle when it exits the fleet. The default disposal emissions SHALL be approximately 2800 kg CO2 per vehicle. Disposal emissions MUST be represented as a distribution to capture uncertainty in recycling rates, shredding energy, and landfill impacts.

#### Scenario: Vehicle disposal at end of life

- **WHEN** a vehicle is scrapped and exits the fleet
- **THEN** the system assigns approximately 2800 kg CO2 in disposal emissions for that vehicle, sampled from the disposal emissions distribution

#### Scenario: Disposal emissions across fleet

- **WHEN** 1000 vehicles are scrapped in a given simulation year
- **THEN** the system calculates total disposal emissions as 1000 times the per-vehicle disposal emission value, with aggregate uncertainty reflecting the per-vehicle distribution

### Requirement: Total GHG Aggregation

The system SHALL calculate total fleet lifecycle GHG emissions as the sum of production emissions, usage emissions (gasoline + electricity), and disposal emissions across all vehicles in the fleet for each simulation year. The system SHALL also provide cumulative GHG over the full simulation horizon. The aggregation MUST propagate uncertainty from all component distributions to produce a total GHG distribution with confidence intervals.

#### Scenario: Single-year fleet GHG total

- **WHEN** the fleet contains vehicles with computed production, usage, and disposal emissions for a given year
- **THEN** the system sums all production emissions (for new vehicles entering that year), all usage emissions (for all active vehicles that year), and all disposal emissions (for vehicles scrapped that year) to produce a total annual fleet GHG value with an associated uncertainty range

#### Scenario: Cumulative GHG over simulation horizon

- **WHEN** a 10-year simulation completes
- **THEN** the system reports cumulative total GHG as the sum of all annual totals across the horizon, with uncertainty bounds derived from the propagated component distributions

#### Scenario: Disaggregated GHG reporting

- **WHEN** the user requests emissions breakdown
- **THEN** the system reports total GHG disaggregated by lifecycle phase (production, usage-gasoline, usage-electricity, disposal) and by powertrain type (ICE, HEV, PHEV, BEV)

### Requirement: Uncertainty Ranges on Emission Factors

All emission factors and parameters in the emissions model MUST be represented as probability distributions rather than point estimates. This includes but is not limited to: body production emissions, powertrain production emissions, battery production emissions per kWh, gasoline carbon intensity, grid carbon intensity, disposal emissions, PHEV utility factor coefficients, and vehicle fuel economy. The system SHALL sample from these distributions during Monte Carlo simulation runs to produce output distributions with quantifiable confidence intervals.

#### Scenario: Distribution-based production factor

- **WHEN** the body production emission factor is defined as a distribution (e.g., Normal with mean 4200 and standard deviation 400 kg CO2e)
- **THEN** each Monte Carlo sample draws a value from that distribution, and the resulting production emissions output reflects the full range of uncertainty

#### Scenario: Confidence intervals on fleet emissions

- **WHEN** a simulation completes with N Monte Carlo samples
- **THEN** the system reports emission outputs with median, 5th percentile, and 95th percentile values, representing the 90% confidence interval derived from propagated input uncertainties

#### Scenario: Sensitivity identification

- **WHEN** uncertainty analysis is performed on the emissions model
- **THEN** the system identifies which emission factor distributions contribute most to variance in total fleet GHG, enabling prioritization of data refinement efforts

### Requirement: Time-Varying Emission Factors

The system SHALL support emission factors that change over the simulation time horizon. Grid carbon intensity MUST follow a configurable decarbonization trajectory (e.g., declining from a baseline value year over year). Gasoline carbon intensity MUST support time-varying profiles to model biofuel adoption. Battery production emissions per kWh MUST support time-varying profiles to model manufacturing decarbonization. Each time-varying factor SHALL be defined as a year-indexed series of distributions.

#### Scenario: Grid decarbonization trajectory

- **WHEN** a grid decarbonization scenario specifies intensity declining from 369 g CO2/kWh in year 1 to 200 g CO2/kWh in year 10
- **THEN** the system applies the year-specific grid carbon intensity distribution to electricity emissions calculations in each simulation year

#### Scenario: Battery manufacturing improvement

- **WHEN** battery production emissions are projected to decline from 100 kg CO2/kWh to 65 kg CO2/kWh over the simulation horizon due to manufacturing decarbonization
- **THEN** vehicles entering the fleet in later years receive lower battery production emissions than those entering in earlier years, with each year's value drawn from the year-specific distribution

#### Scenario: Stable gasoline baseline

- **WHEN** no biofuel blending policy is active
- **THEN** the gasoline carbon intensity remains at its baseline distribution (centered on 8.89 kg CO2/gallon) for all simulation years
