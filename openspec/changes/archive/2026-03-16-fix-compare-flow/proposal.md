## Why

The Compare Scenarios flow has three bugs that make it unreliable for stakeholder use: the trajectory chart always shows hardcoded fake data even when real simulation results exist, the Compare page gives no indication that scenarios must be run before comparing, and the Scenarios page sends incorrect parameter names for most intervention types. These must be fixed before the tool can be used for real decision-support.

## What Changes

- **Connect trajectory chart to real trace data**: After a successful comparison, fetch per-scenario trace data from the API and build the trajectory chart from actual simulation outputs instead of `generateDemoData()`
- **Add run-status awareness to Compare page**: Show which scenarios have been run (via a lightweight status check), disable comparison for unrun scenarios, and display clear messaging when scenarios need to be run first
- **Fix intervention parameter mapping**: Use the intervention catalog's actual parameter names when building intervention specs, instead of the broken heuristic that hardcodes `"factor"` for VMT reduction and `"value"` for everything else

## Capabilities

### New Capabilities

- `compare-flow-fixes`: Frontend fixes for the compare scenarios workflow — real trace data in charts, run-status indicators, correct intervention parameter mapping

### Modified Capabilities

## Impact

- **Frontend**: `ComparePage.tsx` (trajectory chart rewrite, scenario status display), `ScenariosPage.tsx` (intervention param builder)
- **Backend**: No changes needed — existing trace endpoint and comparison endpoint already support everything required
- **No breaking changes**
