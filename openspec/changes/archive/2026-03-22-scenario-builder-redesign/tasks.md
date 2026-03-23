## 1. Backend: Add target_node to intervention catalog

- [x] 1.1 Add `target_node` field to each entry in `INTERVENTION_CATALOG` in `carbonsight/app/api.py` (carbon_pricing→gas_ghg_per_gallon, ev_subsidy→powertrain_proportions, vmt_reduction→adjusted_vmt, grid_decarbonization→grid_ghg_per_kwh, battery_cost_reduction→production_battery_per_kwh, scrappage_program→post_scrappage, phev_charging_improvement→fleet_usage_ghg)
- [x] 1.2 Update `listInterventions` return type in `frontend/src/api/client.ts` to include `target_node: string`

## 2. Create useAutoRun hook

- [x] 2.1 Create `frontend/src/hooks/useAutoRun.ts` — custom hook that debounces (800ms), saves the scenario, runs a deterministic simulation, fetches `total_emissions` + `fleet_snapshot` + `grid_ghg_per_kwh` traces for both scenario and baseline, computes preview data (trajectories, composition, 4 delta metrics). Uses run ID to discard stale results.

## 3. Create CausalPathChips component

- [x] 3.1 Create `frontend/src/components/CausalPathChips.tsx` — takes `targetNode` string and `graphNodes` array, builds downstream adjacency map from `upstream` arrays, BFS from target to `total_emissions`, renders path as pill chips with `→` arrows using display names

## 4. Create ImpactPreview component

- [x] 4.1 Create `frontend/src/components/ImpactPreview.tsx` — takes preview data, scenario name, loading state, and error. Renders: 4 compact delta cards (Total GHG, BEV Share, Fleet Size, Grid Intensity), GHG trajectory LineChart (baseline dashed, scenario solid, delta shading via ReferenceArea), fleet composition stacked AreaChart. Shows informational message for baseline scenario.

## 5. Rewrite ScenariosPage — three-column layout

- [x] 5.1 Restructure `ScenariosPage.tsx` outer layout to three columns: scenario list (200px), intervention controls (380px), impact preview (flex 1)
- [x] 5.2 Slim down the left column (scenario list) — keep existing load/select/new/delete logic but with tighter padding and 200px width
- [x] 5.3 Build center column: scenario name input, accordion category sections (all categories visible, expandable), checkbox + range slider + numeric input for each param, human-readable param labels, CausalPathChips below each active intervention
- [x] 5.4 Wire right column to ImpactPreview + useAutoRun — call trigger() on slider changes and on scenario selection, auto-save before auto-run
- [x] 5.5 Remove old code: category dropdown, custom node overrides section, old monolithic editor panel

## 6. Tests

- [x] 6.1 Write or update `frontend/src/__tests__/ScenariosPage.test.tsx` — test three-column layout renders, accordion categories visible, toggling intervention shows sliders, baseline shows informational preview message
- [x] 6.2 Verify all frontend tests pass (`npx vitest run`)
- [x] 6.3 Verify all backend tests pass (`pytest tests/ -x -q`)
