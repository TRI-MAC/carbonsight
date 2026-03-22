## ADDED Requirements

### Requirement: Engine applies year-specific overrides

The engine SHALL accept a `year_overrides` parameter mapping year (int) to override dicts. During each year step, the engine SHALL merge the base overrides with that year's specific overrides (year-specific taking precedence).

#### Scenario: Carbon pricing ramp over 5 years

- **WHEN** engine runs with `year_overrides={2026: {"carbon_tax": 25}, 2027: {"carbon_tax": 50}}`
- **THEN** years 2024-2025 use base overrides only, 2026 applies carbon_tax=25, 2027+ applies carbon_tax=50

#### Scenario: Year overrides merge with base overrides

- **WHEN** engine runs with `overrides={"renewal_rate": 0.06}` and `year_overrides={2026: {"grid_ghg_per_kwh": 0.30}}`
- **THEN** year 2026 has both renewal_rate=0.06 AND grid_ghg_per_kwh=0.30

#### Scenario: Year override takes precedence over base

- **WHEN** engine runs with `overrides={"oil_price": 75}` and `year_overrides={2026: {"oil_price": 100}}`
- **THEN** year 2026 uses oil_price=100, all other years use oil_price=75

### Requirement: Intervention objects resolve to year-specific overrides

The engine SHALL accept `Intervention` objects and call `get_overrides_for_year(year)` for each simulation year, combining results via `combine_interventions_for_year()`.

#### Scenario: Grid decarbonization trajectory intervention

- **WHEN** a scenario uses a `grid_decarbonization` intervention with year_overrides for each year
- **THEN** each simulation year receives its specific grid_ghg_per_kwh value from the intervention

#### Scenario: Multiple interventions combined per year

- **WHEN** a scenario uses both `carbon_pricing` and `ev_subsidy` interventions
- **THEN** overrides from both are combined per year with conflict warnings, applied in category order (policy before technology)

### Requirement: UQ mode supports year-specific overrides

The UQ execution path SHALL apply the same year-specific override logic as deterministic mode, merging year overrides with per-sample distribution overrides.

#### Scenario: UQ with time-varying policy

- **WHEN** UQ mode runs with year_overrides and distribution inputs
- **THEN** each Monte Carlo sample applies year-specific overrides alongside sampled distribution values
