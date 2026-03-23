## ADDED Requirements

### Requirement: List available interventions

The API SHALL expose `GET /interventions` returning all pre-built intervention types with their category, description, parameters, default values, and `target_node` identifying which DAG node each intervention modifies.

#### Scenario: Client fetches intervention catalog

- **WHEN** client calls `GET /interventions`
- **THEN** response includes all factory interventions with parameter schemas and a `target_node` field (e.g. `ev_subsidy` has `target_node: "powertrain_proportions"`, `carbon_pricing` has `target_node: "gas_ghg_per_gallon"`)

### Requirement: Scenarios reference interventions by name and parameters

The API SHALL accept intervention specifications in scenario creation/update. Each intervention spec includes the factory name and parameter values. The API SHALL resolve these to `Intervention` objects.

#### Scenario: Create scenario with carbon pricing intervention

- **WHEN** client calls `POST /scenarios` with `{"name": "high_carbon_tax", "interventions": [{"type": "carbon_pricing", "params": {"price_per_tonne": 100}}]}`
- **THEN** scenario is created with the carbon_pricing intervention resolved to year-specific overrides

#### Scenario: Create scenario with multiple interventions

- **WHEN** client calls `POST /scenarios` with two interventions (ev_subsidy + grid_decarbonization)
- **THEN** scenario stores both interventions, combination warnings (if any) included in response

### Requirement: Run scenario applies interventions with year resolution

The `POST /scenarios/{name}/run` endpoint SHALL resolve all scenario interventions to per-year overrides before passing to the engine.

#### Scenario: Running a scenario with time-varying intervention

- **WHEN** client runs a scenario containing a carbon_pricing intervention
- **THEN** engine receives year-specific overrides from the intervention's `get_overrides_for_year()` for each simulation year

#### Scenario: Running a scenario with custom overrides AND interventions

- **WHEN** scenario has both raw overrides and intervention objects
- **THEN** intervention overrides are applied first, then raw overrides take precedence

### Requirement: Sensitivity endpoint returns computed Sobol indices

The `GET /scenarios/{name}/sensitivity` endpoint SHALL return actual Sobol sensitivity indices when the scenario was run in UQ mode, not a placeholder message.

#### Scenario: Fetch sensitivity for UQ scenario

- **WHEN** client calls `GET /scenarios/{name}/sensitivity` after a UQ run
- **THEN** response includes first_order and total_order Sobol indices per input node, plus top-5 drivers ranked by total-order index

#### Scenario: Sensitivity for deterministic scenario

- **WHEN** client calls `GET /scenarios/{name}/sensitivity` after a deterministic run
- **THEN** response returns 400 with message explaining UQ mode is required
