# Scenario Builder Redesign

## Problem

The current ScenariosPage is clunky: a dropdown hides intervention categories, number inputs don't convey parameter ranges, multi-param interventions only show one param, and there's no way to understand how inputs cascade through the causal DAG before running a simulation.

## Design

### Layout: Three-Column

- **Scenario List** (~200px): slim sidebar listing saved scenarios with status badges and "+ New" button
- **Intervention Controls** (~350px): scrollable panel with scenario name, accordion category sections, range sliders, causal path annotations, and save/run buttons
- **Live Impact Preview** (remaining width): auto-updating charts and delta cards comparing current config against baseline

### Intervention Controls

- All categories visible as accordion sections (no dropdown filter)
- Range sliders with min/max and numeric value display for each param
- Human-readable labels mapped from param names (e.g. `price_per_tonne` → "Carbon Price")
- All params shown for multi-param interventions (e.g. scrappage shows age threshold, acceleration factor, duration, start year)
- Causal path annotation below each active intervention: chain of pill chips showing the DAG path from the intervention's target node to `total_emissions`
- Remove "Custom Node Overrides" section (power-user clutter)

### Live Impact Preview

- Auto-runs a deterministic simulation with 800ms debounce after any slider change
- `useAutoRun` hook encapsulates: debounce → save scenario → run deterministic → fetch traces
- Cancels stale results if user changes sliders during a run
- Shows:
  - GHG trajectory chart (baseline dashed, current solid, delta shading)
  - 4 compact delta cards (Total GHG, BEV Share, Fleet Size, Grid Intensity) with final-year value and percentage
  - Fleet composition stacked area chart
- Loading shimmer during ~1.6s computation
- Baseline scenario shows informational message instead of preview

### Causal Path Annotations

- Backend: add `target_node` field to each `INTERVENTION_CATALOG` entry mapping intervention type to the DAG node it modifies
- Frontend: fetch graph edges once on mount via `GET /graph/edges`, compute downstream path from `target_node` to `total_emissions` using BFS
- Render as compact muted pill chain below each active intervention's controls

### Backend Changes

- Add `target_node` to `INTERVENTION_CATALOG` entries (e.g. `ev_subsidy` → `powertrain_preference_shift`)
- Trace endpoint already flattens nested sub-dicts (e.g. `by_powertrain` in `fleet_snapshot`)

### What Stays the Same

- Scenario name input
- Save and Run buttons (Run triggers UQ mode; auto-run is always deterministic)
- Run mode selector (deterministic/UQ)
- Scenario list selection and delete behavior

## Performance

- Deterministic 10-year simulation: ~1.6s (measured)
- 800ms debounce + 1.6s run = ~2.4s total feedback latency — acceptable with loading indicator
- Graph edges fetched once on mount and cached
