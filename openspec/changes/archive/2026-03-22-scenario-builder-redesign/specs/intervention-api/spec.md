## MODIFIED Requirements

### Requirement: List available interventions

The API SHALL expose `GET /interventions` returning all pre-built intervention types with their category, description, parameters, default values, and `target_node` identifying which DAG node each intervention modifies.

#### Scenario: Client fetches intervention catalog

- **WHEN** client calls `GET /interventions`
- **THEN** response includes all factory interventions with parameter schemas and a `target_node` field (e.g. `ev_subsidy` has `target_node: "powertrain_proportions"`, `carbon_pricing` has `target_node: "gas_ghg_per_gallon"`)
