## 1. Project Scaffolding

- [ ] 1.1 Initialize Python project with pyproject.toml (dependencies: numpy, pandas, networkx, pydantic, pandera, scipy, scikit-learn, salib, fastapi, uvicorn)
- [ ] 1.2 Create directory structure: carbonsight/{core, domain, analysis, app, data}
- [ ] 1.3 Set up testing framework (pytest) with test directory mirroring src layout
- [ ] 1.4 Set up linting and formatting (ruff)
- [ ] 1.5 Create data/ directory with subdirectories for raw CSV sources and validated/processed data

## 2. Core Simulation Engine — Node System

- [ ] 2.1 Implement base Node class with typed value system (scalar, timeseries, distribution, dataframe)
- [ ] 2.2 Implement Distribution value type supporting normal, lognormal, uniform, triangular, and empirical distributions
- [ ] 2.3 Implement node registration with type validation (reject invalid types)
- [ ] 2.4 Implement compute function auto-wiring (parameter names → upstream node resolution)
- [ ] 2.5 Write tests for node typing, distribution storage, and point-value degenerate case
- [ ] 2.6 Write tests for auto-wiring compute functions to upstream nodes

## 3. Core Simulation Engine — DAG Construction and Execution

- [ ] 3.1 Implement DAG construction from registered nodes with two edge types: within-step edges and temporal edges
- [ ] 3.2 Implement cycle detection on within-step edges only (temporal edges excluded from cycle check)
- [ ] 3.3 Implement type-compatibility validation on edges at construction time
- [ ] 3.4 Implement topological sort and execution in dependency order (within-step edges only)
- [ ] 3.5 Write tests for DAG construction, within-step cycle rejection, and temporal-edge-cycle acceptance
- [ ] 3.6 Write tests for topological execution order correctness

## 4. Core Simulation Engine — Time Stepping

- [ ] 4.1 Implement year-by-year time stepping loop (10 years, 2024-2033) with year-indexed output store
- [ ] 4.2 Implement output chaining (year N outputs → year N+1 inputs)
- [ ] 4.3 Implement temporal edge resolution: declare temporal parameters (prev_<node_name>), resolve from prior year's output store
- [ ] 4.4 Implement initial/default value provision for temporal edges at year 0, reject temporal edges with missing initial values
- [ ] 4.5 Implement provenance distinction for temporal edges (record source year for lagged inputs)
- [ ] 4.6 Implement configurable time horizon (start year, number of years, renewal rate)
- [ ] 4.7 Write tests for 10-year execution producing correctly labeled year outputs
- [ ] 4.8 Write tests for temporal edge resolution: prior-year values, year-0 defaults, missing initial value rejection
- [ ] 4.9 Write tests for feedback loop via temporal edges (e.g., fleet_composition ↔ powertrain_preference across years)

## 5. Core Simulation Engine — Scenarios

- [ ] 5.1 Implement Scenario class (name, input-node override mapping, metadata) with Pydantic model
- [ ] 5.2 Implement scenario CRUD (create, retrieve, update, delete) with unique name enforcement
- [ ] 5.3 Implement scenario serialization/deserialization (YAML/JSON)
- [ ] 5.4 Implement ScenarioResult class holding full outputs, provenance, and execution metadata
- [ ] 5.5 Implement scenario comparison: compute per-year deltas (absolute, percentage) for all output nodes
- [ ] 5.6 Implement distribution-aware comparison (deltas on mean, median, 5th/95th percentiles)
- [ ] 5.7 Write tests for scenario CRUD, serialization, comparison, and distribution comparison

## 6. Core Simulation Engine — Execution Modes and Performance

- [ ] 6.1 Implement deterministic execution mode (collapse distributions to point estimates)
- [ ] 6.2 Implement UQ execution mode (propagate distributions via Monte Carlo sampling)
- [ ] 6.3 Implement execution mode selection at launch time (immutable during run)
- [ ] 6.4 Implement wall-clock timing and performance warning when exceeding 60s target
- [ ] 6.5 Write tests for deterministic vs UQ mode behavior and mode immutability

## 7. Data Layer

- [ ] 7.1 Implement Pandera schemas for fleet inventory DataFrame (age, powertrain, mpg, mpge, battery_kwh, ev_range, vmt, n, high_vmt_prop)
- [ ] 7.2 Implement Pandera schemas for survival curves, VMT-by-age, and powertrain proportions DataFrames
- [ ] 7.3 Implement data loaders for CSV sources with schema validation on ingest (EPA, NHTS, Greene & Leard)
- [ ] 7.4 Implement Pydantic models for emissions factors (production, usage, disposal) with uncertainty ranges
- [ ] 7.5 Implement Pydantic models for macro-driver trajectories (oil price, electricity price)
- [ ] 7.6 Port data files from Ekiden v1: current_veh_t0_VMT.csv, epa_table3.csv, averaged_survival_v2.csv, vmt_by_age.csv
- [ ] 7.7 Write tests for schema validation: valid data passes, invalid data rejected with clear errors

