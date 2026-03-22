## Why

CarbonSight's fleet renewal model computes new vehicle sales as 5.0% of the post-scrappage fleet, which produces an unrealistic shrinking fleet (280M → 264M over 10 years). In reality, US new vehicle sales are primarily driven by macroeconomic factors, not fleet size. The current approach compounds errors over time — a smaller fleet generates fewer new vehicles, which shrinks the fleet further — producing a 45% emissions divergence from Ekiden v1 by year 9 and falling outside VISION's 280-300M reference range.

## What Changes

- Replace percentage-based renewal with a fixed exogenous sales volume (default ~15.5M/year based on 2019-2024 average)
- Add configurable annual sales growth rate (default 0%, option for ~0.5%/year from EIA AEO)
- Update `add_new_vehicles()` to accept an absolute count instead of computing from fleet size × rate
- Update fleet dynamics DAG nodes to wire the new sales volume parameter
- Update validation tests and regenerate validation report to reflect improved Ekiden v1 alignment

## Capabilities

### New Capabilities

- `exogenous-fleet-renewal`: Fixed/configurable new vehicle sales volume decoupled from fleet size, with optional annual growth rate

### Modified Capabilities

## Impact

- `carbonsight/domain/fleet_dynamics.py` — `add_new_vehicles()` signature changes (takes absolute count instead of fleet + rate)
- `carbonsight/domain/fleet_nodes.py` — New DAG nodes for `annual_sales_volume` and `sales_growth_rate`; updated `compute_adjusted_new_entry`
- `carbonsight/core/engine.py` — No changes expected (sales volume flows through DAG)
- `tests/domain/test_fleet_dynamics.py` — Update tests for new `add_new_vehicles` signature
- `tests/test_validation.py` — Regression tolerances may tighten; xfail markers may be removable
- `docs/validation-report.md` — Regenerated with updated results
