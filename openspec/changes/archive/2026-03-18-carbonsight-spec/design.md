## Context

CarbonSight is a ground-up rewrite of Ekiden v1, a causal DAG-based simulator for US automotive fleet carbon emissions. Ekiden v1 proved the approach works: 28 nodes in a directed acyclic graph, 13 intervention levers, 10-year time stepping, Streamlit UI. But it used point estimates, treated interventions as independent sliders, had no formal UQ or explainability, and targeted researchers rather than decision-makers.

This design establishes the architecture for CarbonSight v2: same core concept, but with macro-economic drivers, uncertainty quantification, explainability, and a decision-maker-grade interface. The team is 1-2 people with a 1-year prototype timeline, so the architecture must be simple enough to build and maintain at that scale while supporting the full feature set.

**Key constraints:**

- Python, open-source stack only
- Must be extensible (new node types, new interventions) without architectural changes
- UQ must be integrated from the start, not bolted on
- Explainability is a first-class concern, not an afterthought
- Interactive performance: full 10-year scenario with UQ < 60 seconds

## Goals / Non-Goals

**Goals:**

- Clean separation between simulation engine, domain models, UQ, and presentation
- A node/graph abstraction that makes adding new variables and interventions trivial
- Distribution-aware computation throughout (not point estimates with UQ as a wrapper)
- Provenance tracking that records how every output was produced
- Scenario management that supports baseline vs. counterfactual comparison natively
- Validation-friendly architecture (easy to compare against GREET, VISION)

**Non-Goals:**

- Real-time streaming or event-driven architecture — this is batch simulation
- Multi-user collaboration or concurrent editing
- Plugin/extension system for external contributors (internal tool)
- Mobile or offline support
- GPU acceleration or distributed computing

## Decisions

### 1. Layered architecture with clear boundaries

**Decision:** Organize the codebase into four layers: **core** (simulation engine), **domain** (fleet/emissions/macro models), **analysis** (UQ, explainability), and **app** (visualization, API).

**Rationale:** Ekiden v1 mixed simulation logic, UI code, and data management. This made it hard to test, extend, or swap components. Clear layers let us develop and test the simulation engine independently from the UI, and add UQ without touching domain logic.

**Alternatives considered:**

- Monolithic (like Ekiden v1): Faster to start but becomes unmaintainable as complexity grows. Rejected.
- Microservices: Overkill for 1-2 person team. Rejected.

```
carbonsight/
  core/           # DAG engine, node types, execution, provenance
  domain/         # Fleet dynamics, emissions, macro drivers, interventions
  analysis/       # UQ (distribution propagation, sensitivity), explainability
  app/            # Web UI, API endpoints, visualization
  data/           # Data loaders, schemas, validation
```

### 2. Typed node system with distribution-native values

**Decision:** Each node in the DAG has a declared type (scalar, timeseries, distribution, dataframe) and compute functions operate on these types natively. Distributions are not a separate mode — they are the default representation for uncertain quantities.

**Rationale:** Ekiden v1 stored all values as scalars or DataFrames and had no concept of uncertainty. Bolting UQ onto a point-estimate system is fragile. By making distributions a core value type, UQ is automatic — run the graph once and you get confidence intervals.

**Implementation approach:**

- Scalar nodes can hold a point value or a distribution (e.g., `Normal(mean=369, std=20)` for grid carbon intensity)
- Compute functions receive samples when running in UQ mode (Monte Carlo propagation) or point values in deterministic mode
- The engine handles sampling and aggregation — domain code doesn't need to know about UQ

**Alternatives considered:**

- Analytical uncertainty propagation (error propagation formulas): Only works for linear/near-linear functions. Our graph has nonlinear interactions (utility factors, scrappage curves). Rejected for primary approach, but could be used for quick sensitivity screening.
- Polynomial chaos expansion: More efficient than Monte Carlo for smooth functions but adds significant complexity. Consider as a future optimization if performance requires it.

### 3. Provenance as a built-in execution trace

**Decision:** Every graph execution produces a provenance record: which nodes were computed, what inputs they received, what data sources those inputs came from, and what assumptions were active. This is stored as structured metadata alongside results, not reconstructed after the fact.

