## 1. Summary Cards Component

- [x] 1.1 Create `DeltaSummaryCard` component with props: metric name, baseline values array, intervention values array, years array
- [x] 1.2 Compute final-year delta (absolute and percentage) and display with directional arrow and color (green for reduction, red for increase)
- [x] 1.3 Add inline sparkline showing the 10-year delta trajectory (intervention − baseline per year)
- [x] 1.4 Implement accordion expand/collapse to show year-by-year detail table (Year, Baseline, Intervention, Delta columns)
- [x] 1.5 Ensure only one card is expanded at a time (accordion behavior)

## 2. Wire Summary Cards into ComparePage

- [x] 2.1 After comparison, fetch `total_emissions` trace for both scenarios and extract `field_values` for: `total_ghg`, `usage_ghg_gas`, `usage_ghg_electric`, `production_ghg`
- [x] 2.2 Fetch `grid_ghg_per_kwh` trace for both scenarios
- [x] 2.3 Render 5 `DeltaSummaryCard` instances (Total GHG, Gas Usage, Electric Usage, Production, Grid Intensity) using the fetched trace data
- [x] 2.4 Remove the flat Delta Breakdown table and its rendering code

## 3. Trajectory Chart Delta Shading

- [x] 3.1 Add shaded area between baseline and intervention lines on the trajectory chart — green where intervention < baseline, red where intervention > baseline
- [x] 3.2 Detect crossover point (if any) where intervention transitions from above to below baseline (or vice versa) and render "Crossover: {year}" annotation
- [x] 3.3 Add final-year annotation showing percentage delta (e.g., "−3.5% by 2033")

## 4. Testing and Polish

- [x] 4.1 Write component test for `DeltaSummaryCard` (renders delta, expands/collapses, sparkline present)
- [x] 4.2 Write component test for ComparePage with mocked API (summary cards render, no flat table present)
- [x] 4.3 Verify all existing frontend tests still pass
