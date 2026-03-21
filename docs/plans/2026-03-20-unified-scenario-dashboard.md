# Unified Scenario Dashboard

## Problem

The Dashboard and Compare pages serve related purposes but are disconnected. The Dashboard always shows baseline with no way to switch scenarios. The Compare page requires selecting scenarios before seeing anything useful. Users need a single place to view any scenario's metrics and optionally compare.

## Design

### Page structure

- Scenario selector dropdown at top (defaults to "baseline", shows run status)
- Two tabs: "Overview" (default) and "Compare"
- Overview tab: headline metrics, GHG trajectory by component, fleet composition stacked area -- same as current dashboard but for the selected scenario
- Compare tab: pick a second scenario, trajectory with delta shading/annotations, 5 summary delta cards

### Data flow

- Overview tab: uses `/dashboard` for baseline (cached), or fetches traces for other scenarios
- Compare tab: reuses existing `runComparison` logic with selected scenario as baseline
- Scenario dropdown selection carries into compare tab as the baseline

### File changes

- New: `ScenarioDashboardPage.tsx` (replaces both DashboardPage and ComparePage)
- Keep: `DeltaSummaryCard.tsx`, delta shading logic
- Remove: `DashboardPage.tsx`, `ComparePage.tsx` (functionality merged)
- Update: router to point `/` and `/compare` to new page
