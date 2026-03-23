## Why

The Scenarios page is clunky: a dropdown hides intervention categories so users can only see one at a time, number inputs don't convey parameter ranges, multi-param interventions only show the first parameter, and there is no way to understand how inputs cascade through the causal DAG before running a simulation. Users must save, run, then navigate elsewhere to see results — a disconnected, trial-and-error workflow.

## What Changes

- **Replace ScenariosPage with a three-column layout**: scenario list (left), intervention controls (center), live impact preview (right)
- **Intervention controls overhaul**: accordion category sections showing all interventions at once, range sliders with numeric display for every parameter, human-readable labels, causal path annotations showing the DAG chain from each intervention to total_emissions
- **Live impact preview**: auto-runs a deterministic simulation (~1.6s) with debounce after any slider change, shows GHG trajectory comparison (baseline vs current), fleet composition, and 4 delta metric cards
- **Backend: add `target_node` to intervention catalog** so the frontend knows which DAG node each intervention enters
- **Remove "Custom Node Overrides"** section (unused power-user feature)

## Capabilities

### New Capabilities

- `scenario-builder`: Three-column scenario creation page with slider-based intervention controls, causal path annotations, and debounced live impact preview comparing against baseline

### Modified Capabilities

- `intervention-api`: Add `target_node` field to each intervention catalog entry mapping intervention type to the DAG node it modifies
- `visualization`: The Scenario Configuration UI requirement changes from a basic form to a three-column builder with live preview

## Impact

- **Frontend**: `ScenariosPage.tsx` rewritten. New components: `ImpactPreview.tsx`, `CausalPathChips.tsx`. New hook: `useAutoRun.ts`. API client type updated for `target_node`.
- **Backend**: `INTERVENTION_CATALOG` in `api.py` gains `target_node` field per entry. No new endpoints.
- **Tests**: ScenariosPage tests updated for new layout. New component tests for ImpactPreview and CausalPathChips.
