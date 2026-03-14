import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export interface Trace {
  scenario: string;
  years: number[];
  values: number[];
}

interface NodeTraceChartProps {
  traces: Trace[];
  nodeName: string;
  fieldName?: string;
}

const COLORS = [
  "#22d3ee",
  "#a78bfa",
  "#fbbf24",
  "#34d399",
  "#f87171",
  "#3b82f6",
];

const tooltipStyle = {
  backgroundColor: "#1f2a3f",
  border: "1px solid #1e293b",
  borderRadius: "8px",
  color: "#e8ecf4",
};

export default function NodeTraceChart({
  traces,
  nodeName,
  fieldName,
}: NodeTraceChartProps) {
  if (traces.length === 0) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: 200,
          color: "var(--text-muted)",
          fontSize: 13,
        }}
      >
        No trace data available
      </div>
    );
  }

  // Build chart data: one object per year with a key per scenario
  const allYears = traces[0].years;
  const data = allYears.map((year, i) => {
    const point: Record<string, number> = { year };
    traces.forEach((t) => {
      point[t.scenario] = t.values[i] ?? 0;
    });
    return point;
  });

  const showLegend = traces.length > 1;

  return (
    <div>
      <div
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: "var(--text-secondary)",
          marginBottom: 4,
        }}
      >
        {nodeName}
        {fieldName && (
          <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>
            {" "}
            / {fieldName}
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
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
          {showLegend && (
            <Legend wrapperStyle={{ fontSize: 12, color: "#8b95a8" }} />
          )}
          {traces.map((t, i) => (
            <Line
              key={t.scenario}
              type="monotone"
              dataKey={t.scenario}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
