## ADDED Requirements

### Requirement: ComparePage uses real API data
The ComparePage SHALL use the response from `api.compare()` to populate trajectory charts, delta tables, and attribution waterfalls. Demo data SHALL only be used when the API is unavailable.

#### Scenario: Comparison with real scenario data
- **WHEN** user selects two completed scenarios and the API is reachable
- **THEN** the page SHALL display real per-year GHG deltas and attribution from the API response, not hardcoded demo data

#### Scenario: API unavailable fallback
- **WHEN** the API is unreachable
- **THEN** the page SHALL fall back to demo data with a visible "Demo Mode" indicator

### Requirement: SensitivityPage uses real API data
The SensitivityPage SHALL use the response from `api.getSensitivity()` to populate the tornado chart and parameter table. Demo data SHALL only be used when the API is unavailable.

#### Scenario: Sensitivity with real UQ data
- **WHEN** user selects a scenario that was run in UQ mode and the API returns Sobol indices
- **THEN** the page SHALL display real first-order and total-order indices in the tornado chart, not hardcoded demo data

#### Scenario: Deterministic scenario selected
- **WHEN** user selects a scenario that was run in deterministic mode
- **THEN** the page SHALL display a message explaining that UQ mode is required for sensitivity analysis
