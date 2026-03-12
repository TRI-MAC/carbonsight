# CarbonSight: Counterfactual Carbon Impact Simulator for Automotive Decarbonization

**Version**: 1.0
**Date**: 2026-03-12
**Researcher(s)**: Andrew Taber
**Affiliation**: Toyota Research Institute
**Time Horizon**: 1-year prototype development; 10-year simulation horizon

---

## Executive Summary

CarbonSight is a simulation platform that enables automotive industry decision-makers and policymakers to evaluate the carbon impact of counterfactual interventions across the US light-duty vehicle fleet over a 10-year horizon. Unlike existing tools that address lifecycle analysis, fleet dynamics, or macro-economic modeling in isolation, CarbonSight integrates all three in a causal, explainable framework with uncertainty quantification — allowing users to ask "what if" questions and receive traceable, confidence-bounded answers.

---

## 1. Research Questions

### 1.1 Primary Research Questions

1. **How do specific policy, technology, behavioral, and energy interventions propagate through the US automotive fleet system to affect cumulative greenhouse gas emissions over a 10-year horizon?**
2. **Which interventions — and which combinations of interventions — yield the greatest carbon reduction, and how confident can we be in those estimates?**

### 1.2 Secondary / Enabling Questions

- How should macro-economic drivers (oil prices, electricity prices, consumer preferences) be causally linked to fleet composition and usage patterns in a way that is both defensible and computationally tractable?
- What are appropriate uncertainty distributions for key model inputs (manufacturing emissions, grid carbon intensity, vehicle survival rates), and how do input uncertainties compound through the causal graph?
- Can counterfactual intervention effects be decomposed into attributable components (e.g., "X% of the reduction came from grid decarbonization, Y% from powertrain mix shift")?
- What validation approaches can establish credibility of the simulation with decision-makers who are not modelers?

### 1.3 Out-of-Scope Questions

- Heavy-duty vehicles, commercial fleets, and non-US markets (future extensions)
- Real-time operational optimization (this is a strategic planning tool, not an operational one)
- Detailed financial modeling (ROI, profitability) — the tool models carbon, not dollars, though cost may appear as a driver of behavior
- Autonomous vehicle impacts on fleet dynamics (speculative and data-poor)

---

## 2. Heilmeier Catechism

### Q1: What are you trying to do?

Build a simulation tool that lets decision-makers at Toyota and policymakers ask "what if" questions about the US automotive fleet's carbon footprint over the next 10 years. For example: "What if battery manufacturing emissions drop 30%?" or "What if EV adoption follows trajectory X instead of Y?" The tool traces carbon from manufacturing through driving and disposal, shows how confident we are in each estimate, and explains why a given scenario produces a given result.

### Q2: How is it done today, and what are the limits of current practice?

Current approaches include:

