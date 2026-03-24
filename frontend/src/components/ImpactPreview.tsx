import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
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

function DeltaCard({
  label,
  value,
  pct,
  unit,
}: {
  label: string;
  value: number;
  pct: number;
  unit: string;
}) {
  const isPositive = value > 0;
  // For BEV Share, positive is good (green); for others positive is bad (red)
  const color =
    label === "BEV Share"
      ? isPositive
        ? "var(--accent-green)"
        : "var(--accent-red)"
      : isPositive
        ? "var(--accent-red)"
        : "var(--accent-green)";

  const fmt = (n: number) => {
    const abs = Math.abs(n);
    if (abs >= 1e9) return (n / 1e9).toFixed(1) + "B";
    if (abs >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (abs >= 1e3) return (n / 1e3).toFixed(1) + "K";
    if (abs >= 1) return n.toFixed(1);
    return n.toFixed(3);
  };

  return (
    <div
      style={{
        padding: "12px 16px",
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
      }}
    >
      <div
        style={{
          fontSize: 10,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.5px",
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 20,
          fontWeight: 700,
          fontFamily: "var(--font-display)",
          color,
          marginBottom: 2,
        }}
      >
        {isPositive ? "+" : ""}
        {fmt(value)} {unit}
      </div>
      <div style={{ fontSize: 11, color }}>
        {isPositive ? "+" : ""}
        {pct.toFixed(1)}% by 2033
      </div>
    </div>
  );
}

export default function ImpactPreview({
  data,
  scenarioName,
  isRunning,
  error,
}: Props) {
  if (scenarioName === "baseline") {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "var(--text-muted)",
          fontSize: 13,
          padding: 24,
        }}
      >
        This is the baseline scenario. Select or create an intervention scenario
        to see impact preview.
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
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "var(--text-muted)",
          fontSize: 13,
          padding: 24,
        }}
      >
        Adjust interventions to see a live impact preview.
      </div>
    );
  }

  const trajData = data
    ? data.baselineTrajectory.map((b, i) => ({
        year: b.year,
        baseline: b.ghg,
        scenario: data.scenarioTrajectory[i]?.ghg ?? 0,
      }))
    : [];

  return (
    <div
      style={{
        padding: "0 24px 24px 0",
        display: "flex",
        flexDirection: "column",
        gap: 16,
        opacity: isRunning ? 0.5 : 1,
        transition: "opacity 0.2s",
      }}
    >
      {isRunning && (
        <div
          style={{
            fontSize: 12,
            color: "var(--accent-blue)",
            fontFamily: "var(--font-mono)",
          }}
        >
          Running simulation...
        </div>
      )}

      {data && (
        <>
          {/* Delta cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 10,
            }}
          >
            <DeltaCard
              label="Total GHG"
              value={data.deltas.totalGhg.value}
              pct={data.deltas.totalGhg.pct}
              unit="Mt"
            />
            <DeltaCard
              label="BEV Share"
              value={data.deltas.bevShare.value}
              pct={data.deltas.bevShare.pct}
              unit="pp"
            />
            <DeltaCard
              label="Fleet Size"
              value={data.deltas.fleetSize.value}
              pct={data.deltas.fleetSize.pct}
              unit=""
            />
            <DeltaCard
              label="Grid Intensity"
              value={data.deltas.gridIntensity.value}
              pct={data.deltas.gridIntensity.pct}
              unit="kg/kWh"
            />
          </div>

          {/* GHG Trajectory */}
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: 16,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8 }}>
              GHG Trajectory (Mt CO2e)
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trajData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="year"
                  stroke="#556178"
                  style={{ fontSize: 10, fontFamily: "JetBrains Mono" }}
                />
                <YAxis
                  stroke="#556178"
                  style={{ fontSize: 10, fontFamily: "JetBrains Mono" }}
                />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 11, color: "#8b95a8" }} />
                {trajData.length > 1 &&
                  trajData
                    .slice(0, -1)
                    .map((pt, i) => (
                      <ReferenceArea
                        key={pt.year}
                        x1={pt.year}
                        x2={trajData[i + 1].year}
                        fill={
                          trajData[i].scenario < trajData[i].baseline
                            ? "#34d39920"
                            : "#f871711f"
                        }
                        strokeOpacity={0}
                      />
                    ))}
                <Line
                  type="monotone"
                  dataKey="baseline"
                  stroke="#556178"
                  strokeDasharray="6 3"
                  strokeWidth={1.5}
                  dot={false}
                  name="Baseline"
                />
                <Line
                  type="monotone"
                  dataKey="scenario"
                  stroke="#22d3ee"
                  strokeWidth={2}
                  dot={false}
                  name={scenarioName}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Fleet Composition */}
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: 16,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8 }}>
              Fleet Composition (%)
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={data.composition}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="year"
                  stroke="#556178"
                  style={{ fontSize: 10, fontFamily: "JetBrains Mono" }}
                />
                <YAxis
                  stroke="#556178"
                  style={{ fontSize: 10, fontFamily: "JetBrains Mono" }}
                  domain={[0, 100]}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={
                    ((v: unknown) => `${Number(v).toFixed(1)}%`) as never
                  }
                />
                <Legend wrapperStyle={{ fontSize: 11, color: "#8b95a8" }} />
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
          </div>
        </>
      )}
    </div>
  );
}
