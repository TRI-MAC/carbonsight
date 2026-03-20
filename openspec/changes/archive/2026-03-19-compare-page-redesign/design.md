## Context

The Compare page (`ComparePage.tsx`) currently shows a GHG trajectory line chart and a flat Delta Breakdown table. The table renders every scalar node × year combination from the compare API response — ~170 rows, mostly zero deltas, using raw node names. The target audience is industry decision-makers and policymakers who need to quickly see "does this intervention help, and by how much?"

Key files:
- `frontend/src/pages/ComparePage.tsx` — main page component
- `frontend/src/api/client.ts` — `api.compare()` and `api.getTrace()`
- `carbonsight/app/api.py` — `/compare` returns per-node deltas, `/scenarios/{name}/trace/{node}` returns year-by-year values

The compare API already returns all the data needed. No backend changes required.

## Goals / Non-Goals

**Goals:**
- Replace the flat delta table with scannable summary cards showing key metric deltas
- Add visual delta shading between trajectory lines on the existing chart
- Add annotation callouts for key comparison points (crossover year, final-year delta)
- Make the Compare page immediately useful for sense-checking interventions

**Non-Goals:**
- Backend API changes
- New metrics or computed values (use what the trace endpoint already provides)
- UQ confidence bands on comparison (future work)
- Redesigning the scenario selection UI

## Decisions

### 1. Summary cards with 5 key metrics

**Decision:** Show 5 cards: Total GHG, Gas Usage, Electric Usage, Production, and Grid Intensity. Each card displays the final-year (2033) absolute delta, percentage delta, and a small sparkline showing the 10-year delta trajectory.

**Rationale:** Decision-makers need to answer "what changed and by how much?" at a glance. Five metrics cover the major emission components without overwhelming. The sparkline shows whether the effect is growing or shrinking over time.

**Data source:** Each card fetches `field_values` from the `total_emissions` trace (for GHG components) and the `grid_ghg_per_kwh` trace (for grid intensity). Deltas are computed client-side by subtracting baseline from intervention values.

**Alternatives considered:**
- Use the compare API deltas directly: These include all nodes, requiring filtering. Client-side subtraction of trace values is simpler and gives us the full trajectory for sparklines.
- Fewer cards (just total GHG): Rejected — decision-makers need to see the production vs usage tradeoff (e.g., more BEVs = higher production, lower usage).

### 2. Click-to-expand year-by-year detail on cards

**Decision:** Each summary card is clickable. When expanded, it shows a small table with year, baseline value, intervention value, and delta for that specific metric. Only one card expands at a time (accordion pattern).

**Rationale:** Keeps the default view clean while providing drill-down for anyone who wants the numbers. The accordion prevents the page from becoming as long as the old table.

### 3. Shaded delta area on trajectory chart

**Decision:** Add a filled `Area` between the baseline and intervention lines using recharts' `Area` component. Use green fill (with low opacity) where intervention < baseline, red where intervention > baseline. Add text annotations at the crossover point and at the final year.

**Rationale:** The shaded area makes the magnitude of difference immediately visible. Color coding (green = reduction, red = increase) matches the existing theme conventions. Annotations prevent the user from having to hover to understand key points.

**Implementation:** Use recharts `Area` with a custom shape or `ReferenceArea` segments. For the crossover detection, find the first year where the delta sign changes. Annotations use recharts `Label` or custom SVG overlays.

**Alternatives considered:**
- Separate delta chart below the trajectory: Rejected — adds vertical space and forces the user to correlate two charts mentally.
- Tooltip-only (no shading): Rejected — misses the at-a-glance value.

## Risks / Trade-offs

**Recharts Area between two lines may be tricky** → The built-in `Area` component fills to an axis, not between two series. May need a custom SVG path that traces line1 forward and line2 backward. Fallback: use `ReferenceArea` rectangles per-year as an approximation.

**Hardcoded 5 metrics may not cover all interventions** → Some interventions affect metrics not in the 5 cards (e.g., VMT). Mitigate by choosing the 5 most universal metrics and noting we can add more cards later.

**Client-side delta computation duplicates backend logic** → Acceptable tradeoff. The trace endpoint returns raw values; computing `intervention - baseline` client-side is trivial and avoids a new API endpoint.
