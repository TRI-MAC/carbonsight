## Context

CarbonSight is a 10-year fleet carbon simulator. The RPD requires validation against:

1. **Ekiden v1** (regression): Total GHG trajectory should match within 5%
2. **GREET 2024** (lifecycle): Per-vehicle emissions in the right ballpark
3. **VISION** (fleet): Fleet size and powertrain mix evolution reasonable

Ekiden v1 baseline output exists locally at `/Users/andrewtaber/Projects/counterfactual_calculator/backend/multiple_scenarios/outputs/`. CarbonSight shares the same emission factor defaults (4,200 kg body, 1,400 kg ICE, 100 kg/kWh battery, 8.89 kg CO2/gal, 0.369 kg CO2/kWh grid, 2,800 kg disposal) and fleet inventory data.

Key difference: CarbonSight now has macro-economic drivers (oil price elasticity on VMT/powertrain preference) that Ekiden v1 lacked. Regression tests must control for this.

## Goals / Non-Goals

**Goals:**

- Automated pytest-based validation that runs with the rest of the test suite
- Hardcoded reference values with source citations (no external file downloads)
- Clear pass/fail with informative messages when tolerances are exceeded
- A readable validation report for stakeholders

**Non-Goals:**

- Exact numerical match (different implementations will have minor differences)
- Automated GREET/VISION data fetching or parsing
- Continuous validation against live external data sources
- Fixing any discrepancies found (that's a separate change)

## Decisions

### 1. Regression test runs with macro drivers neutralized

**Decision:** For the Ekiden v1 regression comparison, override macro-driver outputs to neutral values (`vmt_adjustment=1.0`, `powertrain_preference_shift=1.0`) so the comparison is apples-to-apples.

**Rationale:** Ekiden v1 had no macro drivers. If we leave them active, any difference could be macro drivers or a bug — we can't distinguish. A separate test can show the macro-driver delta.

**Alternative considered:** Compare with macro drivers active and use a wider tolerance. Rejected because it defeats the purpose of regression validation.

### 2. Reference values hardcoded in a fixtures module

**Decision:** Store Ekiden v1 trajectory and GREET/VISION reference values in `tests/fixtures/validation_references.py` with inline source citations.

**Rationale:** No external dependencies, version-controlled, reviewable. The values change rarely (only when reference data is updated).

**Alternative considered:** CSV files or JSON fixtures. Rejected because Python module allows inline documentation per value.

### 3. Tolerance structure

**Decision:** Use per-metric tolerances:

- Regression Total GHG: 5% relative (per RPD)
- Regression fleet size: 1% relative
- GREET per-vehicle lifecycle: 20% relative (GREET's own uncertainty ranges are ~15-25%)
- VISION fleet composition: 10% absolute for powertrain shares

**Rationale:** Different metrics have different natural variance. A single tolerance would be too loose for fleet size or too tight for lifecycle emissions.

### 4. Validation report as generated markdown

**Decision:** A script or test that writes `docs/validation-report.md` with actual vs. expected values, pass/fail status, and source citations.

**Rationale:** Stakeholders need a readable document, not pytest output. Generated from the same test data ensures consistency.

## Risks / Trade-offs

- **[Risk] CarbonSight may not match Ekiden v1 within 5%** → This is informative, not a blocker. The test captures the delta and the report explains likely causes (fleet feedback loop, new scrappage model, powertrain mix evolution differences).
- **[Risk] GREET reference values depend on specific vehicle assumptions** → Mitigate by using GREET's published "average" vehicles, not specific models. Document assumptions.
- **[Risk] VISION projections are scenario-dependent** → Use VISION's "Reference" case only. Document which VISION version.
