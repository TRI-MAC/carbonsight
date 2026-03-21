import { useState, useEffect, Fragment } from "react";
import { useNavigate } from "react-router-dom";
import {
  AreaChart,
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
  Label,
} from "recharts";
import { api } from "../api/client";
import type { TraceResponse } from "../types";
import Card from "../components/Card";
import Button from "../components/Button";
import DeltaSummaryCard from "../components/DeltaSummaryCard";

type RunStatus = "checking" | "ready" | "not-run";
type Tab = "overview" | "compare";

interface Metrics {
  fleet_size: number;
  annual_ghg: number;
  bev_share: number;
  bev_share_final: number;
  total_vmt: number;
}

interface TrajectoryPoint {
  year: number;
  ghg: number;
  production: number;
  usage: number;
  disposal: number;
}

interface CompositionPoint {
  year: number;
  ICEV: number;
  HEV: number;
  PHEV: number;
  BEV: number;
}

interface ComparisonData {
  trajectory: Array<Record<string, number>>;
}

const COLORS = ["#22d3ee", "#a78bfa", "#fbbf24", "#34d399"];

const tooltipStyle = {
  backgroundColor: "#1f2a3f",
  border: "1px solid #1e293b",
  borderRadius: "8px",
  color: "#e8ecf4",
};

const fmt = (num: number): string => {
  if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
  return num.toFixed(0);
};

