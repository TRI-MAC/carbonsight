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
  ReferenceLine,
} from "recharts";
import { api } from "../api/client";
import Card from "../components/Card";
import Button from "../components/Button";

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
        (tr) =>
          (tr as PromiseFulfilledResult<import("../types").TraceResponse>)
            .value,
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

          <Card title="Delta Breakdown" style={{ marginBottom: 24 }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #1e293b" }}>
                  {["Node", "Year", "Absolute (Mt CO2e)", "Percentage"].map(
                    (h) => (
                      <th
                        key={h}
                        style={{
                          padding: "10px 12px",
                          textAlign: "left",
                          color: "#8b95a8",
                          fontSize: 12,
                          fontFamily: "JetBrains Mono",
                          textTransform: "uppercase",
                        }}
                      >
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {data.deltas.map((d, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #1e293b" }}>
                    <td style={{ padding: "10px 12px", fontSize: 13 }}>
                      {d.node}
                    </td>
                    <td style={{ padding: "10px 12px", fontSize: 13 }}>
                      {d.year}
                    </td>
                    <td
                      style={{
                        padding: "10px 12px",
                        fontSize: 13,
                        color: d.absolute < 0 ? "#34d399" : "#f87171",
                      }}
                    >
                      {d.absolute > 0 ? "+" : ""}
                      {d.absolute.toFixed(1)}
                    </td>
                    <td
                      style={{
                        padding: "10px 12px",
                        fontSize: 13,
                        color: d.percentage != null && d.percentage < 0 ? "#34d399" : "#f87171",
                      }}
                    >
                      {d.percentage != null
                        ? `${d.percentage > 0 ? "+" : ""}${d.percentage.toFixed(1)}%`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

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
