## Why

CarbonSight's research program identifies "demonstrated use in at least one real decision-support scenario with Toyota stakeholders" as a final success criterion. The backend simulation engine, validation suite, and frontend pages are all functional, but no end-to-end demo flow exists that walks a stakeholder through the core value proposition: ask a "what if" question, see the carbon impact, understand why, and trust the answer. Without this, the tool remains a developer artifact rather than a decision-support platform.

## What Changes

- Create a guided demo script (runnable walkthrough) that exercises the full stack: baseline dashboard, intervention scenario creation, comparison, and provenance drill-down
- Add a `/demo` API endpoint that runs a curated baseline + intervention pair and returns pre-structured comparison data (no manual scenario setup required)
- Add a `DemoPage` frontend component that presents a self-contained, narrated walkthrough of CarbonSight's capabilities
- Polish existing pages for demo readiness: ensure ComparePage and ScenariosPage work end-to-end with the live API (not just demo fallbacks)
- Create a demo launch script that starts backend + frontend together and seeds demo scenarios

## Capabilities

### New Capabilities

- `demo-walkthrough`: Self-contained stakeholder demo page with narrated steps showing baseline analysis, intervention comparison, uncertainty quantification, and provenance tracing
- `demo-launcher`: Single-command script to start the full stack with seeded demo scenarios

### Modified Capabilities

<!-- No existing spec-level requirement changes needed -->

## Impact

- **Frontend**: New `DemoPage.tsx` component, route addition in App.tsx
- **Backend**: New `/demo` endpoint in api.py, demo scenario seeding logic
- **Scripts**: New `run_demo.py` or shell script for one-command launch
- **No breaking changes** to existing API or frontend pages