## 8. Fleet Dynamics Domain Model

- [ ] 8.1 Implement fleet inventory representation (cohorts by age × powertrain × VMT bucket)
- [ ] 8.2 Implement vehicle aging (increment age by 1 each year, preserve attributes)
- [ ] 8.3 Implement scrappage model using Greene & Leard survival curves (age-based scrappage rates, max age 50 cutoff)
- [ ] 8.4 Implement new vehicle entry (5% renewal rate × fleet size, distributed by powertrain proportions)
- [ ] 8.5 Implement VMT assignment by age using NHTS data (high/low VMT buckets)
- [ ] 8.6 Implement fleet composition tracking (annual snapshots, powertrain share evolution)
- [ ] 8.7 Implement used car market dynamics (15% circulable, VMT bucket reassignment, fleet size conservation)
- [ ] 8.8 Implement data validation for survival curves (bounds 0-1, monotonicity), VMT (positive, complete), powertrain proportions (sum to 1)
- [ ] 8.9 Register all fleet dynamics compute functions as DAG nodes
- [ ] 8.10 Write tests for aging, scrappage, new vehicle entry, VMT assignment, and used car market
- [ ] 8.11 Regression test: reproduce Ekiden v1 fleet composition outputs for equivalent inputs

## 9. Emissions Model Domain

- [ ] 9.1 Implement production emissions computation (body + powertrain + battery_kwh × cost_per_kwh) with distribution-based factors
- [ ] 9.2 Implement usage emissions — gasoline (VMT / MPG × ghg_per_gallon) with time-varying fuel carbon intensity
- [ ] 9.3 Implement usage emissions — electricity (VMT × utility_factor / MPGe × grid_ghg_kwh) with time-varying grid intensity
- [ ] 9.4 Implement PHEV utility factor calculation (polynomial fit on battery size × MPGe)
- [ ] 9.5 Implement disposal emissions (per-vehicle cost applied at scrappage)
- [ ] 9.6 Implement total GHG aggregation (production + usage + disposal, annual and cumulative, disaggregated by component)
- [ ] 9.7 Implement time-varying emission factors (grid decarbonization trajectory, battery manufacturing improvement)
- [ ] 9.8 Register all emissions compute functions as DAG nodes
- [ ] 9.9 Write tests for each emissions component, PHEV utility factor, and total aggregation
- [ ] 9.10 Regression test: reproduce Ekiden v1 total GHG within 5% for equivalent scenarios

## 10. Counterfactual Interventions

- [ ] 10.1 Implement intervention base class with category taxonomy (policy, technology, behavioral, grid/energy) and validation
- [ ] 10.2 Implement policy interventions: carbon pricing, CAFE standards, EV subsidies, ZEV mandates, fuel tax, scrappage programs, charging infrastructure
- [ ] 10.3 Implement technology interventions: battery energy density, battery cost, alternative chemistries, manufacturing decarbonization, vehicle lightweighting
- [ ] 10.4 Implement behavioral interventions: VMT reduction, PHEV charging, eco-driving, remote work, ride-sharing
- [ ] 10.5 Implement grid/energy interventions: grid mix scenarios, renewable build-out, smart charging
- [ ] 10.6 Implement intervention application (override input nodes without changing graph topology)
- [ ] 10.7 Implement scenario differencing (absolute delta, percentage delta, per-year breakdown)
- [ ] 10.8 Implement multi-intervention combinations with defined application order and conflict warnings
- [ ] 10.9 Write tests for each intervention category, application, differencing, and conflict detection

## 11. Macro-Economic Drivers

- [ ] 11.1 Implement oil price trajectory node (EIA reference/high/low scenarios, custom trajectories)
- [ ] 11.2 Implement electricity price trajectory node (EIA scenarios, custom trajectories)
- [ ] 11.3 Implement consumer preference parameter nodes (willingness to pay, range anxiety thresholds)
- [ ] 11.4 Implement policy parameter nodes (carbon price, CAFE target, subsidy amount, ZEV mandate %)
- [ ] 11.5 Implement elasticity-based causal propagation (oil price → VMT, oil price → powertrain preference, electricity price → EV advantage)
- [ ] 11.6 Implement configurable elasticity values with literature defaults and source citations
- [ ] 11.7 Implement causal link documentation (queryable: which drivers affect which nodes)
- [ ] 11.8 Register all macro-driver nodes in the DAG with causal edges to downstream nodes
- [ ] 11.9 Write tests for EIA scenario loading, elasticity propagation, and causal link queries