**Rationale:** Explainability for decision-makers requires being able to answer "why does this scenario show X?" at any level of detail. Post-hoc reconstruction is error-prone and incomplete. Recording provenance during execution is reliable and complete.

**Implementation approach:**

- Each node execution logs: input values (or distribution parameters), data source references, active assumptions, compute function version
- Scenario results include the full provenance trace
- The explainability layer queries this trace to produce attribution reports and provenance chains

### 4. Scenario-first design

**Decision:** The primary unit of work is a **Scenario** — a named configuration of all input nodes (values or distributions) plus metadata. The system always computes at least two scenarios (baseline + intervention) and reports differences.

**Rationale:** CarbonSight's core value proposition is counterfactual comparison. Making scenarios first-class objects (not ad-hoc parameter overrides) ensures consistent comparison, reproducibility, and clean UX.

**Implementation approach:**

- A Scenario is a serializable configuration (YAML/JSON) specifying input node overrides from defaults
- The engine runs scenarios independently and produces a ScenarioResult with full outputs and provenance
- Comparison functions compute deltas, attribution, and statistical significance between scenario pairs

### 5. Macro-driver integration via causal links in the DAG

**Decision:** Macro-economic drivers (oil price, electricity price, consumer preferences) are modeled as input nodes in the same DAG, with explicit causal edges to the nodes they influence (e.g., oil price → VMT, oil price → powertrain preference).

**Rationale:** The key insight motivating CarbonSight v2 is that interventions have indirect effects. A carbon tax changes fuel prices, which changes VMT _and_ shifts powertrain preferences _and_ affects used car market values. Modeling these as causal links in the DAG (rather than independent sliders) captures these propagation effects naturally.

**Implementation approach:**

- Macro drivers are exogenous timeseries nodes (10-year trajectories from EIA, user scenarios, etc.)
- Causal links to downstream nodes use elasticity-based or regression-based transfer functions from transportation economics literature
- Example: `oil_price → vmt` with price elasticity of demand for driving (~-0.2 short-run, ~-0.6 long-run per literature)

**Alternatives considered:**

- Separate macro-economic model feeding into fleet model: Adds architectural complexity and coupling. Since our macro modeling is relatively simple (elasticity-based responses, not general equilibrium), embedding it in the DAG is cleaner. Rejected.

### 6. Lagged dependencies for feedback loops

**Decision:** Handle real-world feedback loops (e.g., fleet composition → used car prices → purchase decisions → fleet composition) via **temporal edges** — dependencies on the previous time step's output. The DAG remains acyclic within each time step, but nodes can declare dependencies on prior-year values of other nodes, enabling feedback across years.

**Rationale:** Many real interactions in the automotive fleet system involve feedback: EV adoption affects electricity demand which affects electricity prices which affects EV adoption; VMT affects fuel demand which affects fuel prices which affects VMT. A pure DAG with no feedback mechanism would miss these dynamics. However, most of these feedbacks operate on timescales where a 1-year lag is physically reasonable — markets adjust, consumers respond to last year's prices, fleet composition shifts gradually. This matches how established fleet models (VISION, LAVE-Trans) handle feedback.

**Implementation approach:**

- Compute functions can declare **temporal parameters** that reference a node's value from the previous time step (e.g., `prev_fleet_composition`) rather than the current step
- The engine resolves temporal edges by reading from the prior year's output store. For year 0 (2024), temporal dependencies use initial/default values
- The DAG is validated for acyclicity considering only within-step edges. Temporal (cross-step) edges are excluded from cycle detection since they cannot create within-step circular dependencies
- Provenance records distinguish temporal edges from within-step edges, so traceability shows when a value came from the prior year

**Key feedback loops this enables:**

- `fleet_composition[t-1]` → used car supply → purchase prices → powertrain preference → `fleet_composition[t]`
- `ev_adoption[t-1]` → electricity demand → `electricity_price[t]` → EV cost advantage → `ev_adoption[t]`
- `vmt[t-1]` → fuel demand → `oil_price_effective[t]` → `vmt[t]`

**Alternatives considered:**

