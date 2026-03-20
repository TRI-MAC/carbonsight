## Why

The Compare page's Delta Breakdown table is unusable for decision-makers. It renders every node × year combination as a flat list (~170 rows), most showing 0.0 deltas, uses raw node names (`production_battery_per_kwh`), and labels everything as "Mt CO2e" even for elasticities and proportions. The actual signal — which interventions matter and by how much — is buried in noise.

## What Changes

- **Replace the delta table with summary cards**: Show 4-5 key metrics (total GHG, usage emissions, production emissions, grid intensity, BEV share) as cards with headline delta numbers, direction arrows, and sparkline trends. Click to expand year-by-year detail.
- **Add visual delta to the trajectory chart**: Shade the area between baseline and intervention lines (green where intervention is lower, red where higher). Add annotation callouts at key points (crossover year, final-year delta).
- **Remove the raw delta table entirely**: The flat node × year table is replaced by the two new display modes above.

## Capabilities

### New Capabilities
- `compare-delta-display`: Summary cards and visual delta overlay for scenario comparison — replaces the flat delta table with scannable cards and an annotated trajectory chart

### Modified Capabilities
- `visualization`: The Compare page's delta breakdown section is being redesigned from a flat table to summary cards + annotated chart

## Impact

- **Frontend only**: `ComparePage.tsx` — delta table replaced with new components
- **No backend changes**: Uses existing compare and trace API endpoints
- **New components**: Summary card component, delta shading on trajectory chart
- **Dependencies**: May need a recharts `Area` or custom SVG for the shaded delta region
