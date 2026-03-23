# Scenario Builder Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the clunky ScenariosPage with a three-column scenario builder featuring live impact preview, causal path annotations, and slider-based intervention controls.

**Architecture:** Three-column layout (scenario list | intervention controls | live impact preview). An `useAutoRun` hook debounces slider changes, auto-saves, runs a deterministic simulation, and fetches traces to update preview charts. Causal paths are computed client-side from the graph node topology.

**Tech Stack:** React, TypeScript, Recharts, existing FastAPI backend

---

### Task 1: Add `target_node` to intervention catalog (backend)

**Files:**

- Modify: `carbonsight/app/api.py:95-156` (INTERVENTION_CATALOG)
- Test: `tests/test_api.py` (or manual curl)

**Step 1: Add target_node to each catalog entry**

In `carbonsight/app/api.py`, add a `"target_node"` field to each entry in `INTERVENTION_CATALOG`:

```python
INTERVENTION_CATALOG = [
    {
        "type": "carbon_pricing",
        "category": InterventionCategory.POLICY.value,
        "description": "Carbon price applied to fuel costs",
        "target_node": "gas_ghg_per_gallon",
        "params": [
            {"name": "price_per_tonne", "type": "float", "default": 50, "min": 10, "max": 500},
            {"name": "start_year", "type": "int", "default": 2024, "min": 2024, "max": 2034},
        ],
    },
    {
        "type": "ev_subsidy",
        "category": InterventionCategory.POLICY.value,
        "description": "EV purchase subsidy shifting powertrain mix",
        "target_node": "powertrain_proportions",
        "params": [
            {"name": "proportion_shift", "type": "dict", "default": {"bev": 0.15}, "min": None, "max": None},
        ],
    },
    {
        "type": "vmt_reduction",
        "category": InterventionCategory.BEHAVIORAL.value,
        "description": "Reduce vehicle miles traveled",
        "target_node": "adjusted_vmt",
        "params": [
            {"name": "factor", "type": "float", "default": 0.9, "min": 0.5, "max": 1.0},
        ],
    },
    {
        "type": "grid_decarbonization",
        "category": InterventionCategory.GRID_ENERGY.value,
        "description": "Grid carbon intensity trajectory override",
        "target_node": "grid_ghg_per_kwh",
        "params": [
            {"name": "trajectory", "type": "dict", "default": {}, "min": None, "max": None},
        ],
    },
    {
        "type": "battery_cost_reduction",
        "category": InterventionCategory.TECHNOLOGY.value,
        "description": "Battery production emissions trajectory",
        "target_node": "production_battery_per_kwh",
        "params": [
            {"name": "trajectory", "type": "dict", "default": {}, "min": None, "max": None},
        ],
    },
    {
        "type": "scrappage_program",
        "category": InterventionCategory.POLICY.value,
        "description": "Accelerated scrappage for old vehicles",
        "target_node": "post_scrappage",
        "params": [
            {"name": "age_threshold", "type": "int", "default": 15, "min": 5, "max": 25},
            {"name": "acceleration_factor", "type": "float", "default": 2.0, "min": 1.1, "max": 5.0},
            {"name": "duration_years", "type": "int", "default": 3, "min": 1, "max": 10},
            {"name": "start_year", "type": "int", "default": 0, "min": 0, "max": 2034},
        ],
    },
    {
        "type": "phev_charging_improvement",
        "category": InterventionCategory.BEHAVIORAL.value,
        "description": "Improve PHEV charging behavior",
        "target_node": "fleet_usage_ghg",
        "params": [
            {"name": "charging_factor", "type": "float", "default": 0.85, "min": 0.5, "max": 1.0},
        ],
    },
]
```

**Step 2: Verify endpoint returns target_node**

Run: `curl -s http://localhost:8000/interventions | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('target_node'))"`
Expected: `gas_ghg_per_gallon`

**Step 3: Commit**

```bash
git add carbonsight/app/api.py
git commit -m "Add target_node to intervention catalog entries"
```

---

### Task 2: Update API client types for target_node

**Files:**

