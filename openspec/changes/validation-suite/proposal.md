## Why

CarbonSight's research program requires validation against Ekiden v1 (regression) and external models (GREET lifecycle, VISION fleet projections) before the stakeholder demo. Without validation, the tool produces numbers but can't claim they're trustworthy. The RPD's success criteria specify: regression within 5%, and external validation "within published uncertainty ranges."

## What Changes

- Add regression validation tests comparing CarbonSight 10-year baseline against Ekiden v1's known Total GHG trajectory (1,243 Mt → 1,047 Mt over 10 years)
- Add GREET lifecycle spot-check tests comparing per-vehicle production, usage, and disposal emissions against GREET 2024 published values
- Add VISION fleet spot-check tests comparing fleet size and powertrain mix evolution against VISION reference case projections
- Create a validation report document summarizing results for stakeholder review
- Add a validation data fixtures file with reference values and their sources

## Capabilities

### New Capabilities
- `regression-validation`: Automated regression tests comparing CarbonSight baseline against Ekiden v1 output trajectory, with configurable tolerance (default 5%)
- `external-validation`: GREET lifecycle and VISION fleet spot-check tests with published reference values and source citations
- `validation-report`: Generated markdown report summarizing all validation results for stakeholder consumption

### Modified Capabilities

## Impact

- New test file: `tests/test_validation.py`
- New data fixtures: `tests/fixtures/validation_references.py`
- New doc: `docs/validation-report.md`
- No changes to existing production code — validation is purely observational
