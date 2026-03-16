## 1. Fix Intervention Parameter Mapping (ScenariosPage)

- [x] 1.1 Store full `params` array from intervention catalog alongside each category item in state
- [x] 1.2 Replace hardcoded param-name heuristic with `params[0].name` lookup when building intervention specs
- [x] 1.3 Add special-case handling for `ev_subsidy` dict param (wrap value in `{bev: value}`)
- [x] 1.4 Verify intervention specs match API expectations for all 7 intervention types

## 2. Add Run-Status Awareness to ComparePage

- [x] 2.1 Add `runStatus` state tracking per scenario (ready / not-run / checking)
- [x] 2.2 On mount, probe `api.getTrace(name, "total_emissions")` for each scenario to determine run status
- [x] 2.3 Show visual indicator (green dot / grey dot) next to each scenario checkbox based on run status
- [x] 2.4 Disable Compare button when any selected scenario has not been run, with explanatory tooltip or message
- [x] 2.5 Display error message naming specific unrun scenarios when user attempts comparison

## 3. Connect Trajectory Chart to Real Trace Data

- [x] 3.1 After `api.compare()` succeeds, fetch `api.getTrace(name, "total_emissions")` for each selected scenario
- [x] 3.2 Extract `field_values` from trace responses and build chart data series with correct year-by-year values
- [x] 3.3 Remove `generateDemoData()` call and replace with real trace data in trajectory chart
- [x] 3.4 Handle trace fetch failure gracefully — show error indicating which scenario trace failed
- [x] 3.5 Preserve demo-mode fallback when API is entirely unreachable (keep "Demo Mode" indicator)