- Modify: `frontend/src/api/client.ts:101-115` (listInterventions return type)

**Step 1: Add target_node to the intervention type**

In `frontend/src/api/client.ts`, update the `listInterventions` return type:

```typescript
  listInterventions: () =>
    request<
      Array<{
        type: string;
        category: string;
        description: string;
        target_node: string;
        params: Array<{
          name: string;
          type: string;
          default: unknown;
          min: number | null;
          max: number | null;
        }>;
      }>
    >("/interventions"),
```

**Step 2: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "Add target_node to intervention API type"
```

---

### Task 3: Create `useAutoRun` hook

**Files:**

- Create: `frontend/src/hooks/useAutoRun.ts`

**Step 1: Create the hook**

```typescript
import { useState, useRef, useCallback, useEffect } from "react";
import { api } from "../api/client";
import type { TraceResponse } from "../types";

export interface PreviewData {
  baselineTrajectory: Array<{ year: number; ghg: number }>;
  scenarioTrajectory: Array<{ year: number; ghg: number }>;
  composition: Array<{
    year: number;
    ICEV: number;
    HEV: number;
    PHEV: number;
    BEV: number;
  }>;
  deltas: {
    totalGhg: { value: number; pct: number };
    bevShare: { value: number; pct: number };
    fleetSize: { value: number; pct: number };
    gridIntensity: { value: number; pct: number };
  };
}

export function useAutoRun(scenarioName: string, debounceMs = 800) {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runIdRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const trigger = useCallback(() => {
    if (!scenarioName || scenarioName === "baseline") return;

    // Cancel pending debounce
    if (timerRef.current) clearTimeout(timerRef.current);

    timerRef.current = setTimeout(async () => {
      const thisRunId = ++runIdRef.current;
      setIsRunning(true);
      setError(null);

      try {
        // Run deterministic simulation
        await api.runScenario(scenarioName, {
          mode: "deterministic",
          num_years: 10,
        });

        // Check if stale
        if (runIdRef.current !== thisRunId) return;

        // Fetch traces for scenario and baseline
        const [
          scenarioEmissions,
          baselineEmissions,
          scenarioFleet,
          baselineFleet,
          scenarioGrid,
          baselineGrid,
        ] = await Promise.all([
          api.getTrace(scenarioName, "total_emissions"),
          api.getTrace("baseline", "total_emissions"),
          api.getTrace(scenarioName, "fleet_snapshot"),
          api.getTrace("baseline", "fleet_snapshot"),
          api.getTrace(scenarioName, "grid_ghg_per_kwh").catch(() => null),
          api.getTrace("baseline", "grid_ghg_per_kwh").catch(() => null),
        ]);

        if (runIdRef.current !== thisRunId) return;

        const years = scenarioEmissions.years;
        const baseTraj = years.map((y, i) => ({
          year: y,
          ghg:
            (baselineEmissions.field_values?.total_ghg?.[i] ??
              baselineEmissions.values[i]) / 1e9,
        }));
        const scenTraj = years.map((y, i) => ({
          year: y,
          ghg:
            (scenarioEmissions.field_values?.total_ghg?.[i] ??
              scenarioEmissions.values[i]) / 1e9,
        }));

        // Fleet composition from scenario fleet_snapshot
        const sfv = scenarioFleet.field_values;
        const comp = years.map((y, i) => {
          const total = sfv?.total_vehicles?.[i] ?? 1;
          return {
            year: y,
            ICEV: ((sfv?.icev?.[i] ?? 0) / total) * 100,
            HEV: ((sfv?.hev?.[i] ?? 0) / total) * 100,
            PHEV: ((sfv?.phev?.[i] ?? 0) / total) * 100,
            BEV: ((sfv?.bev?.[i] ?? 0) / total) * 100,
          };
        });

        // Compute final-year deltas
        const last = years.length - 1;
        const baseGhg = baseTraj[last].ghg;
        const scenGhg = scenTraj[last].ghg;

        const bfv = baselineFleet.field_values;
        const baseTotal = bfv?.total_vehicles?.[last] ?? 1;
        const scenTotal = sfv?.total_vehicles?.[last] ?? 1;
        const baseBev = ((bfv?.bev?.[last] ?? 0) / baseTotal) * 100;
        const scenBev = ((sfv?.bev?.[last] ?? 0) / scenTotal) * 100;

        const baseGrid = baselineGrid?.values[last] ?? 0;
        const scenGrid = scenarioGrid?.values[last] ?? 0;

        const pct = (a: number, b: number) =>
          b !== 0 ? ((a - b) / Math.abs(b)) * 100 : 0;

        setPreviewData({
          baselineTrajectory: baseTraj,
          scenarioTrajectory: scenTraj,
          composition: comp,
          deltas: {
            totalGhg: { value: scenGhg - baseGhg, pct: pct(scenGhg, baseGhg) },
            bevShare: { value: scenBev - baseBev, pct: pct(scenBev, baseBev) },
            fleetSize: {
              value: scenTotal - baseTotal,
              pct: pct(scenTotal, baseTotal),
            },
            gridIntensity: {
              value: scenGrid - baseGrid,
              pct: pct(scenGrid, baseGrid),
            },
          },
        });
      } catch (e) {
        if (runIdRef.current === thisRunId) {
          setError(String(e));
        }
      } finally {
        if (runIdRef.current === thisRunId) {
          setIsRunning(false);
        }
      }
    }, debounceMs);
  }, [scenarioName, debounceMs]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { previewData, isRunning, error, trigger };
}
```

**Step 2: Commit**

```bash
mkdir -p frontend/src/hooks
git add frontend/src/hooks/useAutoRun.ts
git commit -m "Add useAutoRun hook for debounced live preview"
```

---

### Task 4: Create `CausalPathChips` component

**Files:**

- Create: `frontend/src/components/CausalPathChips.tsx`

This component takes a `targetNode` and the full graph node list, computes the BFS path to `total_emissions`, and renders it as a chain of pill chips.

**Step 1: Create the component**

```typescript
import { useMemo } from "react";
import type { GraphNode } from "../types";

interface Props {
  targetNode: string;
  graphNodes: GraphNode[];
}

function bfsPath(
  from: string,
  to: string,
  adjacency: Map<string, string[]>,
): string[] | null {
  const queue: string[][] = [[from]];
  const visited = new Set<string>([from]);
  while (queue.length > 0) {
    const path = queue.shift()!;
    const current = path[path.length - 1];
    if (current === to) return path;
    for (const neighbor of adjacency.get(current) ?? []) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push([...path, neighbor]);
      }
    }
  }
  return null;
}

