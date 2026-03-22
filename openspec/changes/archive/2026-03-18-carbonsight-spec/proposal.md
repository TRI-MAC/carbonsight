## Why

Toyota needs a decision-support tool that lets product strategists and policymakers evaluate the carbon impact of interventions across the US light-duty vehicle fleet over a 10-year horizon. The prior prototype (Ekiden v1) proved the concept — a causal DAG-based simulator with 13 intervention levers — but lacked uncertainty quantification, macro-economic drivers, explainability, and the rigor needed for industry decision-makers. This ground-up rewrite addresses those gaps while targeting a 1-year prototype timeline with 1-2 researchers.

## What Changes

- **New simulation engine**: DAG-based architecture rebuilt from scratch with typed nodes, distribution-based inputs, and provenance tracking baked in from the start
- **Fleet dynamics model**: Vehicle stock turnover (entry, aging, scrappage via Greene & Leard survival model), powertrain composition tracking, and VMT assignment by age/usage bucket — carried forward from Ekiden v1 with improved data structures
- **Lifecycle emissions model**: Component-level GHG (production: body/powertrain/battery, usage: fuel + electricity, disposal) with literature-derived uncertainty ranges instead of point estimates
- **Macro-economic driver layer**: Oil price, electricity price, and consumer preference trajectories that causally propagate through the graph to affect powertrain adoption, VMT, and fleet composition
- **Expanded counterfactual interventions**: 15+ intervention types across policy (carbon pricing, CAFE standards, EV subsidies, ZEV mandates), technology (battery improvements, efficiency, manufacturing decarbonization), behavioral (VMT reduction, PHEV charging, eco-driving), and grid/energy (grid mix scenarios, renewable build-out, smart charging)
- **Uncertainty quantification**: All key parameters carry distributions; outputs report confidence intervals; sensitivity analysis identifies which inputs matter most
- **Explainability**: Every output traceable to data sources and assumptions; intervention attribution decomposes total effect into per-intervention contributions
- **Interactive visualization**: Dashboard designed for non-technical decision-makers, replacing the research-oriented Streamlit prototype

## Capabilities

### New Capabilities

- `simulation-engine`: Core DAG execution framework — typed nodes, topological execution, year-by-year time stepping, scenario management (baseline + counterfactual comparison)
- `fleet-dynamics`: Vehicle stock model — new vehicle entry, aging, scrappage (survival curves), powertrain mix tracking, fleet composition over 10-year horizon
- `emissions-model`: Lifecycle GHG calculation — production (body, powertrain, battery), usage (gasoline + electricity, PHEV utility factor), disposal; component-level with uncertainty ranges
- `macro-drivers`: Exogenous scenario inputs — oil price trajectories, electricity prices, consumer preference parameters, policy parameters; causal links to downstream fleet behavior
- `counterfactual-interventions`: Intervention definition, application, and comparison — policy, technology, behavioral, and grid/energy levers; scenario differencing with attribution
- `uncertainty-quantification`: Distribution propagation through the causal graph, confidence intervals on outputs, variance-based sensitivity analysis, identification of top uncertainty drivers
- `explainability`: Provenance tracing (input → output chains), intervention attribution (decomposing effects), assumption documentation per node, data source lineage
- `visualization`: Interactive dashboard for scenario exploration — causal graph view, scenario comparison charts, uncertainty displays, intervention attribution views; designed for industry decision-makers

### Modified Capabilities

<!-- No existing capabilities to modify — this is a greenfield project -->

## Impact

- **Data dependencies**: Requires EPA powertrain/emissions data, NHTS VMT data, Greene & Leard survival curves, EIA energy price projections, GREET lifecycle factors — all publicly available
- **Tech stack**: Python, open-source (no licensing). Key libraries: NetworkX or similar for DAG, NumPy/Pandas for computation, a UQ library (e.g., SALib for sensitivity analysis), web framework for visualization
- **Validation**: Must validate against GREET (lifecycle values) and VISION (fleet projections) to establish credibility with decision-makers
- **Deployment**: Web application (replaces Streamlit prototype); AWS infrastructure from Ekiden v1 can be adapted
- **Audience shift**: From researchers (Ekiden v1) to industry decision-makers and policymakers — requires higher bar for explainability, polish, and trust
