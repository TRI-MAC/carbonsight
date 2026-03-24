import {
  ComposedChart,
  Line,
  Area,
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
  /** UQ band data keyed by stat name (p5, p25, p75, p95, median) */
  bands?: Record<string, number[]>;
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

function hasUqBands(trace: Trace): boolean {
  return !!(trace.bands && trace.bands.p5 && trace.bands.p95);
}

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

  const anyUq = traces.some(hasUqBands);

  // Build chart data with band widths for stacking trick
  // To render a band between p5 and p95, we store p5 as the invisible base
  // and (p95 - p5) as the visible band height stacked on top
  const allYears = traces[0].years;
  const data = allYears.map((year, i) => {
    const point: Record<string, number> = { year };
    traces.forEach((t) => {
      if (hasUqBands(t)) {
        const p5 = t.bands!.p5[i];
        const p25 = t.bands!.p25?.[i] ?? p5;
        const p75 = t.bands!.p75?.[i] ?? t.bands!.p95[i];
        const p95 = t.bands!.p95[i];
        const median = t.bands!.median?.[i] ?? t.values[i] ?? 0;

        point[t.scenario] = median;
        // Outer band (90% CI): invisible base + visible range
        point[`${t.scenario}_p5`] = p5;
        point[`${t.scenario}_outer`] = p95 - p5;
        // Inner band (50% CI): invisible base + visible range
        point[`${t.scenario}_p25`] = p25;
        point[`${t.scenario}_inner`] = p75 - p25;
      } else {
        point[t.scenario] = t.values[i] ?? 0;
      }
    });
    return point;
  });

  const showLegend = traces.length > 1 || anyUq;

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
        {anyUq && (
          <span
            style={{
              marginLeft: 8,
              fontSize: 10,
              color: "var(--text-muted)",
              fontWeight: 400,
              fontStyle: "italic",
            }}
          >
            shaded = 90% CI, dark = 50% CI
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={anyUq ? 300 : 250}>
        <ComposedChart data={data}>
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
            formatter={
              ((value: unknown, name: unknown) => {
                const n = String(name ?? "");
                if (n.endsWith("_p5") || n.endsWith("_p25")) return null;
                const v = Number(value);
                if (n.endsWith("_outer")) return [v.toFixed(2), "90% CI width"];
                if (n.endsWith("_inner")) return [v.toFixed(2), "50% CI width"];
                return [v.toFixed(2), n];
              }) as never
            }
          />
          {showLegend && (
            <Legend
              wrapperStyle={{ fontSize: 12, color: "#8b95a8" }}
              {...{
                payload: traces.map((t, i) => ({
                  value: hasUqBands(t)
                    ? `${t.scenario} (median + CI)`
                    : t.scenario,
                  type: "line" as const,
                  color: COLORS[i % COLORS.length],
                  id: t.scenario,
                })),
              }}
            />
          )}
          {/* Render bands first (behind lines) */}
          {traces.map((t, i) => {
            if (!hasUqBands(t)) return null;
            const color = COLORS[i % COLORS.length];
            return [
              // Outer band: invisible p5 base + visible p5→p95 range
              <Area
                key={`${t.scenario}_p5`}
                type="monotone"
                dataKey={`${t.scenario}_p5`}
                stackId={`outer_${t.scenario}`}
                stroke="none"
                fill="transparent"
                legendType="none"
                tooltipType="none"
              />,
              <Area
                key={`${t.scenario}_outer`}
                type="monotone"
                dataKey={`${t.scenario}_outer`}
                stackId={`outer_${t.scenario}`}
                stroke="none"
                fill={color}
                fillOpacity={0.1}
                legendType="none"
                tooltipType="none"
              />,
              // Inner band: invisible p25 base + visible p25→p75 range
              <Area
                key={`${t.scenario}_p25`}
                type="monotone"
                dataKey={`${t.scenario}_p25`}
                stackId={`inner_${t.scenario}`}
                stroke="none"
                fill="transparent"
                legendType="none"
                tooltipType="none"
              />,
              <Area
                key={`${t.scenario}_inner`}
                type="monotone"
                dataKey={`${t.scenario}_inner`}
                stackId={`inner_${t.scenario}`}
                stroke="none"
                fill={color}
                fillOpacity={0.25}
                legendType="none"
                tooltipType="none"
              />,
            ];
          })}
          {/* Render lines on top */}
          {traces.map((t, i) => (
            <Line
              key={t.scenario}
              type="monotone"
              dataKey={t.scenario}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
              name={hasUqBands(t) ? `${t.scenario} (median)` : t.scenario}
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
