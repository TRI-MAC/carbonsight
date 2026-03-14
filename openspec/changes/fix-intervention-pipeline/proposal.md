## Why

The intervention system is CarbonSight's core differentiator — answering "what if" questions about fleet decarbonization. The domain layer (`interventions.py`) has a rich model with year-specific overrides, multi-intervention combination, and Shapley attribution, but none of it connects through to execution. The engine applies flat overrides to every year, the API doesn't expose interventions, and macro driver outputs (`vmt_adjustment`, `powertrain_preference_shift`) are computed but nothing downstream reads them. The result: the tool cannot answer its primary research question.

## What Changes

- Engine gains `year_overrides` support so time-varying interventions (carbon pricing ramps, grid decarbonization trajectories) apply correctly per year
- Macro driver outputs wire into fleet dynamics: `vmt_adjustment` scales VMT, `powertrain_preference_shift` modulates new vehicle powertrain mix
- API exposes intervention library (list available, compose into scenarios) and wires `Intervention` objects into scenario execution
- Scenario model gains `interventions` field linking to `Intervention` objects with year-specific override support
- ComparePage and SensitivityPage connect to real API data instead of always showing hardcoded demo data
- Sensitivity endpoint returns actual Sobol indices from UQ results

## Capabilities

### New Capabilities
- `year-specific-execution`: Engine and API support for time-varying intervention overrides applied per simulation year
- `intervention-api`: REST endpoints to list, create, and compose interventions; scenarios reference interventions by name
- `macro-fleet-linkage`: Macro driver outputs (VMT adjustment, powertrain preference shift) propagate into fleet dynamics nodes

### Modified Capabilities
- `node-trace-endpoint`: Add intervention metadata to trace responses (which interventions affected this node)
- `node-trace-visualization`: ComparePage and SensitivityPage use real API data; sensitivity endpoint returns computed Sobol indices

## Impact

- **Engine** (`core/engine.py`): New `year_overrides` parameter in `run()`, per-year override merging in both deterministic and UQ loops
- **Scenario** (`core/scenario.py`): `Scenario` dataclass gains `interventions: list[Intervention]` field; store resolves year overrides during execution
- **API** (`app/api.py`): New `/interventions` endpoint group; updated `/scenarios/{name}/run` to resolve interventions; real `/sensitivity` implementation
- **Domain** (`domain/fleet_nodes.py`, `domain/macro_drivers.py`): New compute functions that consume `vmt_adjustment` and `powertrain_preference_shift`
- **Frontend**: ComparePage and SensitivityPage wired to real data; intervention picker sends intervention names (not raw overrides)
- **Tests**: New integration tests for year-varying scenarios; updated API tests for intervention endpoints
