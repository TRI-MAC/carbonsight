## 1. Core Fleet Dynamics Changes

- [x] 1.1 Change `add_new_vehicles()` in `fleet_dynamics.py` to accept `n_new` (absolute count) instead of computing from `fleet_size × renewal_rate`
- [x] 1.2 Update `step_fleet_one_year()` to accept and pass through `n_new` instead of `renewal_rate`
- [x] 1.3 Update all existing tests in `test_fleet_dynamics.py` for the new `add_new_vehicles` signature

## 2. DAG Node Wiring

- [x] 2.1 Replace `renewal_rate` node with `annual_sales_volume` (default 15,500,000) and `sales_growth_rate` (default 0.0) nodes in `fleet_nodes.py`
- [x] 2.2 Update `compute_adjusted_new_entry` (and `compute_post_new_entry`) to compute `n_new = annual_sales_volume * (1 + sales_growth_rate) ** year_index` and pass absolute count to `add_new_vehicles`
- [x] 2.3 Wire year index into the new entry compute function (via engine context or node parameter)
- [x] 2.4 Update `create_fleet_dynamics_nodes()` signature — remove `renewal_rate`, add `annual_sales_volume` and `sales_growth_rate`

## 3. Update Callers and Integration

- [x] 3.1 Update `build_graph()` in `generate_validation_report.py` and `test_validation.py` (remove renewal_rate references)
- [x] 3.2 Update any other callers of `create_fleet_dynamics_nodes` (search for all usages)
- [x] 3.3 Run full test suite, fix any remaining breakage from signature changes

## 4. Validation

- [x] 4.1 Run baseline simulation and verify fleet trajectory stays within VISION 260M-300M range
- [x] 4.2 Verify fleet does not shrink over 10-year baseline (year 9 >= year 0)
- [x] 4.3 Update xfail markers in `test_validation.py` if regression alignment improves
- [x] 4.4 Regenerate `docs/validation-report.md` and review updated deltas
- [ ] 4.5 Commit all changes
