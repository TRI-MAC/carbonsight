# Tasks: stakeholder-demo

## 1. Backend: Demo API Endpoint

- [x] 1.1 Add `GET /demo` endpoint to `carbonsight/app/api.py` that runs baseline + intervention simulations and returns combined comparison data
- [x] 1.2 Define the curated intervention: EV subsidy (15% BEV proportion shift) + grid decarbonization (grid_ghg_per_kwh trajectory declining ~50% over 10 years)
- [x] 1.3 Cache demo results after first call (same pattern as `_dashboard_cache`)
- [x] 1.4 Add test for `/demo` endpoint in `tests/app/test_api.py`

## 2. Backend: Demo Scenario Seeding

- [x] 2.1 Add `seed_demo_scenarios()` function to `carbonsight/app/api.py` that creates "baseline" and "ev-grid-intervention" scenarios in the ScenarioStore
- [x] 2.2 Add test verifying seeded scenarios appear in `GET /scenarios`

## 3. Frontend: DemoPage Component

- [x] 3.1 Create `frontend/src/pages/DemoPage.tsx` with step-based navigation (4 steps + intro)
- [x] 3.2 Step 1: Baseline fleet analysis — fleet size metric, GHG trajectory chart, fleet composition chart, narrative text
- [x] 3.3 Step 2: Intervention description — display the "what if" question, show intervention parameters, explain expected mechanisms
- [x] 3.4 Step 3: Comparison results — overlay/side-by-side GHG trajectories, cumulative emissions avoided metric, fleet composition comparison
- [x] 3.5 Step 4: Trust & provenance — data sources table, validation results summary (GREET/VISION), assumption transparency
- [x] 3.6 Add fallback demo data (hardcoded from actual simulation run) for offline mode
- [x] 3.7 Add API client method for `GET /demo` in `frontend/src/api/client.ts`

## 4. Frontend: Routing and Navigation

- [x] 4.1 Add `/demo` route to `frontend/src/App.tsx`
- [x] 4.2 Add "Demo" link to navigation sidebar in `frontend/src/components/Layout.tsx`

## 5. Demo Launch Script

- [x] 5.1 Create `run_demo.py` that starts FastAPI server, seeds demo scenarios, and prints demo URL
- [x] 5.2 Add instructions for starting the frontend dev server separately

## 6. Verification

- [x] 6.1 Run all backend tests to verify no regressions
- [x] 6.2 Run frontend tests to verify no regressions
- [x] 6.3 Manual end-to-end test: start backend with `run_demo.py`, start frontend, navigate to `/demo`, walk through all 4 steps