export default function CausalPathChips({ targetNode, graphNodes }: Props) {
  const path = useMemo(() => {
    // Build adjacency: for each node, which nodes depend on it (downstream)
    const downstream = new Map<string, string[]>();
    for (const node of graphNodes) {
      for (const up of node.upstream) {
        if (!downstream.has(up)) downstream.set(up, []);
        downstream.get(up)!.push(node.name);
      }
    }
    return bfsPath(targetNode, "total_emissions", downstream);
  }, [targetNode, graphNodes]);

  if (!path || path.length === 0) return null;

  // Look up display names
  const nameMap = new Map(graphNodes.map((n) => [n.name, n.display_name ?? n.name]));

  return (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 2, marginTop: 4 }}>
      {path.map((node, i) => (
        <span key={node} style={{ display: "flex", alignItems: "center", gap: 2 }}>
          <span
            style={{
              fontSize: 10,
              padding: "1px 6px",
              borderRadius: 8,
              background: "var(--bg-elevated)",
              color: "var(--text-muted)",
              fontFamily: "var(--font-mono)",
              whiteSpace: "nowrap",
            }}
          >
            {nameMap.get(node) ?? node}
          </span>
          {i < path.length - 1 && (
            <span style={{ fontSize: 9, color: "var(--text-muted)" }}>&rarr;</span>
          )}
        </span>
      ))}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/CausalPathChips.tsx
