## ADDED Requirements

### Requirement: Demo API endpoint returns curated baseline-vs-intervention comparison
The system SHALL provide a `GET /demo` endpoint that runs a baseline scenario and a curated intervention scenario (EV subsidy + grid decarbonization), returning structured comparison data without requiring manual scenario setup.

#### Scenario: Demo endpoint returns complete comparison data
- **WHEN** a client calls `GET /demo`
- **THEN** the response SHALL include baseline trajectory (10 years of GHG by component), intervention trajectory, delta values (absolute and percentage), fleet composition for both scenarios, and wall clock time

#### Scenario: Demo endpoint caches results after first call
- **WHEN** `GET /demo` is called a second time
- **THEN** the response SHALL return cached results without re-running simulations

### Requirement: DemoPage presents a narrated stakeholder walkthrough
The frontend SHALL include a `/demo` route with a `DemoPage` component that walks stakeholders through CarbonSight's core capabilities in a guided, step-by-step format.

#### Scenario: DemoPage loads and shows introduction
- **WHEN** a user navigates to `/demo`
- **THEN** the page SHALL display a title, brief description of CarbonSight, and a "Start Demo" button or auto-advance to step 1

#### Scenario: Step 1 shows baseline fleet analysis
- **WHEN** the demo advances to step 1
- **THEN** the page SHALL display baseline fleet size, GHG trajectory chart, and fleet composition chart with narrative text explaining what the user is seeing

#### Scenario: Step 2 shows intervention configuration
- **WHEN** the demo advances to step 2
- **THEN** the page SHALL display the curated intervention (EV subsidy + grid decarbonization) with parameter descriptions and narrative explaining the "what if" question being asked

#### Scenario: Step 3 shows comparison results
- **WHEN** the demo advances to step 3
- **THEN** the page SHALL display side-by-side or overlay charts comparing baseline vs intervention GHG trajectories, cumulative emissions avoided, and fleet composition differences

#### Scenario: Step 4 shows provenance and trust
- **WHEN** the demo advances to step 4
- **THEN** the page SHALL display data sources, assumptions, and validation results (GREET/VISION spot checks) to demonstrate traceability and trustworthiness

### Requirement: DemoPage works in both live and fallback modes
The DemoPage SHALL function with both a live API connection and hardcoded fallback data, so the demo can be shown without a running backend.

#### Scenario: DemoPage uses live API when available
- **WHEN** the API is reachable at the configured endpoint
- **THEN** the DemoPage SHALL fetch data from `GET /demo` and display live results

#### Scenario: DemoPage falls back to demo data when API is unavailable
- **WHEN** the API is not reachable
- **THEN** the DemoPage SHALL display pre-computed demo data with a "Demo Mode" indicator
