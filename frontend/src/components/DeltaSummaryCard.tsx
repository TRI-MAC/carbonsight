import { useState } from "react";
import { LineChart, Line, ResponsiveContainer, ReferenceLine } from "recharts";

function formatNum(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e9) return (v / 1e9).toFixed(2) + "B";
  if (abs >= 1e6) return (v / 1e6).toFixed(2) + "M";
  if (abs >= 1e3) return (v / 1e3).toFixed(1) + "K";
  if (abs >= 1) return v.toFixed(2);
  if (abs >= 0.01) return v.toFixed(3);
  return v.toFixed(4);
}

interface DeltaSummaryCardProps {
  metric: string;
  baselineValues: number[];
  interventionValues: number[];
  years: number[];
  unit?: string;
  expanded?: boolean;
  onToggle?: () => void;
}

export default function DeltaSummaryCard({
  metric,
  baselineValues,
  interventionValues,
  years,
  unit = "Mt CO2e",
  expanded = false,
  onToggle,
}: DeltaSummaryCardProps) {
  const [internalExpanded, setInternalExpanded] = useState(false);
  const isExpanded = onToggle ? expanded : internalExpanded;
  const toggle = onToggle ?? (() => setInternalExpanded((p) => !p));

  const deltas = years.map((_, i) => interventionValues[i] - baselineValues[i]);
  const finalIdx = deltas.length - 1;
  const finalDelta = deltas[finalIdx] ?? 0;
  const finalBaseline = baselineValues[finalIdx] ?? 0;
  const pctDelta =
    finalBaseline !== 0 ? (finalDelta / finalBaseline) * 100 : null;

  const isReduction = finalDelta < 0;
  const color = isReduction ? "#34d399" : "#f87171";
  const arrow = isReduction ? "\u2193" : "\u2191";

  const sparkData = deltas.map((d, i) => ({ year: years[i], delta: d }));

  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        cursor: "pointer",
        transition: "border-color 0.15s",
      }}
      onClick={toggle}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggle();
        }
      }}
    >
      {/* Summary header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "14px 18px",
        }}
      >
        {/* Metric name */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 12,
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              fontFamily: "JetBrains Mono",
              marginBottom: 4,
            }}
          >
            {metric}
          </div>
          <div
            style={{
              fontSize: 20,
              fontWeight: 700,
              color,
              fontFamily: "var(--font-display)",
              lineHeight: 1.2,
            }}
          >
            {arrow} {finalDelta > 0 ? "+" : ""}
            {formatNum(finalDelta)}{" "}
            <span
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                fontWeight: 400,
              }}
            >
              {unit}
            </span>
          </div>
          {pctDelta != null && (
            <div
              style={{
                fontSize: 13,
                color,
                fontWeight: 600,
                marginTop: 2,
              }}
            >
              {pctDelta > 0 ? "+" : ""}
              {pctDelta.toFixed(1)}%
            </div>
          )}
        </div>

        {/* Sparkline */}
        <div style={{ width: 100, height: 36, flexShrink: 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparkData}>
              <ReferenceLine y={0} stroke="#556178" strokeDasharray="2 2" />
              <Line
                type="monotone"
                dataKey="delta"
                stroke={color}
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Expand indicator */}
        <div
          style={{
            fontSize: 14,
            color: "var(--text-muted)",
            transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.15s",
          }}
        >
          &#9660;
        </div>
      </div>

      {/* Accordion detail table */}
      {isExpanded && (
        <div
          style={{
            borderTop: "1px solid var(--border-subtle)",
            padding: "12px 18px",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #1e293b" }}>
                {["Year", "Baseline", "Intervention", "Delta"].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "6px 8px",
                      textAlign: "left",
                      color: "#8b95a8",
                      fontSize: 11,
                      fontFamily: "JetBrains Mono",
                      textTransform: "uppercase",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {years.map((year, i) => {
                const d = deltas[i];
                return (
                  <tr key={year} style={{ borderBottom: "1px solid #1e293b" }}>
                    <td
                      style={{
                        padding: "6px 8px",
                        fontSize: 12,
                        fontFamily: "JetBrains Mono",
                      }}
                    >
                      {year}
                    </td>
                    <td style={{ padding: "6px 8px", fontSize: 12 }}>
                      {formatNum(baselineValues[i])}
                    </td>
                    <td style={{ padding: "6px 8px", fontSize: 12 }}>
                      {formatNum(interventionValues[i])}
                    </td>
                    <td
                      style={{
                        padding: "6px 8px",
                        fontSize: 12,
                        color:
                          d < 0
                            ? "#34d399"
                            : d > 0
                              ? "#f87171"
                              : "var(--text-primary)",
                      }}
                    >
                      {d > 0 ? "+" : ""}
                      {formatNum(d)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