git commit -m "Add CausalPathChips component for intervention path display"
```

---

### Task 5: Create `ImpactPreview` component

**Files:**

- Create: `frontend/src/components/ImpactPreview.tsx`

This is the right-column panel showing the live preview charts and delta cards.

**Step 1: Create the component**

```typescript
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceArea,
} from "recharts";
import type { PreviewData } from "../hooks/useAutoRun";

interface Props {
  data: PreviewData | null;
  scenarioName: string;
  isRunning: boolean;
  error: string | null;
}

const tooltipStyle = {
  backgroundColor: "#1f2a3f",
  border: "1px solid #1e293b",
  borderRadius: "8px",
  color: "#e8ecf4",
};

function DeltaCard({ label, value, pct, unit }: { label: string; value: number; pct: number; unit: string }) {
  const isPositive = value > 0;
  const color = label === "BEV Share"
    ? (isPositive ? "var(--accent-green)" : "var(--accent-red)")
    : (isPositive ? "var(--accent-red)" : "var(--accent-green)");

  const fmt = (n: number) => {
    const abs = Math.abs(n);
    if (abs >= 1e9) return (n / 1e9).toFixed(1) + "B";
    if (abs >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (abs >= 1e3) return (n / 1e3).toFixed(1) + "K";
    if (abs >= 1) return n.toFixed(1);
    return n.toFixed(3);
  };

  return (
    <div style={{
      padding: "12px 16px",
      background: "var(--bg-surface)",
      border: "1px solid var(--border-subtle)",
      borderRadius: "var(--radius-md)",
    }}>
      <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "var(--font-display)", color, marginBottom: 2 }}>
        {isPositive ? "+" : ""}{fmt(value)} {unit}
      </div>
      <div style={{ fontSize: 11, color }}>
        {isPositive ? "+" : ""}{pct.toFixed(1)}% by 2033
      </div>
    </div>
  );
}

export default function ImpactPreview({ data, scenarioName, isRunning, error }: Props) {
  if (scenarioName === "baseline") {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-muted)", fontSize: 13, padding: 24 }}>
        This is the baseline scenario. Select or create an intervention scenario to see impact preview.
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24, color: "var(--accent-red)", fontSize: 13 }}>
        Preview error: {error}
      </div>
    );
  }

  if (!data && !isRunning) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-muted)", fontSize: 13, padding: 24 }}>
        Adjust interventions to see a live impact preview.
      </div>
    );
  }

  // Build merged trajectory data for chart
  const trajData = data ? data.baselineTrajectory.map((b, i) => ({
    year: b.year,
    baseline: b.ghg,
    scenario: data.scenarioTrajectory[i]?.ghg ?? 0,
  })) : [];

  return (
    <div style={{ padding: "0 24px 24px 0", display: "flex", flexDirection: "column", gap: 16, opacity: isRunning ? 0.5 : 1, transition: "opacity 0.2s" }}>
      {isRunning && (
        <div style={{ fontSize: 12, color: "var(--accent-blue)", fontFamily: "var(--font-mono)" }}>
          Running simulation...
        </div>
      )}

      {data && (
        <>
          {/* Delta cards */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <DeltaCard label="Total GHG" value={data.deltas.totalGhg.value} pct={data.deltas.totalGhg.pct} unit="Mt" />
            <DeltaCard label="BEV Share" value={data.deltas.bevShare.value} pct={data.deltas.bevShare.pct} unit="pp" />
            <DeltaCard label="Fleet Size" value={data.deltas.fleetSize.value} pct={data.deltas.fleetSize.pct} unit="" />
            <DeltaCard label="Grid Intensity" value={data.deltas.gridIntensity.value} pct={data.deltas.gridIntensity.pct} unit="kg/kWh" />
          </div>

          {/* GHG Trajectory */}
          <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8 }}>GHG Trajectory (Mt CO2e)</div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trajData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#556178" style={{ fontSize: 10, fontFamily: "JetBrains Mono" }} />
                <YAxis stroke="#556178" style={{ fontSize: 10, fontFamily: "JetBrains Mono" }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11, color: "#8b95a8" }} />
                {/* Delta shading */}
                {trajData.length > 1 && trajData.slice(0, -1).map((pt, i) => (
                  <ReferenceArea
                    key={pt.year}
                    x1={pt.year}
                    x2={trajData[i + 1].year}
                    fill={trajData[i].scenario < trajData[i].baseline ? "#34d39920" : "#f871711f"}
                    strokeOpacity={0}
                  />
                ))}
                <Line type="monotone" dataKey="baseline" stroke="#556178" strokeDasharray="6 3" strokeWidth={1.5} dot={false} name="Baseline" />
                <Line type="monotone" dataKey="scenario" stroke="#22d3ee" strokeWidth={2} dot={false} name={scenarioName} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Fleet Composition */}
          <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8 }}>Fleet Composition (%)</div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={data.composition}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#556178" style={{ fontSize: 10, fontFamily: "JetBrains Mono" }} />
                <YAxis stroke="#556178" style={{ fontSize: 10, fontFamily: "JetBrains Mono" }} domain={[0, 100]} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => `${v.toFixed(1)}%`} />
                <Legend wrapperStyle={{ fontSize: 11, color: "#8b95a8" }} />
                <Area type="monotone" dataKey="BEV" stackId="1" stroke="#34d399" fill="#34d399" fillOpacity={0.7} />
                <Area type="monotone" dataKey="PHEV" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.7} />
                <Area type="monotone" dataKey="HEV" stackId="1" stroke="#fbbf24" fill="#fbbf24" fillOpacity={0.7} />
                <Area type="monotone" dataKey="ICEV" stackId="1" stroke="#f87171" fill="#f87171" fillOpacity={0.7} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/ImpactPreview.tsx
