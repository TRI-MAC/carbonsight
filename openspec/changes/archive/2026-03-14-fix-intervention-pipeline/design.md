## Context

CarbonSight's intervention domain layer is fully implemented: 7 factory functions, year-specific overrides, multi-intervention combination with conflict detection, and Shapley attribution. But none of it connects through the execution path. The engine takes flat overrides, the API doesn't expose interventions, and macro driver outputs are dead ends. Three layers need bridging: domain → engine → API → frontend.

Current data flow (broken):

```
Intervention.year_overrides ──→ (never called)
Scenario.overrides ──→ engine.run(overrides=flat_dict) ──→ same dict every year
vmt_adjustment ──→ (nothing reads it)
powertrain_preference_shift ──→ (nothing reads it)
ComparePage ──→ api.compare() ──→ (result discarded, demo data shown)
SensitivityPage ──→ api.getSensitivity() ──→ (placeholder returned)
```

Target data flow:

```
Intervention.get_overrides_for_year(year) ──→ engine merges per year step
Scenario.interventions ──→ API resolves ──→ engine.run(year_overrides={...})
vmt_adjustment ──→ compute_post_vmt_assignment (scales VMT)
powertrain_preference_shift ──→ compute_post_new_entry (modulates mix)
ComparePage ──→ api.compare() ──→ real deltas displayed
SensitivityPage ──→ api.getSensitivity() ──→ computed Sobol indices
```

## Goals / Non-Goals

**Goals:**

- Interventions work end-to-end: define → attach to scenario → run → see time-varying effects
- Macro drivers propagate into fleet dynamics (VMT + powertrain mix)
- ComparePage and SensitivityPage show real data
- All existing tests continue to pass (year_overrides is additive, not breaking)

**Non-Goals:**

- Provenance UI drill-down (separate change)
- Ekiden v1 validation (separate change)
- Persistent scenario storage (in-memory store is sufficient for prototype)
- New intervention types beyond the existing 7 factories

## Decisions

### D1: Year overrides as engine parameter (not Scenario field)

Add `year_overrides: dict[int, dict[str, Any]]` to `engine.run()`. The API layer resolves Intervention objects to year_overrides before calling the engine. This keeps the engine generic and the intervention logic in the API/domain layer.

Alternative considered: Store year_overrides on the Scenario dataclass. Rejected because Scenario is a data storage concern; override resolution is execution logic.

### D2: Intervention resolution in API layer

The API's run endpoint resolves Scenario.interventions → per-year overrides using `combine_interventions_for_year()` before calling `engine.run()`. This leverages the existing domain functions without modifying the engine's interface beyond adding the year_overrides parameter.

### D3: Macro-fleet linkage via new wrapper compute functions

Create two new compute functions in `fleet_nodes.py`:

- `compute_adjusted_vmt(post_vmt_assignment, vmt_adjustment)` — multiplies assigned VMT by the adjustment factor
- `compute_adjusted_new_entry(post_scrappage, powertrain_proportions, renewal_rate, powertrain_preference_shift)` — modulates BEV proportion before calling `add_new_vehicles()`

These slot into the existing DAG between the current nodes. The `vmt_adjustment` and `powertrain_preference_shift` nodes become within-step dependencies of the new nodes.

Alternative considered: Modify existing compute functions to accept optional macro inputs. Rejected because it would change signatures of tested functions and require conditional logic.

### D4: Intervention catalog as static endpoint

`GET /interventions` returns a hardcoded catalog derived from the factory functions. Each entry includes: name, category, description, parameters with types/defaults/ranges. No database needed — the catalog is defined by the code.

### D5: Frontend intervention picker sends structured specs

ScenariosPage currently converts UI selections to raw override dicts client-side. Change to sending `{type: "carbon_pricing", params: {price_per_tonne: 100}}` and let the API resolve. This preserves year-override semantics that are lost when flattening to a dict.

### D6: Fix ComparePage/SensitivityPage by removing demo-data override

Both pages have a bug where `setData(generateDemoData(...))` is called in the `.then()` success path, overriding real API responses. Fix by only calling demo data in the `.catch()` error path.

## Risks / Trade-offs

**[Risk] Macro-fleet linkage changes simulation outputs** → All existing tests were written against the non-linked behavior. Integration tests may need updated expected values. Mitigate by running the full test suite after each node addition.

**[Risk] Year-override merging order is ambiguous** → Document clearly: base overrides < year_overrides < intervention year_overrides. Last writer wins within same priority.

**[Trade-off] Intervention catalog is static, not configurable** → Users can't define custom intervention types via the API. Acceptable for prototype; custom overrides still available as raw dicts.

**[Trade-off] Adjusted VMT/powertrain nodes add DAG complexity** → Two new intermediate nodes. Acceptable because they make the causal chain explicit and auditable, which aligns with RPD's explainability goal.
