## Context

The Dashboard (`DashboardPage.tsx`) shows baseline-only metrics from `/dashboard`. The Compare page (`ComparePage.tsx`) shows trajectory + delta cards for two selected scenarios. Both use the same underlying data (traces from the simulation engine) but are disconnected pages with separate data-fetching logic.

Key files:

- `frontend/src/pages/DashboardPage.tsx` — current dashboard (baseline only)
- `frontend/src/pages/ComparePage.tsx` — current compare page
- `frontend/src/components/DeltaSummaryCard.tsx` — delta summary card component
- `frontend/src/api/client.ts` — API client with `getDashboard()`, `getTrace()`, `compare()`
- `carbonsight/app/api.py` — `/dashboard` returns cached baseline summary

## Goals / Non-Goals

**Goals:**

- Single unified page for viewing any scenario and comparing scenarios
- Scenario selector dropdown defaulting to baseline
- Tab-based navigation: "Overview" (dashboard charts) and "Compare" (delta analysis)
- Selected scenario carries into compare tab as the baseline

**Non-Goals:**

- Backend API changes
- New metrics or computed values
- Redesigning the chart components themselves
- Multi-scenario overview (one scenario at a time in Overview tab)

## Decisions

### 1. Single page with tab navigation

**Decision:** Replace DashboardPage and ComparePage with ScenarioDashboardPage. Top of page has scenario selector dropdown. Below it, two tabs: "Overview" and "Compare".

**Rationale:** Users currently navigate between two separate pages to go from "what does this scenario look like?" to "how does it compare?". Tabs keep both views one click apart with shared context (selected scenario).

### 2. Overview tab data source

**Decision:** For the "baseline" scenario, use the existing `/dashboard` endpoint (cached, fast). For any other scenario, fetch `total_emissions` and `fleet_snapshot` traces and reconstruct the same chart data client-side.

**Rationale:** The `/dashboard` endpoint is convenient and cached but only works for baseline. Other scenarios need trace-based reconstruction. This avoids backend changes while supporting any scenario.

**Alternatives considered:**

- Generalize `/dashboard` to accept a scenario name: Requires backend changes (non-goal).
- Always use traces even for baseline: Works but wastes the cached endpoint.

### 3. Compare tab inherits selected scenario

**Decision:** The scenario selected in the top dropdown becomes the "baseline" in compare mode. The compare tab shows a second scenario picker for the intervention.

**Rationale:** Natural mental model — "I'm looking at baseline, now I want to compare it with something." Avoids re-selecting the baseline when switching tabs.

## Risks / Trade-offs

**Trace-based dashboard reconstruction may not perfectly match `/dashboard` output** — The `/dashboard` endpoint does its own rounding and formatting. Client-side trace reconstruction may show slightly different numbers. Acceptable since the differences are cosmetic.

**Two pages worth of code in one component** — ScenarioDashboardPage will be larger than either original page. Mitigate by extracting the Overview and Compare content into sub-components if needed.