- Within-step iterative equilibrium (fixed-point iteration for strongly connected components): More accurate for fast-adjusting markets but adds significant complexity — convergence detection, potential for oscillation, harder to explain to decision-makers. Rejected for the prototype, but the architecture does not preclude adding it later for specific sub-graphs where annual lag is insufficient.
- Simultaneous equation solving for cycle nodes: Works for small analytical systems but doesn't generalize well to our graph. Rejected.

### 7. Web application with FastAPI backend + React frontend

**Decision:** Replace Streamlit with a FastAPI backend serving a React (or similar) frontend.

**Rationale:** Streamlit was appropriate for the research prototype but limits layout control, interactivity, and UX polish needed for decision-maker audiences. FastAPI provides a clean API layer separating simulation from presentation. A proper frontend framework enables the interactive visualizations (causal graph exploration, uncertainty displays, scenario comparison) that decision-makers need.

**Alternatives considered:**

- Streamlit v2 with custom components: Still limited by Streamlit's execution model (rerun-on-interaction). Rejected for production but could be used for rapid prototyping during development.
- Jupyter/Panel: Good for researchers, wrong audience. Rejected.
- Desktop app (Electron/Tauri): Adds deployment complexity. Web is more accessible. Rejected.

### 8. Data layer with schema validation

**Decision:** All input data (CSV files, parameter defaults, scenario configs) pass through a validation layer with declared schemas before entering the simulation.

**Rationale:** Ekiden v1 had implicit data contracts — CSV columns had to match expected names, and mismatches caused silent errors. Explicit schemas (using Pandera for DataFrames, Pydantic for configs) catch errors early and document the data contract.

**Implementation approach:**

- Pandera schemas for all DataFrame inputs (fleet inventory, VMT tables, survival curves, emissions factors)
- Pydantic models for scenario configurations and node parameters
- Data loaders validate on ingest and produce clear error messages

## Risks / Trade-offs

**Monte Carlo UQ may be slow for interactive use** → Start with small sample sizes (N=100-500) for interactive exploration, offer full runs (N=5000+) for final analysis. Profile early and optimize hot paths. Latin Hypercube Sampling for efficiency.

**Elasticity-based macro-driver models may be too simplistic** → This is a known limitation. Document the elasticity values and their sources explicitly. Allow users to override elasticities as scenario parameters. The architecture supports swapping in more sophisticated models later without changing the graph structure.

**8 capabilities is ambitious for 1-2 people in 1 year** → Prioritize: simulation-engine and fleet-dynamics first (core), then emissions-model and counterfactual-interventions (value), then UQ and macro-drivers (differentiation), then explainability and visualization (polish). Accept that early milestones may use simpler UIs (CLI, notebooks) before the full dashboard.

**Decision-makers may not trust a model they can't interrogate** → This is why explainability is a capability, not a feature. But building trust also requires validation (GREET/VISION comparison) and presentation quality. Budget time for stakeholder demos and iteration.

**Lagged feedback may miss fast-adjusting dynamics** → Some feedback loops (e.g., fuel price ↔ VMT) may adjust faster than annual. For the prototype, annual lag is sufficient and matches established models. If validation reveals specific sub-systems where within-year dynamics matter, the architecture supports adding iterative equilibrium for those nodes without changing the overall DAG structure.

**Data quality varies across sources** → EPA/NHTS data is well-documented but aging (NHTS 2017). EIA projections are scenarios, not forecasts. Literature-derived manufacturing emissions have wide ranges. Mitigate by carrying uncertainty ranges and being transparent about data vintage in provenance records.

## Open Questions

- **Consumer preference model**: What level of sophistication is appropriate? Simple price elasticities, discrete choice models, or something in between? Needs literature review and prototyping.
- **Used car market dynamics**: Ekiden v1 had a linear programming optimizer for fleet reshuffling. Is this the right approach or should we use a simpler model?
- **Regional vs. national**: Should we model regional grid mixes (which vary significantly) or stick with national averages for the prototype? Regional adds complexity but much more accuracy for EV emissions.
- **Visualization framework**: React is the decision for the frontend, but which charting library? D3 for full control, or a higher-level library (Plotly, Recharts) for faster development?
- **Validation protocol**: What quantitative thresholds define "validates against GREET/VISION"? Need to define this before we start comparing.
