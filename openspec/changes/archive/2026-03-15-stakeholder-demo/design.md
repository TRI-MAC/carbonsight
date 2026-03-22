## Context

CarbonSight has a working backend (242 tests passing), validated against GREET and VISION, with a React frontend that includes Dashboard, Scenarios, Compare, Graph, and Sensitivity pages. The frontend has demo fallback data when the API is unavailable. The RPD success criterion requires "at least one Toyota stakeholder walkthrough with positive feedback on clarity and utility."

Current state:

- Backend: FastAPI with `/dashboard`, `/scenarios`, `/compare`, `/graph`, `/scenarios/{name}/run`, `/scenarios/{name}/trace/{node}`, `/scenarios/{name}/provenance/{node}` endpoints
- Frontend: 5 pages with dark "observatory" theme, recharts, ReactFlow DAG visualization
- Gap: No curated end-to-end demo flow; stakeholder must navigate independently and set up scenarios manually

## Goals / Non-Goals

**Goals:**

- A stakeholder can see CarbonSight's full value proposition in under 5 minutes
- The demo works reliably (live API preferred, demo fallback when offline)
- Narrative text guides non-technical viewers through each step
- The demo showcases: fleet simulation, intervention analysis, comparison, and provenance/trust

**Non-Goals:**

- Interactive scenario editing (stakeholders watch, not operate)
- UQ/sensitivity in the demo (adds complexity without core value for first demo)
- New chart types or visualization libraries
- Polishing non-demo pages for stakeholder use

## Decisions

### 1. Single `/demo` endpoint vs reusing existing endpoints

**Decision**: New `GET /demo` endpoint that internally runs baseline + intervention and returns a combined comparison payload.

**Rationale**: Stakeholder demo should be one-click, not "create scenario, run it, create another, run it, compare." The existing endpoints work for power users but the demo needs a curated, self-contained experience.

**Alternative considered**: Frontend orchestrating multiple API calls — rejected because it's fragile and slow for a demo.

### 2. Step-based DemoPage vs scrolling narrative

**Decision**: Step-based progression with 4 steps (baseline → intervention → comparison → trust), using a stepper UI with next/back navigation.

**Rationale**: Guided steps prevent information overload and create a natural presentation flow. A scrolling page works for reading but not for presenting to a group.

**Alternative considered**: Single scrolling page — rejected because it doesn't pace the narrative for a live walkthrough.

### 3. Curated intervention: EV subsidy + grid decarbonization

**Decision**: Use a combined EV subsidy (15% BEV share shift) + grid decarbonization (50% reduction by 2033) as the demo intervention.

**Rationale**: This combination shows a multi-lever intervention with visible carbon impact. EV adoption alone has limited impact without grid decarbonization — this is a key CarbonSight insight worth demonstrating.

### 4. Fallback data strategy

**Decision**: Hardcode realistic fallback data directly in DemoPage, computed from actual simulation runs.

**Rationale**: The existing pattern (DashboardPage already does this) works well. We'll capture one run's output as the fallback dataset.

## Risks / Trade-offs

- **[Simulation time]** Running two full 10-year simulations on demo load adds ~5-10s. → Mitigation: Cache after first call; show loading state with progress.
- **[Fallback data staleness]** Hardcoded fallback may drift from actual model output as the model evolves. → Mitigation: Generate fallback from actual run; document how to refresh.
- **[Demo scope creep]** Temptation to add UQ, sensitivity, etc. → Mitigation: Strict 4-step scope; additional capabilities can be added in future demos.
