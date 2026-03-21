## 1. Create ScenarioDashboardPage shell

- [x] 1.1 Create `ScenarioDashboardPage.tsx` with scenario selector dropdown (fetches scenario list, defaults to "baseline") and two tabs: "Overview" and "Compare"
- [x] 1.2 Update `App.tsx` routes: point `/` (index) and `/compare` to `ScenarioDashboardPage`
- [x] 1.3 Update `Layout.tsx` nav links if they reference Dashboard/Compare separately

## 2. Overview tab

- [x] 2.1 Move headline metrics rendering from DashboardPage into Overview tab (fleet size, annual GHG, BEV share, VMT)
- [x] 2.2 Move GHG trajectory by component chart from DashboardPage into Overview tab
- [x] 2.3 Move fleet composition stacked area chart from DashboardPage into Overview tab
- [x] 2.4 For baseline scenario, fetch from `/dashboard` endpoint. For other scenarios, fetch `total_emissions` and `fleet_snapshot` traces and reconstruct equivalent chart data

## 3. Compare tab

- [x] 3.1 Move comparison logic from ComparePage into Compare tab: second scenario picker, runComparison, trajectory with delta shading, annotations
- [x] 3.2 Use the top-level selected scenario as the baseline (instead of separate baseline picker)
- [x] 3.3 Wire DeltaSummaryCard rendering and metric trace fetching into the Compare tab

## 4. Cleanup and testing

- [x] 4.1 Remove `DashboardPage.tsx` and `ComparePage.tsx`
- [x] 4.2 Remove old imports from `App.tsx`
- [x] 4.3 Update or replace `DashboardPage.test.tsx` and `ComparePage.test.tsx` with tests for `ScenarioDashboardPage`
- [x] 4.4 Verify all frontend tests pass
