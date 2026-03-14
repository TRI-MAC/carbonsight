## 1. Engine — Year-Specific Override Support

- [x] 1.1 Add `year_overrides: dict[int, dict[str, Any]] | None` parameter to `engine.run()`, `_run_deterministic()`, and `_run_uq()`
- [x] 1.2 In both execution loops, merge `year_overrides.get(year, {})` into effective overrides per step (year-specific takes precedence over base)
- [x] 1.3 Add engine tests: year-specific override applied correctly, year-specific takes precedence over base, UQ mode with year overrides

## 2. Macro-Fleet Linkage

- [x] 2.1 Add `compute_adjusted_new_entry(post_scrappage, powertrain_proportions, renewal_rate, powertrain_preference_shift)` to `fleet_nodes.py` — modulates BEV proportion by shift factor, normalizes to sum=1.0, delegates to `add_new_vehicles()`
- [x] 2.2 Add `compute_adjusted_vmt(post_vmt_assignment, vmt_adjustment)` to `fleet_nodes.py` — multiplies VMT column by adjustment factor
- [x] 2.3 Update `create_fleet_dynamics_nodes()` to insert the adjusted nodes: `post_new_entry` now uses `compute_adjusted_new_entry`, `post_vmt_assignment` feeds into new `adjusted_vmt` node
- [x] 2.4 Update node pipeline so `post_used_market` reads from `adjusted_vmt` instead of `post_vmt_assignment`
- [x] 2.5 Add tests for adjusted nodes: preference shift increases BEV share, VMT adjustment scales VMT, proportions sum to 1.0
- [x] 2.6 Run full test suite — update any integration test expected values that changed due to macro linkage

## 3. Scenario Model — Intervention Integration

- [x] 3.1 Add `interventions` field to `Scenario` dataclass (list of intervention specs: `{type: str, params: dict}`)
- [x] 3.2 Add `resolve_interventions()` function that converts intervention specs to `Intervention` objects via factory functions
- [x] 3.3 Add `resolve_year_overrides()` that takes a list of `Intervention` objects and returns `dict[int, dict[str, Any]]` using `combine_interventions_for_year()` for each year
- [x] 3.4 Add tests for intervention resolution: single intervention, multiple interventions, unknown type error

## 4. API — Intervention Endpoints

- [x] 4.1 Add `GET /interventions` endpoint returning catalog of available intervention types with category, description, parameter schemas (name, type, default, min, max)
- [x] 4.2 Update `POST /scenarios` and `PUT /scenarios/{name}` to accept `interventions` field
- [x] 4.3 Update `POST /scenarios/{name}/run` to resolve scenario interventions to year_overrides before calling `engine.run()`
- [x] 4.4 Implement real `GET /scenarios/{name}/sensitivity` — call `compute_sobol_indices()` and `identify_top_drivers()` on UQ results, return structured response
- [x] 4.5 Add API tests: intervention catalog, scenario with interventions, run with year resolution, real sensitivity response

## 5. Frontend — Wire Real Data

- [x] 5.1 Fix ComparePage: only call `setData(generateDemoData(...))` in the `.catch()` error path, use real API response in `.then()` success path
- [x] 5.2 Fix SensitivityPage: only call `setSensitivityData(DEMO_SENSITIVITY)` in `.catch()`, use real API response in `.then()`
- [x] 5.3 Update ScenariosPage intervention picker to send structured intervention specs (`{type, params}`) instead of raw override dicts
- [x] 5.4 Add `api.listInterventions()` method to frontend API client
- [x] 5.5 Update ScenariosPage to fetch intervention catalog from API and populate picker dynamically
- [x] 5.6 Add SensitivityPage handling for deterministic-mode scenarios (show message instead of empty chart)