git commit -m "Add ImpactPreview component with trajectory, composition, and delta cards"
```

---

### Task 6: Rewrite `ScenariosPage` — left column (scenario list)

**Files:**

- Modify: `frontend/src/pages/ScenariosPage.tsx`

This task restructures the page to a three-column layout and rewrites the left column. The center and right columns will be placeholder divs initially.

**Step 1: Replace the page layout**

Replace the outer `<div>` structure with three columns. Keep the existing scenario list logic (state, handlers for load/select/new/delete) but slim down the left column to ~200px. Add placeholder divs for center and right columns.

Key changes:

- Left column: 200px, same content as before but tighter padding
- Center column: 380px, placeholder text "Intervention controls"
- Right column: flex 1, placeholder text "Impact preview"
- Remove the entire right panel (scenario editor) — it will be rebuilt in tasks 7-8

**Step 2: Verify page renders with the three columns**

Run: `npx vite --port 5173` and navigate to `/scenarios`
Expected: Three-column layout with scenario list on left, two placeholder panels

**Step 3: Commit**

```bash
git add frontend/src/pages/ScenariosPage.tsx
git commit -m "Restructure ScenariosPage to three-column layout"
```

---

### Task 7: Rewrite `ScenariosPage` — center column (intervention controls)

**Files:**

- Modify: `frontend/src/pages/ScenariosPage.tsx`

Replace the center column placeholder with the full intervention controls panel.

**Step 1: Build intervention controls**

The center column contains:

1. Scenario name input (top)
2. Accordion sections for each intervention category
3. For each intervention: checkbox to enable, range slider + numeric input for each param, causal path chips below when active
4. Save and Run buttons at bottom

Key implementation details:

- Fetch intervention catalog on mount via `api.listInterventions()`
- Fetch graph nodes on mount via `api.listNodes()` (for CausalPathChips)
- Group interventions by category
- Each category section: clickable header that toggles visibility
- Each intervention param: `<input type="range">` paired with `<input type="number">`, sharing state
- Human-readable param labels via a mapping:
  ```typescript
  const PARAM_LABELS: Record<string, string> = {
    price_per_tonne: "Carbon Price",
    start_year: "Start Year",
    proportion_shift: "BEV Purchase Shift",
    factor: "VMT Factor",
    trajectory: "Trajectory",
    age_threshold: "Age Threshold",
    acceleration_factor: "Acceleration Factor",
    duration_years: "Duration (Years)",
    charging_factor: "Charging Factor",
  };
  ```
- Call `autoRun.trigger()` whenever an intervention value changes
- Remove the old "Custom Node Overrides" section entirely

**Step 2: Verify interventions render with sliders and causal paths**

Navigate to `/scenarios`, create/select a scenario, toggle an intervention, check:

- Slider moves and numeric input updates
- Causal path chips appear below the active intervention
- Multi-param interventions (scrappage) show all 4 params

**Step 3: Commit**

```bash
git add frontend/src/pages/ScenariosPage.tsx
git commit -m "Add intervention controls with sliders and causal path chips"
```

---

### Task 8: Wire right column to `ImpactPreview` + `useAutoRun`

**Files:**

- Modify: `frontend/src/pages/ScenariosPage.tsx`

**Step 1: Connect the auto-run hook and preview component**

Replace the right column placeholder with `<ImpactPreview>`. Wire up:

- `useAutoRun(scenarioName)` at the component level
- Call `autoRun.trigger()` on every intervention slider change (already done in Task 7)
- Also call `autoRun.trigger()` when selecting an existing scenario that has interventions
- Pass `autoRun.previewData`, `autoRun.isRunning`, `autoRun.error` to `<ImpactPreview>`
- The auto-save before auto-run: call `handleSaveScenario()` (without alert) before triggering

**Step 2: Integration test**

1. Navigate to `/scenarios`
2. Create a new scenario "test-preview"
3. Toggle "EV subsidy" → set BEV Purchase Shift to 0.15
4. After ~2.4s, the right panel should show:
   - GHG trajectory with baseline (dashed) and scenario (solid) lines
   - Delta shading between lines
   - 4 delta cards showing final-year differences
   - Fleet composition stacked area chart
5. Adjust slider → preview updates after debounce

**Step 3: Commit**

```bash
git add frontend/src/pages/ScenariosPage.tsx
git commit -m "Wire live impact preview to auto-run hook"
```

---

### Task 9: Update tests

**Files:**

- Modify: `frontend/src/__tests__/ScenariosPage.test.tsx` (if it exists)
- Create: `frontend/src/__tests__/ScenariosPage.test.tsx` (if not)

**Step 1: Check if test file exists**

Run: `ls frontend/src/__tests__/ScenariosPage.test.tsx`

**Step 2: Write/update tests**

Key test cases:

- Renders three-column layout with scenario list
- Shows intervention categories as accordion sections
- Toggling an intervention shows slider controls
- CausalPathChips renders a path for an active intervention
- ImpactPreview shows baseline message when baseline is selected
- ImpactPreview shows delta cards when preview data is present

Mock `fetch` for: `/scenarios`, `/interventions` (with `target_node`), `/graph/nodes`

**Step 3: Run tests**

Run: `cd frontend && npx vitest run --reporter=verbose`
Expected: All tests pass

**Step 4: Commit**

```bash
git add frontend/src/__tests__/ScenariosPage.test.tsx
git commit -m "Add tests for redesigned ScenariosPage"
```

---

### Task 10: Final cleanup and verification

**Step 1: Remove dead code**

Check `ScenariosPage.tsx` for any unused imports, state variables, or handlers from the old design (e.g. `selectedCategory` dropdown state, `customOverrides` state and handlers).

**Step 2: Run all frontend tests**

Run: `cd frontend && npx vitest run`
Expected: All tests pass

**Step 3: Run backend tests**

Run: `.venv/bin/python -m pytest tests/ -x -q`
Expected: All pass (278+)

**Step 4: Manual smoke test**

1. Start servers: `./init.sh`
2. Navigate to `/scenarios` — three-column layout renders
3. Select `ev-grid-intervention` — preview auto-populates
4. Create new scenario, add EV subsidy — preview updates after ~2.4s
5. Navigate to `/` (dashboard) — still works
6. Navigate to `/graph` — still works

**Step 5: Commit**

```bash
git add -A
git commit -m "Scenario builder redesign: cleanup and finalize"
```
