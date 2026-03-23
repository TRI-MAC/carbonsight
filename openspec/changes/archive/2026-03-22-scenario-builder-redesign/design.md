## Context

The current `ScenariosPage.tsx` (~1000 lines) uses a two-column layout: scenario list (left) and a monolithic editor panel (right). The editor has a category dropdown that shows one category at a time, number inputs without range context, and no feedback until the user saves and runs manually. There is no connection between interventions and the causal DAG they affect.

Key files:

- `frontend/src/pages/ScenariosPage.tsx` — current scenarios page
- `frontend/src/api/client.ts` — API client with `listInterventions()`, `runScenario()`, `getTrace()`
- `frontend/src/types/index.ts` — TypeScript types for GraphNode, TraceResponse, etc.
- `carbonsight/app/api.py` — `INTERVENTION_CATALOG` (lines 95-156), intervention and scenario endpoints
- `carbonsight/domain/interventions.py` — intervention factory functions mapping types to DAG node overrides

Intervention-to-node mapping (from `interventions.py`):
| Intervention | Target DAG Node |
|---|---|
| carbon_pricing | gas_ghg_per_gallon |
| ev_subsidy | powertrain_proportions |
| vmt_reduction | adjusted_vmt |
| grid_decarbonization | grid_ghg_per_kwh |
| battery_cost_reduction | production_battery_per_kwh |
| scrappage_program | post_scrappage |
| phev_charging_improvement | fleet_usage_ghg |

A deterministic 10-year simulation takes ~1.6 seconds (measured), making auto-run on slider change feasible.

## Goals / Non-Goals

**Goals:**

- Three-column layout showing scenario list, intervention controls, and live impact preview simultaneously
- Slider-based controls with all params visible for every intervention
- Causal path annotations showing the DAG chain from each intervention's target node to total_emissions
- Auto-run deterministic simulation with debounce for live preview (baseline vs current scenario)
- Show GHG trajectory, fleet composition, and 4 delta metric cards in the preview panel

**Non-Goals:**

- Backend API changes beyond adding `target_node` to the catalog
- New endpoints or new simulation modes
- UQ auto-preview (too slow; UQ stays manual via Run button)
- Redesigning other pages

## Decisions

### 1. Three-column layout with fixed widths

**Decision:** Scenario list at 200px, intervention controls at 380px, impact preview fills remaining space.

**Rationale:** The scenario list needs minimal width (just names + status). Controls need enough room for sliders. The preview panel benefits from maximum width for charts.

**Alternatives:** Two-column with controls + preview stacked vertically — rejected because the user can't see both controls and preview without scrolling.

### 2. `useAutoRun` hook with 800ms debounce

**Decision:** A custom hook encapsulates debounce → save scenario → run deterministic → fetch traces. Uses a run ID to discard stale results when the user changes sliders during a run.

**Rationale:** 800ms debounce + 1.6s run = ~2.4s feedback latency. Fast enough to feel responsive with a loading indicator. Stale-result handling prevents flicker.

**Alternatives:** Poll-based approach — rejected because debounce is simpler and sufficient. Server-sent events — overkill for this latency.

### 3. Client-side BFS for causal paths

**Decision:** Fetch graph nodes once on mount via `GET /graph/nodes` (each node has an `upstream` array). Build a downstream adjacency map and BFS from each intervention's `target_node` to `total_emissions`.

**Rationale:** No new backend endpoint needed. The graph has ~35 nodes — BFS is instant. Caching the node list on mount avoids repeated fetches.

**Alternatives:** Backend endpoint for shortest path — unnecessary given the small graph size. Hardcoded paths — brittle and would break if the DAG changes.

### 4. Accordion categories instead of dropdown

**Decision:** All intervention categories rendered as expandable accordion sections, all visible at once (collapsed by default).

**Rationale:** Users need to scan available interventions across categories. A dropdown forces exploring one category at a time. Accordion lets users expand multiple categories simultaneously.

### 5. Range sliders paired with numeric inputs

**Decision:** Each param with min/max gets a range slider and an editable number input sharing the same state. Params without numeric ranges (e.g. `trajectory` dict types) get a simplified control or are handled separately.

**Rationale:** Sliders make it easy to explore a range; numeric inputs allow precision. Together they cover both exploration and exact-value use cases.

## Risks / Trade-offs

**Auto-run may feel sluggish for rapid slider dragging** — The 800ms debounce prevents excessive runs, but users dragging quickly will see a delay. Mitigation: show a "Running simulation..." indicator immediately on debounce start.

**Large ScenariosPage component** — The rewrite adds complexity. Mitigation: extract ImpactPreview, CausalPathChips, and useAutoRun as separate modules. The page itself orchestrates layout and state.

**Dict-type params (trajectory, proportion_shift) don't fit a simple slider** — Some interventions have dict params. Mitigation: for `proportion_shift`, expose the BEV value as a single slider. For `trajectory` params, show a simplified single-value control initially; full trajectory editing is a non-goal.
