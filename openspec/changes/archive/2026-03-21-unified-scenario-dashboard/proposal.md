## Why

The Dashboard and Compare pages serve related purposes but are disconnected. The Dashboard always shows the baseline with no way to switch scenarios. The Compare page requires selecting scenarios before showing anything useful. Users need a single place to view any scenario's metrics and optionally compare against another.

## What Changes

- **Merge Dashboard and Compare into a single page** (`ScenarioDashboardPage`): scenario selector dropdown at top, two tabs ("Overview" and "Compare")
- **Overview tab**: headline metrics, GHG trajectory by component, fleet composition stacked area — same as current dashboard but for any selected scenario
- **Compare tab**: pick a second scenario, trajectory with delta shading/annotations, 5 summary delta cards
- **Remove** separate `DashboardPage.tsx` and `ComparePage.tsx`
- **Update routing** so `/` and `/compare` both go to the new unified page

## Capabilities

### New Capabilities

- `unified-scenario-dashboard`: Single page combining scenario overview and comparison, with scenario selector and tab-based navigation between single-scenario view and comparison mode

### Modified Capabilities

- `visualization`: The Dashboard and Compare views are merged into a single unified page with tab navigation

## Impact

- **Frontend**: New `ScenarioDashboardPage.tsx` replaces `DashboardPage.tsx` and `ComparePage.tsx`. Existing `DeltaSummaryCard.tsx` reused as-is.
- **Router**: `/` and `/compare` routes updated
- **Backend**: No changes. Existing `/dashboard` and trace endpoints used as-is.
- **Tests**: Dashboard and Compare page tests updated for new component