export default function ScenarioDashboardPage() {
  const navigate = useNavigate();

  // Shared state
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [selectedScenario, setSelectedScenario] = useState("baseline");
  const [runStatus, setRunStatus] = useState<Record<string, RunStatus>>({});
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [apiHealthy, setApiHealthy] = useState(false);

  // Overview state
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [trajectory, setTrajectory] = useState<TrajectoryPoint[]>([]);
  const [composition, setComposition] = useState<CompositionPoint[]>([]);
  const [overviewLoading, setOverviewLoading] = useState(true);

  // Compare state
  const [compareScenario, setCompareScenario] = useState<string>("");
  const [compareData, setCompareData] = useState<ComparisonData | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  const [metricTraces, setMetricTraces] = useState<{
    years: number[];
    baseline: Record<string, number[]>;
    intervention: Record<string, number[]>;
  } | null>(null);

  // Fetch scenario list and run status on mount
  useEffect(() => {
    api
      .listScenarios()
      .then(async (list) => {
        const names = list.map((s) => s.name);
        setScenarios(names);
        setApiHealthy(true);
        const statusMap: Record<string, RunStatus> = {};
        for (const n of names) statusMap[n] = "checking";
        setRunStatus({ ...statusMap });
        await Promise.all(
          names.map(async (n) => {
            try {
              await api.getTrace(n, "total_emissions");
              statusMap[n] = "ready";
            } catch {
              statusMap[n] = "not-run";
            }
          }),
        );
        setRunStatus({ ...statusMap });
      })
      .catch(() => setApiHealthy(false));
  }, []);

  // Fetch overview data when selected scenario changes
  useEffect(() => {
    setOverviewLoading(true);
    if (selectedScenario === "baseline") {
      api
        .getDashboard()
        .then((data) => {
          setMetrics(data.metrics);
          setTrajectory(data.trajectory);
          setComposition(data.composition);
        })
        .catch(() => setMetrics(null))
        .finally(() => setOverviewLoading(false));
    } else {
      // Reconstruct dashboard from traces
      Promise.all([
        api.getTrace(selectedScenario, "total_emissions"),
        api.getTrace(selectedScenario, "fleet_snapshot"),
      ])
        .then(([emissionsTrace, fleetTrace]) => {
          const years = emissionsTrace.years;
          const traj: TrajectoryPoint[] = [];
          const comp: CompositionPoint[] = [];

          for (let i = 0; i < years.length; i++) {
            const fv = emissionsTrace.field_values;
            traj.push({
              year: years[i],
              ghg: (fv?.total_ghg?.[i] ?? emissionsTrace.values[i]) / 1e9,
              production: (fv?.production_ghg?.[i] ?? 0) / 1e9,
              usage: (fv?.usage_ghg_total?.[i] ?? 0) / 1e9,
              disposal: (fv?.disposal_ghg?.[i] ?? 0) / 1e9,
            });

            const ffv = fleetTrace.field_values;
            if (ffv) {
              const total = ffv.total_vehicles?.[i] ?? 1;
              comp.push({
                year: years[i],
                ICEV: ((ffv.icev?.[i] ?? 0) / total) * 100,
                HEV: ((ffv.hev?.[i] ?? 0) / total) * 100,
                PHEV: ((ffv.phev?.[i] ?? 0) / total) * 100,
                BEV: ((ffv.bev?.[i] ?? 0) / total) * 100,
              });
            }
          }

          setTrajectory(traj);
          setComposition(comp);

          // Compute headline metrics from first/last year
          if (traj.length > 0) {
            const fleetFv = fleetTrace.field_values;
            const totalVehicles0 = fleetFv?.total_vehicles?.[0] ?? 0;
            const totalVmt0 = fleetFv?.total_vmt?.[0] ?? 0;
            setMetrics({
              fleet_size: totalVehicles0,
              annual_ghg: traj[0].ghg,
              bev_share: comp[0]?.BEV ?? 0,
              bev_share_final: comp[comp.length - 1]?.BEV ?? 0,
              total_vmt: totalVmt0,
            });
          }
        })
        .catch(() => setMetrics(null))
        .finally(() => setOverviewLoading(false));
    }
  }, [selectedScenario]);

  // Run comparison
  const runComparison = async (baseline: string, intervention: string) => {
    setCompareLoading(true);
    setCompareError(null);
    try {
      await api.compare(baseline, [intervention]);

      const traceResults = await Promise.allSettled(
        [baseline, intervention].map((name) =>
          api.getTrace(name, "total_emissions"),
        ),
      );

      const failedTraces: string[] = [];
      traceResults.forEach((tr, i) => {
        if (tr.status === "rejected")
          failedTraces.push([baseline, intervention][i]);
      });
      if (failedTraces.length > 0) {
        setCompareError(
          `Trace data unavailable for: ${failedTraces.join(", ")}. Run these scenarios first.`,
        );
        setCompareLoading(false);
        return;
      }

      const traces = traceResults.map(
        (tr) => (tr as PromiseFulfilledResult<TraceResponse>).value,
      );
      const years = traces[0]?.years ?? [];
      const trajData: Array<Record<string, number>> = [];
      for (let yi = 0; yi < years.length; yi++) {
        const pt: Record<string, number> = { year: years[yi] };
        const baseVals = traces[0].field_values?.total_ghg ?? traces[0].values;
        const intvVals = traces[1].field_values?.total_ghg ?? traces[1].values;
        pt[baseline] = baseVals[yi] ?? 0;
        pt[intervention] = intvVals[yi] ?? 0;
        trajData.push(pt);
      }
      setCompareData({ trajectory: trajData });

      // Fetch grid traces
      const gridTraceResults = await Promise.allSettled(
        [baseline, intervention].map((name) =>
          api.getTrace(name, "grid_ghg_per_kwh"),
        ),
      );
      const gridTraces = gridTraceResults.map((tr) =>
        tr.status === "fulfilled"
          ? (tr as PromiseFulfilledResult<TraceResponse>).value
          : null,
      );

      // Extract 5 metrics for summary cards
      const emissionsFields = [
        "total_ghg",
        "usage_ghg_gas",
        "usage_ghg_electric",
        "production_ghg",
      ];
      const baselineMetrics: Record<string, number[]> = {};
      const interventionMetrics: Record<string, number[]> = {};
      for (const field of emissionsFields) {
        baselineMetrics[field] =
          traces[0].field_values?.[field] ?? traces[0].values;
        interventionMetrics[field] =
          traces[1].field_values?.[field] ?? traces[1].values;
      }
      baselineMetrics["grid_ghg_per_kwh"] = gridTraces[0]?.values ?? [];
      interventionMetrics["grid_ghg_per_kwh"] = gridTraces[1]?.values ?? [];

      setMetricTraces({
        years,
        baseline: baselineMetrics,
        intervention: interventionMetrics,
      });
    } catch {
      setCompareError("Comparison failed. Is the API running?");
    } finally {
      setCompareLoading(false);
    }
  };

  const compareScenarios = [selectedScenario, compareScenario];

  const tabStyle = (tab: Tab): React.CSSProperties => ({
    padding: "8px 20px",
    fontSize: 14,
    fontWeight: activeTab === tab ? 600 : 400,
    color: activeTab === tab ? "var(--text-primary)" : "var(--text-secondary)",
    background: activeTab === tab ? "var(--bg-elevated)" : "transparent",
    borderTop:
      activeTab === tab
        ? "1px solid var(--border-subtle)"
        : "1px solid transparent",
    borderLeft:
      activeTab === tab
        ? "1px solid var(--border-subtle)"
        : "1px solid transparent",
    borderRight:
      activeTab === tab
        ? "1px solid var(--border-subtle)"
        : "1px solid transparent",
    borderBottom:
      activeTab === tab
        ? "1px solid var(--bg-primary)"
        : "1px solid var(--border-subtle)",
    borderRadius: "6px 6px 0 0",
    cursor: "pointer",
    marginBottom: -1,
  });

  return (
    <div style={{ padding: 32, minHeight: "100vh" }}>
      {/* Header with scenario selector */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 36,
            fontWeight: 700,
          }}
        >
          Scenario Dashboard
        </h1>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <label
            style={{
              fontSize: 13,
              color: "var(--text-secondary)",
            }}
          >
            Scenario:
          </label>
          <select
            value={selectedScenario}
            onChange={(e) => {
              setSelectedScenario(e.target.value);
              setCompareData(null);
              setMetricTraces(null);
            }}
            style={{
              background: "var(--bg-surface)",
              color: "var(--text-primary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "6px 12px",
              fontSize: 14,
              fontFamily: "inherit",
            }}
          >
            {scenarios.length === 0 && (
              <option value="baseline">baseline</option>
            )}
            {scenarios.map((name) => (
              <option key={name} value={name}>
                {name}
                {runStatus[name] === "not-run" ? " (not run)" : ""}
              </option>
            ))}
          </select>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: apiHealthy ? "#34d399" : "#556178",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              color: "var(--text-muted)",
            }}
          >
            {apiHealthy ? "Live" : "Offline"}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid var(--border-subtle)",
          marginBottom: 24,
        }}
      >
        <button
          onClick={() => setActiveTab("overview")}
          style={tabStyle("overview")}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab("compare")}
          style={tabStyle("compare")}
        >
          Compare
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <>
          {overviewLoading && (
            <div style={{ color: "var(--text-muted)", marginBottom: 24 }}>
              Loading scenario data...
            </div>
          )}

          {/* Headline Metrics */}
          {metrics && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: 20,
                marginBottom: 24,
              }}
            >
              <Card>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: 10,
                  }}
                >
                  Total Fleet Size
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 32,
                    fontWeight: 700,
                    marginBottom: 4,
                  }}
                >
                  {fmt(metrics.fleet_size)}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  vehicles in simulation
                </div>
              </Card>
              <Card>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: 10,
                  }}
                >
                  Annual GHG (Year 1)
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 32,
                    fontWeight: 700,
                    marginBottom: 4,
                  }}
                >
                  {metrics.annual_ghg.toFixed(1)}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  Mt CO2e
                </div>
              </Card>
              <Card>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: 10,
                  }}
                >
                  BEV Share
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 32,
                    fontWeight: 700,
                    color: "var(--accent-green)",
                    marginBottom: 4,
                  }}
                >
                  {metrics.bev_share.toFixed(1)}%
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  of fleet &rarr; {metrics.bev_share_final.toFixed(1)}% by 2033
                </div>
              </Card>
              <Card>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    marginBottom: 10,
                  }}
                >
                  Total VMT
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 32,
                    fontWeight: 700,
                    marginBottom: 4,
                  }}
                >
                  {fmt(metrics.total_vmt)}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  miles driven annually
                </div>
              </Card>
            </div>
          )}

          {/* Charts */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 20,
              marginBottom: 24,
            }}
          >
            <Card
              title="GHG Emissions by Component"
              subtitle="10-year trajectory (Mt CO2e)"
            >
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={trajectory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="year"
                    stroke="#556178"
                    style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                  />
                  <YAxis
                    stroke="#556178"
                    style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(v) => `${Number(v).toFixed(1)} Mt`}
                  />
                  <Legend wrapperStyle={{ fontSize: 12, color: "#8b95a8" }} />
                  <Area
                    type="monotone"
                    dataKey="usage"
                    name="Usage"
                    stackId="1"
                    stroke="#f87171"
                    fill="#f87171"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="production"
                    name="Production"
                    stackId="1"
                    stroke="#fbbf24"
                    fill="#fbbf24"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="disposal"
                    name="Disposal"
                    stackId="1"
                    stroke="#a78bfa"
                    fill="#a78bfa"
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Card>

            <Card
              title="Fleet Composition"
              subtitle="Powertrain share evolution (%)"
            >
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={composition}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="year"
                    stroke="#556178"
                    style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                  />
                  <YAxis
                    stroke="#556178"
                    style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(v) => `${Number(v).toFixed(1)}%`}
                  />
                  <Legend wrapperStyle={{ fontSize: 12, color: "#8b95a8" }} />
                  <Area
                    type="monotone"
                    dataKey="BEV"
                    stackId="1"
                    stroke="#34d399"
                    fill="#34d399"
                    fillOpacity={0.7}
                  />
                  <Area
                    type="monotone"
                    dataKey="PHEV"
                    stackId="1"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.7}
                  />
                  <Area
                    type="monotone"
                    dataKey="HEV"
                    stackId="1"
                    stroke="#fbbf24"
                    fill="#fbbf24"
                    fillOpacity={0.7}
                  />
                  <Area
                    type="monotone"
                    dataKey="ICEV"
                    stackId="1"
                    stroke="#f87171"
                    fill="#f87171"
                    fillOpacity={0.7}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card title="Quick Actions">
            <div style={{ display: "flex", gap: 12 }}>
              <Button variant="primary" onClick={() => navigate("/scenarios")}>
                Run Simulation
              </Button>
              <Button onClick={() => setActiveTab("compare")}>
                Compare Scenarios
              </Button>
              <Button onClick={() => navigate("/sensitivity")}>
                Sensitivity Analysis
              </Button>
              <Button onClick={() => navigate("/graph")}>
                Explore Causal Graph
              </Button>
            </div>
          </Card>
        </>
      )}

      {/* Compare Tab */}
      {activeTab === "compare" && (
        <>
          <Card title="Compare Against" style={{ marginBottom: 24 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                Baseline: <strong>{selectedScenario}</strong>
              </span>
              <span style={{ color: "var(--text-muted)" }}>vs</span>
              <select
                value={compareScenario}
                onChange={(e) => setCompareScenario(e.target.value)}
                style={{
                  background: "var(--bg-surface)",
                  color: "var(--text-primary)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "6px 12px",
                  fontSize: 14,
                  fontFamily: "inherit",
                }}
              >
                <option value="">Select scenario...</option>
                {scenarios
                  .filter((n) => n !== selectedScenario)
                  .map((name) => (
                    <option key={name} value={name}>
                      {name}
                      {runStatus[name] === "not-run" ? " (not run)" : ""}
                    </option>
                  ))}
              </select>
              <Button
                variant="primary"
                onClick={() => runComparison(selectedScenario, compareScenario)}
                disabled={
                  !compareScenario ||
                  compareLoading ||
                  runStatus[compareScenario] === "not-run" ||
                  runStatus[selectedScenario] === "not-run"
                }
              >
                {compareLoading ? "Comparing..." : "Compare"}
              </Button>
            </div>
            {compareError && (
              <div
                style={{
                  color: "var(--accent-red)",
                  fontSize: 13,
                  marginTop: 8,
                }}
              >
                {compareError}
              </div>
            )}
          </Card>

          {compareData && (
            <>
              <Card title="GHG Trajectory" style={{ marginBottom: 24 }}>
                <ResponsiveContainer width="100%" height={380}>
                  <LineChart data={compareData.trajectory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="year"
                      stroke="#556178"
                      style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                    />
                    <YAxis
                      stroke="#556178"
                      style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                    />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ color: "#8b95a8" }} />
                    {/* Delta shading */}
                    {compareData.trajectory.length > 1 &&
                      (() => {
                        const [base, intv] = compareScenarios;
                        const areas: React.ReactElement[] = [];
                        for (
                          let i = 0;
                          i < compareData.trajectory.length - 1;
                          i++
                        ) {
                          const y1 = compareData.trajectory[i].year;
                          const y2 = compareData.trajectory[i + 1].year;
                          const avgBase =
                            ((compareData.trajectory[i][base] ?? 0) +
                              (compareData.trajectory[i + 1][base] ?? 0)) /
                            2;
                          const avgIntv =
                            ((compareData.trajectory[i][intv] ?? 0) +
                              (compareData.trajectory[i + 1][intv] ?? 0)) /
                            2;
                          areas.push(
                            <ReferenceArea
                              key={`delta-${y1}`}
                              x1={y1}
                              x2={y2}
                              fill={
                                avgIntv < avgBase ? "#34d39920" : "#f871711f"
                              }
                              strokeOpacity={0}
                            />,
                          );
                        }
                        // Crossover
                        for (
                          let i = 0;
                          i < compareData.trajectory.length - 1;
                          i++
                        ) {
                          const d1 =
                            (compareData.trajectory[i][intv] ?? 0) -
                            (compareData.trajectory[i][base] ?? 0);
                          const d2 =
                            (compareData.trajectory[i + 1][intv] ?? 0) -
                            (compareData.trajectory[i + 1][base] ?? 0);
                          if ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) {
                            const crossYear =
                              compareData.trajectory[i + 1].year;
                            areas.push(
                              <ReferenceLine
                                key={`crossover-${crossYear}`}
                                x={crossYear}
                                stroke="#fbbf24"
                                strokeDasharray="4 4"
                              >
                                <Label
                                  value={`Crossover: ${crossYear}`}
                                  position="top"
                                  fill="#fbbf24"
                                  fontSize={11}
                                />
                              </ReferenceLine>,
                            );
                            break;
                          }
                        }
                        // Final-year annotation
                        const lastPt =
                          compareData.trajectory[
                            compareData.trajectory.length - 1
                          ];
                        const finalBase = lastPt[base] ?? 0;
                        const finalIntv = lastPt[intv] ?? 0;
                        const finalPct =
                          finalBase !== 0
                            ? ((finalIntv - finalBase) / finalBase) * 100
                            : null;
                        if (finalPct != null) {
                          areas.push(
                            <ReferenceLine
                              key="final-year"
                              x={lastPt.year}
                              stroke="none"
                            >
                              <Label
                                value={`${finalPct > 0 ? "+" : ""}${finalPct.toFixed(1)}% by ${lastPt.year}`}
                                position="insideTopRight"
                                fill={finalPct < 0 ? "#34d399" : "#f87171"}
                                fontSize={12}
                                fontWeight={600}
                              />
                            </ReferenceLine>,
                          );
                        }
                        return areas;
                      })()}
                    {compareScenarios.map((s, i) => (
                      <Fragment key={s}>
                        <Line
                          type="monotone"
                          dataKey={s}
                          stroke={COLORS[i % COLORS.length]}
                          strokeWidth={2}
                          dot={false}
                          name={s}
                        />
                      </Fragment>
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </Card>

              {metricTraces && metricTraces.years.length > 0 && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                    gap: 12,
                    marginBottom: 24,
                  }}
                >
                  {(
                    [
                      {
                        key: "total_ghg",
                        label: "Total GHG",
                        unit: "Mt CO2e",
                      },
                      {
                        key: "usage_ghg_gas",
                        label: "Gas Usage Emissions",
                        unit: "Mt CO2e",
                      },
                      {
                        key: "usage_ghg_electric",
                        label: "Electric Usage Emissions",
                        unit: "Mt CO2e",
                      },
                      {
                        key: "production_ghg",
                        label: "Production Emissions",
                        unit: "Mt CO2e",
                      },
                      {
                        key: "grid_ghg_per_kwh",
                        label: "Grid Carbon Intensity",
                        unit: "kg CO2/kWh",
                      },
                    ] as const
                  ).map(({ key, label, unit }) => (
                    <DeltaSummaryCard
                      key={key}
                      metric={label}
                      baselineValues={metricTraces.baseline[key] ?? []}
                      interventionValues={metricTraces.intervention[key] ?? []}
                      years={metricTraces.years}
                      unit={unit}
                      expanded={expandedCard === key}
                      onToggle={() =>
                        setExpandedCard((prev) => (prev === key ? null : key))
                      }
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
