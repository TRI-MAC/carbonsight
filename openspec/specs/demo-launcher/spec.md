## ADDED Requirements

### Requirement: Single-command demo launch script
The system SHALL provide a `run_demo.py` script that starts the backend API server, seeds demo scenarios, and optionally opens the frontend in a browser.

#### Scenario: Script starts backend and reports readiness
- **WHEN** a user runs `python run_demo.py`
- **THEN** the script SHALL start the FastAPI server with the simulation graph initialized, seed a "baseline" and "ev-grid-intervention" scenario, and print a URL for the demo page

#### Scenario: Script handles missing frontend gracefully
- **WHEN** the frontend dev server is not running
- **THEN** the script SHALL print instructions for starting the frontend separately rather than failing

### Requirement: Demo scenarios are pre-seeded
The demo launch script SHALL create two pre-configured scenarios in the ScenarioStore: a "baseline" with default parameters and an "ev-grid-intervention" with EV subsidy (15% BEV proportion shift) and grid decarbonization interventions.

#### Scenario: Pre-seeded scenarios appear in scenario list
- **WHEN** the demo server is running and a client calls `GET /scenarios`
- **THEN** the response SHALL include both "baseline" and "ev-grid-intervention" scenarios