## 12. Uncertainty Quantification

- [ ] 12.1 Implement distribution specification API for input parameters (normal, lognormal, uniform, triangular, empirical)
- [ ] 12.2 Implement Monte Carlo propagation through DAG (sample all inputs, execute DAG per sample, collect output samples)
- [ ] 12.3 Implement Latin Hypercube Sampling as default strategy (stratified coverage)
- [ ] 12.4 Implement confidence interval computation on outputs (5th, 25th, 50th, 75th, 95th percentiles, mean, std)
- [ ] 12.5 Implement variance-based sensitivity analysis using SALib (first-order and total-order Sobol indices)
- [ ] 12.6 Implement top-N uncertainty driver identification with human-readable descriptions
- [ ] 12.7 Implement sample size configuration (interactive: 100-500, full: 5000+, custom) with insufficiency warnings
- [ ] 12.8 Write tests for distribution specification, MC propagation, LHS stratification, confidence intervals, and Sobol indices

## 13. Explainability

- [ ] 13.1 Implement provenance recording during graph execution (node ID, inputs, data sources, assumptions, compute function hash, timestamp, scenario ID)
- [ ] 13.2 Implement provenance storage as structured metadata on ScenarioResult
- [ ] 13.3 Implement input-to-output traceability queries (forward and backward chain traversal)
- [ ] 13.4 Implement intervention attribution (decompose total effect into per-intervention contributions plus interaction terms)
- [ ] 13.5 Implement data source lineage metadata on input nodes (source name, date, version, URL/DOI, transformations)
- [ ] 13.6 Implement assumption documentation per node (description, rationale, confidence level) as structured metadata
- [ ] 13.7 Implement human-readable provenance report generation (plain language, units, top drivers, data sources, assumptions)
- [ ] 13.8 Implement provenance report export (PDF, HTML)
- [ ] 13.9 Write tests for provenance recording, chain queries, attribution decomposition, and report generation

## 14. API Layer

- [ ] 14.1 Set up FastAPI application with CORS, health check endpoint
- [ ] 14.2 Implement scenario CRUD endpoints (POST/GET/PUT/DELETE /scenarios)
- [ ] 14.3 Implement simulation execution endpoint (POST /scenarios/{id}/run with mode selection)
- [ ] 14.4 Implement scenario comparison endpoint (POST /compare with baseline + intervention IDs)
- [ ] 14.5 Implement graph introspection endpoints (GET /graph/nodes, GET /graph/nodes/{id})
- [ ] 14.6 Implement provenance query endpoints (GET /scenarios/{id}/provenance/{node})
- [ ] 14.7 Implement sensitivity analysis endpoint (GET /scenarios/{id}/sensitivity)
- [ ] 14.8 Implement export endpoints (GET /scenarios/{id}/export?format=csv|yaml)
- [ ] 14.9 Write API integration tests for all endpoints

## 15. Visualization — Frontend

- [ ] 15.1 Initialize React application with build tooling (Vite or similar)
- [ ] 15.2 Implement causal graph visualization (interactive DAG with node click → detail panel, causal path highlighting)
- [ ] 15.3 Implement scenario configuration UI (create/edit scenarios, select interventions, override inputs, validate parameters)
- [ ] 15.4 Implement scenario comparison view (side-by-side/overlay charts, deltas, metric selection)
- [ ] 15.5 Implement cumulative GHG trajectory chart (10-year line chart with confidence bands, multi-scenario overlay)
- [ ] 15.6 Implement uncertainty visualizations (fan charts, click-to-drill distribution histograms)
- [ ] 15.7 Implement sensitivity analysis display (tornado chart, first-order/total-order toggle, plain-language labels)
- [ ] 15.8 Implement intervention attribution view (waterfall chart, per-intervention contributions, interaction terms)
- [ ] 15.9 Implement export functionality (charts as PNG/SVG, data as CSV, scenarios as YAML)
- [ ] 15.10 Write frontend component tests for key interactions

## 16. Validation and Integration

- [ ] 16.1 Validate lifecycle emissions against GREET values (production, usage, disposal within published ranges)
- [ ] 16.2 Validate fleet trajectory against VISION model projections (fleet composition, total VMT within published ranges)
- [ ] 16.3 Define quantitative validation thresholds and document comparison methodology
- [ ] 16.4 End-to-end integration test: full 10-year scenario with UQ, comparison, attribution, and provenance
- [ ] 16.5 Performance benchmark: verify UQ run completes < 60s on reference hardware
- [ ] 16.6 Stakeholder demo scenario: prepare at least one real decision-support walkthrough with Toyota stakeholders