- **LCA tools** (GREET, openLCA, SimaPro): Rigorous lifecycle analysis but static — they don't model fleet dynamics, consumer behavior, or time evolution. You get a snapshot, not a trajectory.
- **Fleet models** (VISION, LAVE-Trans, EPA's MOVES): Model fleet turnover and usage emissions well but treat supply chains as black boxes and don't support arbitrary counterfactual interventions.
- **Integrated assessment models** (GCAM, REMIND): Macro-scale energy-economy models too coarse for vehicle-level or supply-chain-level decisions.
- **The prior Ekiden prototype**: Combined fleet dynamics with causal interventions but used scalar approximations for manufacturing, lacked uncertainty quantification, and didn't model macro-economic drivers.

**Key limitation:** No existing tool combines granular lifecycle emissions, fleet turnover dynamics, macro-economic drivers, counterfactual interventions, and uncertainty quantification in one coherent, explainable framework aimed at industry decision-makers.

### Q3: What is new in your approach and why do you think it will succeed?

Three things are new:

1. **Causal graph with macro-economic inputs**: Instead of treating interventions as independent sliders, we model upstream drivers (oil prices, electricity prices, policy incentives, consumer preferences) that propagate causally through the system. A carbon tax doesn't just change fuel cost — it shifts powertrain mix, VMT, and used car market dynamics.
2. **Explainable, traceable emissions**: Every output carries a full provenance chain — which data sources, assumptions, and model steps produced it. Decision-makers can interrogate *why* a scenario produces a given result, not just see the number.
3. **Uncertainty quantification throughout**: Instead of point estimates, the system propagates distributions, giving confidence intervals on outcomes and identifying which uncertain inputs matter most via sensitivity analysis.

We expect this to succeed because the Ekiden prototype already demonstrated the core DAG-based simulation approach works at a simpler scale. This is an expansion of a proven architecture with better data, richer causal structure, and formal UQ.

### Q4: Who cares?

- **Toyota product strategy**: Which powertrain investments yield the most carbon reduction? Should we prioritize BEV range, PHEV charging infrastructure, or manufacturing decarbonization?
- **Toyota sustainability reporting**: Defensible, traceable estimates for corporate carbon commitments and ESG disclosures.
- **Policy teams**: What fleet-level carbon trajectories result from different regulatory scenarios (CAFE standards, EV mandates, carbon pricing)?
- **Policymakers**: Evidence-based analysis of which policy levers actually move the needle on transportation emissions, with quantified uncertainty.

### Q5: What are the risks and payoffs?

**Risks:**
- Macro-economic driver modeling (oil prices, consumer preferences) introduces assumptions that are inherently hard to validate against future outcomes
- UQ can give a false sense of precision if input distributions are poorly characterized — garbage in, calibrated garbage out
- Scope creep — integrating macro drivers, UQ, and explainability in a 1-year prototype with 1-2 people is ambitious
- The model may be too complex for non-technical decision-makers to trust, or too simple for domain experts to respect

**Payoffs:**
- A decision-support tool that directly informs Toyota's decarbonization strategy with quantified confidence
- Ability to rapidly evaluate new policy proposals or market shifts (scenario turnaround in minutes, not months)
- Transparent, defensible carbon accounting that can withstand stakeholder scrutiny
- A reusable framework that could extend to other vehicle segments, markets, or OEMs
- Published research contribution at the intersection of causal modeling, fleet simulation, and decision support

### Q6: How much will it cost, and how long will it take?

- **Team**: 1-2 researchers
- **Timeline**: 1 year for a working prototype
- **Compute**: Modest — simulation is not ML-intensive; standard workstation or cloud compute sufficient
- **Data**: Primarily public sources (EPA, EIA, NHTS, GREET, IEA) supplemented by Toyota internal data where available
- **Software**: Open-source stack (Python, no licensing costs)

### Q7: What are the midterm and final "exams"?

**Midterm milestones (6 months):**
- Core fleet simulation reproduces Ekiden v1 results as a regression baseline
- Macro-economic driver inputs (oil price, electricity price, consumer preference models) integrated and affecting fleet outcomes through the causal graph
- UQ framework producing confidence intervals on Total GHG for at least 3 reference scenarios
- At least one explainability mechanism operational (e.g., intervention attribution or provenance tracing)

**Final success criteria (12 months):**
- Full counterfactual analysis capability with 15+ intervention types across policy, technology, behavioral, and energy categories
- Any output traceable to its data sources and assumptions (explainability)
- Uncertainty propagation across the full causal graph with sensitivity analysis identifying top drivers
- Validation against at least 2 external models or datasets (e.g., GREET for lifecycle, VISION for fleet trajectories)
- Demonstrated use in at least one real decision-support scenario with Toyota stakeholders

### Q8: What are the key assumptions?

- US light-duty vehicle fleet only (no heavy trucks, no global markets in this phase)
- 10-year horizon is sufficient for meaningful strategic analysis
- Causal relationships between macro drivers and fleet outcomes can be reasonably parameterized from publicly available data and literature
- Component-level manufacturing emissions (body, powertrain, battery) with literature-derived uncertainty ranges provide sufficient fidelity without requiring proprietary supplier data
- Vehicle scrappage and VMT patterns from historical data (Greene & Leard 2024, NHTS 2017) remain approximately valid over the simulation horizon
- Grid decarbonization follows estimable trajectories based on current trends and announced policies
- Consumer behavior responds to price signals and policy incentives in ways consistent with published elasticity estimates
- Toyota's vehicle portfolio (RAV4 family as representative) is a reasonable proxy for fleet-average characteristics

---

## 3. State of the Art

### 3.1 Current Best Approaches

| Approach | Description | Strengths | Limitations |
|----------|-------------|-----------|-------------|
| GREET (Argonne) | Lifecycle analysis tool for vehicles and fuels | Gold standard for well-to-wheels and cradle-to-grave LCA; extensive database | Static analysis, no fleet dynamics or time evolution; no counterfactuals |
| VISION (Argonne) | Fleet stock turnover model | Mature fleet dynamics; projects energy use and emissions over decades | Treats manufacturing as exogenous; limited intervention types; no UQ |
| LAVE-Trans (DOE) | Consumer choice + fleet model | Models consumer behavior and policy impacts on adoption | Complex, opaque; limited supply chain representation |
| EPA MOVES | Official US mobile source emissions model | Regulatory standard; detailed driving cycle emissions | Usage-phase only; no manufacturing or disposal; not designed for counterfactuals |
| GCAM (PNNL) | Integrated assessment model | Economy-wide; models energy-economy interactions | Too coarse for vehicle-level decisions; long learning curve |
| SimaPro / openLCA | General-purpose LCA software | Flexible, standards-compliant (ISO 14040/44) | Per-product analysis, not fleet-level; no dynamics |
| Ekiden v1 (TRI) | Causal DAG fleet + carbon simulator | Causal structure, counterfactual interventions, interactive UI | Scalar manufacturing, no UQ, no macro drivers, limited explainability |

### 3.2 Key Gaps

- No tool integrates lifecycle emissions, fleet dynamics, macro-economic drivers, and counterfactual interventions in a single framework
- Existing fleet models lack formal uncertainty quantification
- Decision-makers must mentally integrate results from multiple tools (LCA + fleet model + economic forecast) to answer strategic questions
- Explainability — being able to trace *why* a scenario produces a result — is absent from all current tools

---

## 4. Prior Art and References

### 4.1 Foundational Works

| Reference | Relevance |
|-----------|-----------|
| Greene & Leard, "Vehicle Survival and Scrappage Rates," 2024 | Statistical model for fleet turnover — used directly in Ekiden v1 and will be carried forward |
| Argonne GREET Model (2024 release) | Lifecycle emissions factors for vehicles and fuels; primary data source for manufacturing and fuel-cycle emissions |
| EPA "Multi-Pollutant Emissions Standards for MY2027+," 2024 | Defines powertrain mix targets and emissions standards that serve as policy scenarios |
| NHTS 2017 (Federal Highway Administration) | Vehicle miles traveled by age, household, and vehicle type; basis for VMT modeling |
| EIA Annual Energy Outlook 2024 | Oil price, electricity price, and energy mix projections used as macro-driver scenarios |

### 4.2 Closely Related Work

| Reference | Relevance |
|-----------|-----------|
| Argonne VISION Model | Fleet stock model we'll validate against; complementary approach without supply chain or UQ |
| Keith et al., "Vehicle fleet turnover and the future of fuel economy," Energy Policy, 2019 | Methods for modeling fleet composition evolution under policy scenarios |
| Wolfram & Hertwich, "Representing vehicle-technology-specific consumer preferences in energy-economy models," J. Transport & Land Use, 2021 | Consumer preference modeling approaches relevant to our macro-driver integration |
| Milovanoff et al., "Electrification of light-duty vehicle fleet alone will not meet mitigation targets," Nature Climate Change, 2020 | Demonstrates importance of multi-lever analysis (not just electrification) — validates our multi-intervention approach |

### 4.3 Inspirations and Analogies

| Reference | Insight |
|-----------|---------|
| Pearl, "Causality" (2009) | Formal causal inference framework; DAG-based reasoning that underpins our simulation architecture |
| Saltelli et al., "Global Sensitivity Analysis" (2008) | Methods for variance-based sensitivity analysis applicable to our UQ framework |
| En-ROADS climate simulator (Climate Interactive) | UX inspiration — accessible, interactive "what if" tool for non-technical decision-makers; demonstrates the value of explainable simulation |

---

## 5. Approach

### 5.1 Technical Approach

CarbonSight models the US light-duty vehicle fleet as a **directed acyclic graph (DAG)** where nodes represent quantities (emissions factors, fleet counts, VMT, macro-economic variables) and edges represent causal dependencies. The simulation advances year-by-year over a 10-year horizon.

**Core architecture layers:**

1. **Macro-economic layer**: Exogenous scenario inputs (oil price trajectories, electricity prices, policy parameters) that drive downstream behavior.
2. **Consumer/market layer**: Models how macro drivers affect new vehicle purchase decisions (powertrain mix), driving behavior (VMT), and used car market dynamics.
3. **Fleet dynamics layer**: Tracks the full vehicle stock — new vehicle entry, aging, scrappage (Greene & Leard survival model), and fleet composition over time.
4. **Emissions layer**: Computes production, usage, and disposal GHG for each vehicle cohort, with component-level granularity for manufacturing.
5. **UQ layer**: Wraps the deterministic simulation in uncertainty propagation — input parameters carry distributions, and outputs report confidence intervals.
6. **Explainability layer**: Records provenance (which inputs and computation paths produced each output) and supports intervention attribution (decomposing total effect into per-intervention contributions).

**Counterfactual mechanism**: Users define a baseline scenario and one or more intervention scenarios by modifying any input node. The system computes both trajectories and reports the difference with uncertainty bounds.

### 5.2 Key Design Decisions

- **DAG-based simulation (carried from Ekiden v1)**: Enforces explicit causal structure, prevents circular dependencies, and enables topological execution. Rationale: makes the model auditable and extensible.
- **Component-level manufacturing (not material-level)**: Body, powertrain, and battery emissions parameterized from LCA literature ranges. Rationale: data availability limits material-level fidelity; component-level with uncertainty ranges is more honest.
- **Distribution-based inputs (not point estimates)**: All key parameters carry uncertainty distributions. Rationale: point estimates hide the uncertainty that matters most for decision-making.
- **Macro-driver integration via causal links (not independent sliders)**: Oil prices affect VMT, powertrain choice, and used car values through modeled relationships. Rationale: interventions have indirect effects that independent sliders miss.
- **Python + open-source stack**: Rationale: reproducibility, no licensing barriers, accessible to research community.

### 5.3 Alternatives Considered

- **Agent-based modeling (individual vehicles/consumers)**: Rejected because data requirements are prohibitive and computational cost is high for marginal fidelity gain at fleet scale.
- **Full material flow analysis for supply chain**: Rejected because publicly available data cannot support material-level decomposition with meaningful accuracy. Component-level with uncertainty ranges is more defensible.
- **Machine learning for consumer behavior**: Rejected for the prototype — ML models are less explainable and require training data we may not have. Elasticity-based models from transportation economics literature are more transparent.

---

## 6. Scope

### 6.1 In Scope

- US light-duty vehicle fleet simulation over a 10-year horizon (2024-2034)
- Fleet dynamics: new vehicle entry, aging, scrappage, VMT by age
- Lifecycle GHG: production (component-level), usage (fuel + electricity), disposal
- Macro-economic drivers: oil prices, electricity prices, consumer preference parameters
- Policy interventions: carbon pricing, CAFE standards, EV subsidies, ZEV mandates
- Technology interventions: battery improvements, vehicle efficiency, manufacturing decarbonization
- Behavioral interventions: VMT reduction, PHEV charging, eco-driving
- Grid/energy interventions: grid mix scenarios, renewable build-out, smart charging
- Uncertainty quantification with confidence intervals on all outputs
- Explainability: provenance tracing and intervention attribution
- Interactive visualization for non-technical decision-makers
- Validation against GREET (lifecycle) and VISION (fleet trajectories)

### 6.2 Out of Scope

- Heavy-duty vehicles, commercial fleets, motorcycles
- Non-US markets (though architecture should not preclude future extension)
- Material-level supply chain decomposition (Tier 1/2/3 supplier modeling)
- Financial modeling (cost, revenue, profitability)
- Real-time operational decisions
- Autonomous vehicle impacts
- Vehicle-to-grid energy system modeling (beyond carbon impact of smart charging)

### 6.3 Non-Goals

- Replacing GREET or MOVES — CarbonSight is complementary, not competitive
- Producing regulatory-grade emissions inventories — this is a decision-support and exploration tool
- Forecasting — the tool evaluates "what if" scenarios, not "what will happen"

---

## 7. Success Criteria

| Criterion | How Measured | Target |
|-----------|-------------|--------|
| Regression fidelity | Reproduce Ekiden v1 Total GHG within 5% for equivalent scenarios | Baseline parity |
| Intervention coverage | Count of distinct, functional intervention types | >= 15 |
| Uncertainty quantification | All primary outputs carry confidence intervals; sensitivity analysis identifies top-5 drivers | Operational UQ |
| Explainability | Any output can be traced to data sources and assumptions in <= 3 clicks | Full provenance |
| External validation | Comparison against GREET lifecycle values and VISION fleet projections | Within published uncertainty ranges |
| Decision-maker usability | At least one Toyota stakeholder walkthrough with positive feedback on clarity and utility | Qualitative validation |
| Simulation performance | Full 10-year scenario with UQ completes in < 60 seconds on standard hardware | Interactive speed |

---

## 8. Revision History

| Version | Date | Author | Summary of Changes |
|---------|------|--------|--------------------|
| 1.0 | 2026-03-12 | Andrew Taber | Initial version — created from Ekiden v1 analysis and research discussion |

---

*End of Research Program Document*
