## Context

CarbonSight currently computes new vehicle entry as `post_scrappage_fleet_size × 0.05`, which creates a feedback loop where smaller fleets produce fewer new vehicles, compounding into unrealistic fleet decline (280M → 264M over 10 years). Analysis shows the US fleet has been slowly growing, with sales driven by macroeconomic factors (~15.3M/year average 2019-2024), not fleet size.

Ekiden v1 uses `pre_scrappage_fleet_size × 0.052`, which coincidentally produces a stable fleet but for the wrong structural reason.

## Goals / Non-Goals

**Goals:**

- Replace percentage-based renewal with fixed exogenous sales volume
- Produce a realistic baseline fleet trajectory (slow growth, within VISION 280-300M range)
- Maintain backward compatibility for scenario overrides and intervention analysis
- Improve regression alignment with Ekiden v1

**Non-Goals:**

- Econometric modeling of sales (price elasticity, interest rates, etc.) — that's a future macro driver
- Changing scrappage logic (survival curves are validated)
- Matching Ekiden v1 exactly (structural differences in temporal feedback loop remain)

## Decisions

### 1. Fixed sales volume over percentage-based renewal

**Decision:** Use `annual_sales_volume = 15_500_000` as an exogenous DAG input node.

**Alternatives considered:**

- _5.2% of pre-scrappage (Ekiden v1)_: Produces stable fleet by coincidence, but sales shouldn't depend on fleet size. Interventions that change scrappage would incorrectly alter sales.
- _5.0% of post-scrappage (current)_: Unrealistic shrinking fleet, compounds errors.
- _Replace scrapped + growth_: More mechanistic but couples sales to scrappage, which isn't how the market works.

**Rationale:** Fixed volume is the simplest, most defensible baseline. Real sales are primarily demand-driven. Decoupling from fleet size means interventions affecting scrappage don't artificially change sales counts.

### 2. Growth rate as separate parameter

**Decision:** Add `sales_growth_rate` (default 0.0) applied as compound growth: `volume × (1 + rate)^year_index`.

**Rationale:** VISION projects slow fleet growth. A 0% default is the most neutral baseline, but 0.3-0.5% matches historical trends. Keeping it separate from the base volume makes it easy to explore scenarios.

### 3. Modify `add_new_vehicles` to accept absolute count

**Decision:** Change `add_new_vehicles(fleet, proportions, renewal_rate)` → `add_new_vehicles(fleet, proportions, n_new)` where `n_new` is the total new vehicle count.

**Rationale:** The function currently computes `n_new = fleet_size × rate` internally. Accepting an absolute count is simpler and makes the function agnostic to how the count was derived.

### 4. Replace `renewal_rate` DAG node with `annual_sales_volume` and `sales_growth_rate`

**Decision:** Remove the `renewal_rate` scalar node. Add two new scalar nodes: `annual_sales_volume` (default 15,500,000) and `sales_growth_rate` (default 0.0). The compute node for new entry will calculate the year-specific count using `volume × (1 + rate)^year_index`.

**Rationale:** Clean replacement — the renewal_rate concept is superseded. Keeping both would create confusion about which controls fleet entry.

## Risks / Trade-offs

- **[Regression break]** Changing renewal logic will shift all validation numbers. → Mitigation: Regenerate validation report, expect improved Ekiden v1 alignment for fleet size trajectory. GHG trajectory may or may not improve depending on per-vehicle emission differences.
- **[Existing tests]** Tests that use `renewal_rate` parameter will break. → Mitigation: Update all call sites. The change is mechanical.
- **[Year index dependency]** Growth rate compounding requires knowing which simulation year we're in. → Mitigation: The engine already tracks year index; pass it through the DAG or compute in the node function.
