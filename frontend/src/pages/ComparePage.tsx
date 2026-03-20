import { useState, useEffect, Fragment } from "react";
import {
  LineChart,
  Line,
  Area,
  BarChart,
  Bar,
  Cell,
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

interface Scenario {
  name: string;
}

type RunStatus = "checking" | "ready" | "not-run";

interface ComparisonData {
  trajectory: Array<Record<string, number>>;
  deltas: Array<{
    node: string;
    year: number;
    absolute: number;
    percentage: number | null;
  }>;
  attribution?: Array<{ intervention: string; contribution: number }>;
}

const DEMO_SCENARIOS: Scenario[] = [
  { name: "Baseline" },
  { name: "High EV Adoption" },
];

const generateDemoData = (selected: string[]): ComparisonData => {
  const trajectory: Array<Record<string, number>> = [];
  for (let i = 0; i <= 10; i++) {
    const pt: Record<string, number> = { year: 2024 + i };
    selected.forEach((s) => {
      const base = s === "Baseline" ? 100 + i * 8 : 100 + i * 3.5;
      pt[s] = base;
      pt[`${s}_p5`] = base - 10;
      pt[`${s}_p25`] = base - 5;
      pt[`${s}_p75`] = base + 5;
      pt[`${s}_p95`] = base + 10;
    });
    trajectory.push(pt);
  }
  return {
    trajectory,
    deltas: [
      {
        node: "Fleet Operations",
        year: 2030,
        absolute: -25.3,
        percentage: -18.5,
      },
      {
        node: "Vehicle Production",
        year: 2030,
        absolute: 8.2,
        percentage: 12.3,
      },
      {
        node: "Fuel Lifecycle",
        year: 2030,
        absolute: -32.1,
        percentage: -28.7,
      },
      { node: "End of Life", year: 2030, absolute: -2.4, percentage: -8.2 },
    ],
    attribution: [
      { intervention: "EV Adoption Rate", contribution: -35.2 },
      { intervention: "Grid Decarbonization", contribution: -18.4 },
      { intervention: "Vehicle Efficiency", contribution: -12.8 },
      { intervention: "Production Emissions", contribution: 8.5 },
      { intervention: "VMT Reduction", contribution: -6.3 },
    ],
  };
};

const COLORS = ["#22d3ee", "#a78bfa", "#fbbf24", "#34d399"];
const tooltipStyle = {
  backgroundColor: "#1f2a3f",
  border: "1px solid #1e293b",
  borderRadius: "8px",
  color: "#e8ecf4",
};

export default function ComparePage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [data, setData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [runStatus, setRunStatus] = useState<Record<string, RunStatus>>({});
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  const [metricTraces, setMetricTraces] = useState<{
    years: number[];
    baseline: Record<string, number[]>;
    intervention: Record<string, number[]>;
  } | null>(null);

  const runComparison = async (scenarioNames: string[]) => {
    if (scenarioNames.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const [baseline, ...rest] = scenarioNames;
      const result = await api.compare(baseline, rest);

      const traceResults = await Promise.allSettled(
        scenarioNames.map((name) => api.getTrace(name, "total_emissions")),
      );

      const failedTraces: string[] = [];
      traceResults.forEach((tr, i) => {
        if (tr.status === "rejected") failedTraces.push(scenarioNames[i]);
      });

      if (failedTraces.length > 0) {
        setError(
          `Trace data unavailable for: ${failedTraces.join(", ")}. Run these scenarios first.`,
        );
        setLoading(false);
        return;
      }

      const traces = traceResults.map(
        (tr) => (tr as PromiseFulfilledResult<TraceResponse>).value,
      );
      const years = traces[0]?.years ?? [];
      const trajectory: Array<Record<string, number>> = [];
      for (let yi = 0; yi < years.length; yi++) {
        const pt: Record<string, number> = { year: years[yi] };
        traces.forEach((trace, si) => {
          const vals = trace.field_values?.total_ghg ?? trace.values;
          pt[scenarioNames[si]] = vals[yi] ?? 0;
        });
        trajectory.push(pt);
      }

      // Fetch grid_ghg_per_kwh traces for both scenarios
      const gridTraceResults = await Promise.allSettled(
        scenarioNames.map((name) => api.getTrace(name, "grid_ghg_per_kwh")),
      );
      const gridTraces = gridTraceResults.map((tr) =>
        tr.status === "fulfilled"
          ? (tr as PromiseFulfilledResult<TraceResponse>).value
          : null,
      );

      // Extract 5 metrics for summary cards (baseline = first scenario, intervention = second)
      if (scenarioNames.length >= 2) {
        const emissionsFields = [
          "total_ghg",
          "usage_ghg_gas",
          "usage_ghg_electric",
          "production_ghg",
        ];
        const baselineEmissions = traces[0];
        const interventionEmissions = traces[1];

        const baselineMetrics: Record<string, number[]> = {};
        const interventionMetrics: Record<string, number[]> = {};

        for (const field of emissionsFields) {
          baselineMetrics[field] =
            baselineEmissions.field_values?.[field] ?? baselineEmissions.values;
          interventionMetrics[field] =
            interventionEmissions.field_values?.[field] ??
            interventionEmissions.values;
        }

        // Grid intensity
        const baselineGrid = gridTraces[0];
        const interventionGrid = gridTraces[1];
        baselineMetrics["grid_ghg_per_kwh"] = baselineGrid?.values ?? [];
        interventionMetrics["grid_ghg_per_kwh"] =
          interventionGrid?.values ?? [];

        setMetricTraces({
          years,
          baseline: baselineMetrics,
          intervention: interventionMetrics,
        });
      }

      const comparisonData: ComparisonData = {
        trajectory,
        deltas: [],
        attribution: undefined,
      };

      for (const [, comp] of Object.entries(result.comparisons ?? {})) {
        const compDeltas =
          (
            comp as {
              deltas: Array<{
                node_name: string;
                year: number;
                absolute_delta: number;
                percentage_delta: number;
              }>;
            }
          ).deltas ?? [];
        compDeltas.forEach((d) => {
          comparisonData.deltas.push({
            node: d.node_name,
            year: d.year,
            absolute: d.absolute_delta,
            percentage: d.percentage_delta,
          });
        });
      }
      setData(comparisonData);
    } catch {
      if (demoMode) {
        setData(generateDemoData(scenarioNames));
      } else {
        setError("Comparison failed. Is the API running?");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api
      .listScenarios()
      .then(async (list) => {
        const scenarioList = list.map((s) => ({ name: s.name }));
        setScenarios(scenarioList);
        setDemoMode(false);
        const statusMap: Record<string, RunStatus> = {};
        for (const s of scenarioList) {
          statusMap[s.name] = "checking";
        }
        setRunStatus({ ...statusMap });
        await Promise.all(
          scenarioList.map(async (s) => {
            try {
              await api.getTrace(s.name, "total_emissions");
              statusMap[s.name] = "ready";
            } catch {
              statusMap[s.name] = "not-run";
            }
          }),
        );
        setRunStatus({ ...statusMap });

        // Auto-select and compare if standard scenarios are ready
        const standardPair = ["baseline", "ev-grid-intervention"];
        if (standardPair.every((n) => statusMap[n] === "ready")) {
          setSelected(standardPair);
          runComparison(standardPair);
        }
      })
      .catch(() => {
        setScenarios(DEMO_SCENARIOS);
        setDemoMode(true);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggle = (name: string) =>
    setSelected((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name],
    );

  const compare = () => runComparison(selected);

  const exportCSV = () => {
    if (!data) return;
    const csv = [
      "Year," + selected.join(","),
      ...data.trajectory.map((r) =>
        [r.year, ...selected.map((s) => r[s])].join(","),
      ),
    ].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = "comparison.csv";
    a.click();
  };

  return (
    <div style={{ padding: 32 }}>
      <h1
        style={{
          fontFamily: "var(--font-display)",
          fontSize: 36,
          fontWeight: 700,
          marginBottom: 24,
        }}
      >
        Scenario Comparison
      </h1>

      <Card title="Select Scenarios" style={{ marginBottom: 24 }}>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            marginBottom: 16,
          }}
        >
          {scenarios.map((s) => {
            const status = runStatus[s.name];
            return (
              <label
                key={s.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(s.name)}
                  onChange={() => toggle(s.name)}
                />
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    backgroundColor:
                      !status || status === "checking"
                        ? "#556178"
                        : status === "ready"
                          ? "#34d399"
                          : "#556178",
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: 14 }}>{s.name}</span>
                {status === "not-run" && (
                  <span
                    style={{
                      fontSize: 11,
                      color: "#8b95a8",
                      marginLeft: 4,
                    }}
                  >
                    Not run
                  </span>
                )}
              </label>
            );
          })}
        </div>
        {error && (
          <div
            style={{
              color: "var(--accent-red)",
              fontSize: 13,
              marginBottom: 12,
            }}
          >
            {error}
          </div>
        )}
        {(() => {
          const unrunSelected = selected.filter(
            (n) => runStatus[n] === "not-run",
          );
          const hasUnrun = !demoMode && unrunSelected.length > 0;
          return (
            <>
              <Button
                variant="primary"
                onClick={compare}
                disabled={loading || selected.length < 2 || hasUnrun}
              >
                {loading ? "Comparing..." : "Compare"}
              </Button>
              {hasUnrun && (
                <div
                  style={{
                    color: "#fbbf24",
                    fontSize: 12,
                    marginTop: 8,
                  }}
                >
                  Run these scenarios first: {unrunSelected.join(", ")}
                </div>
              )}
            </>
          );
        })()}
      </Card>

      {data && (
        <>
          <Card
            title="GHG Trajectory"
            style={{ marginBottom: 24 }}
            actions={
              <>
                <Button size="sm" onClick={exportCSV}>
                  CSV
                </Button>
                <Button size="sm" onClick={() => alert("PNG export TBD")}>
                  PNG
                </Button>
              </>
            }
          >
            <ResponsiveContainer width="100%" height={380}>
              <LineChart data={data.trajectory}>
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
                {/* Delta shading between baseline and intervention */}
                {selected.length === 2 &&
                  data.trajectory.length > 1 &&
                  (() => {
                    const [base, intv] = selected;
                    const areas: React.ReactElement[] = [];
                    for (let i = 0; i < data.trajectory.length - 1; i++) {
                      const y1 = data.trajectory[i].year;
                      const y2 = data.trajectory[i + 1].year;
                      const avgBase =
                        ((data.trajectory[i][base] ?? 0) +
                          (data.trajectory[i + 1][base] ?? 0)) /
                        2;
                      const avgIntv =
                        ((data.trajectory[i][intv] ?? 0) +
                          (data.trajectory[i + 1][intv] ?? 0)) /
                        2;
                      const fill =
                        avgIntv < avgBase ? "#34d39920" : "#f871711f";
                      areas.push(
                        <ReferenceArea
                          key={`delta-${y1}`}
                          x1={y1}
                          x2={y2}
                          fill={fill}
                          strokeOpacity={0}
                        />,
                      );
                    }
                    // Crossover annotation
                    for (let i = 0; i < data.trajectory.length - 1; i++) {
                      const d1 =
                        (data.trajectory[i][intv] ?? 0) -
                        (data.trajectory[i][base] ?? 0);
                      const d2 =
                        (data.trajectory[i + 1][intv] ?? 0) -
                        (data.trajectory[i + 1][base] ?? 0);
                      if ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) {
                        const crossYear = data.trajectory[i + 1].year;
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
                    const lastPt = data.trajectory[data.trajectory.length - 1];
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
                {selected.map((s, i) => (
                  <Fragment key={s}>
                    <Area
                      type="monotone"
                      dataKey={`${s}_p95`}
                      stroke="none"
                      fill={COLORS[i % COLORS.length]}
                      fillOpacity={0.08}
                      legendType="none"
                    />
                    <Area
                      type="monotone"
                      dataKey={`${s}_p25`}
                      stroke="none"
                      fill={COLORS[i % COLORS.length]}
                      fillOpacity={0.15}
                      legendType="none"
                    />
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
                  { key: "total_ghg", label: "Total GHG", unit: "Mt CO2e" },
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

          {data.attribution && (
            <Card title="Attribution Waterfall">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.attribution}
                  layout="vertical"
                  margin={{ left: 140, right: 30 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    type="number"
                    stroke="#556178"
                    style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                  />
                  <YAxis
                    type="category"
                    dataKey="intervention"
                    stroke="#556178"
                    style={{ fontSize: 12 }}
                  />
                  <Tooltip contentStyle={tooltipStyle} />
                  <ReferenceLine x={0} stroke="#556178" strokeWidth={2} />
                  <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
                    {data.attribution.map((entry, idx) => (
                      <Cell
                        key={idx}
                        fill={entry.contribution < 0 ? "#34d399" : "#f87171"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
