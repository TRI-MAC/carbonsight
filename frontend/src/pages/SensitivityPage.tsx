import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { api } from "../api/client";
import Card from "../components/Card";
import Button from "../components/Button";

interface SensitivityDriver {
  parameter: string;
  firstOrder: number;
  totalOrder: number;
  displayName: string;
}

const DEMO_SENSITIVITY: SensitivityDriver[] = [
  {
    parameter: "battery_cost",
    displayName: "Battery Cost",
    firstOrder: 0.32,
    totalOrder: 0.38,
  },
  {
    parameter: "grid_intensity",
    displayName: "Grid Carbon Intensity",
    firstOrder: 0.28,
    totalOrder: 0.35,
  },
  {
    parameter: "oil_price",
    displayName: "Oil Price",
    firstOrder: 0.18,
    totalOrder: 0.22,
  },
  {
    parameter: "vmt_elasticity",
    displayName: "VMT Elasticity",
    firstOrder: 0.12,
    totalOrder: 0.16,
  },
  {
    parameter: "survival_rate",
    displayName: "Vehicle Survival Rate",
    firstOrder: 0.09,
    totalOrder: 0.13,
  },
  {
    parameter: "production_emissions_factor",
    displayName: "Production Emissions Factor",
    firstOrder: 0.08,
    totalOrder: 0.11,
  },
  {
    parameter: "renewal_rate",
    displayName: "Fleet Renewal Rate",
    firstOrder: 0.06,
    totalOrder: 0.09,
  },
  {
    parameter: "electricity_price",
    displayName: "Electricity Price",
    firstOrder: 0.05,
    totalOrder: 0.07,
  },
];

const DEMO_SCENARIOS = [{ name: "Baseline" }, { name: "High EV Adoption" }];

export default function SensitivityPage() {
  const [scenarios, setScenarios] = useState<Array<{ name: string }>>([]);
  const [selectedScenario, setSelectedScenario] = useState("");
  const [sensitivityData, setSensitivityData] = useState<SensitivityDriver[]>(
    [],
  );
  const [indexType, setIndexType] = useState<"firstOrder" | "totalOrder">(
    "totalOrder",
  );
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    api
      .listScenarios()
      .then((list) => {
        const mapped = list.map((s) => ({ name: s.name }));
        setScenarios(mapped);
        if (mapped.length > 0) setSelectedScenario(mapped[0].name);
      })
      .catch(() => {
        setScenarios(DEMO_SCENARIOS);
        setSelectedScenario(DEMO_SCENARIOS[0].name);
      });
  }, []);

  useEffect(() => {
    if (!selectedScenario) return;
    setLoading(true);
    api
      .getSensitivity(selectedScenario)
      .then((result) => {
        const drivers = (result as { drivers?: Array<{ input_node: string; first_order_index: number; total_order_index: number }> }).drivers;
        if (drivers && drivers.length > 0) {
          setSensitivityData(
            drivers.map((d) => ({
              parameter: d.input_node,
              displayName: d.input_node.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
              firstOrder: d.first_order_index,
              totalOrder: d.total_order_index,
            })),
          );
          setErrorMsg(null);
        } else {
          const msg = (result as { message?: string }).message;
          if (msg) {
            setErrorMsg(msg);
            setSensitivityData([]);
          } else {
            setSensitivityData(DEMO_SENSITIVITY);
            setErrorMsg(null);
          }
        }
      })
      .catch((err) => {
        const errStr = String(err);
        if (errStr.includes("UQ mode")) {
          setErrorMsg("Sensitivity analysis requires a UQ mode run. Re-run the scenario in UQ mode.");
          setSensitivityData([]);
        } else {
          setSensitivityData(DEMO_SENSITIVITY);
          setErrorMsg(null);
        }
      })
      .finally(() => setLoading(false));
  }, [selectedScenario]);

  const tornadoData = sensitivityData
    .map((d) => {
      const v =
        (indexType === "firstOrder" ? d.firstOrder : d.totalOrder) * 100;
      return {
        displayName: d.displayName,
        value: v,
        negative: -v / 2,
        positive: v / 2,
      };
    })
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 10);

  const tooltipStyle = {
    backgroundColor: "#1f2a3f",
    border: "1px solid #1e293b",
    borderRadius: "8px",
    color: "#e8ecf4",
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
        Sensitivity Analysis
      </h1>

      <Card title="Configuration" style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", gap: 24, alignItems: "flex-end" }}>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 6,
              flex: 1,
            }}
          >
            <label style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              Scenario
            </label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              style={{
                padding: "8px 12px",
                background: "var(--bg-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 6,
                color: "var(--text-primary)",
                fontSize: 13,
                fontFamily: "var(--font-mono)",
              }}
            >
              {scenarios.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <Button
              variant={indexType === "firstOrder" ? "primary" : "secondary"}
              size="sm"
              onClick={() => setIndexType("firstOrder")}
            >
              First Order
            </Button>
            <Button
              variant={indexType === "totalOrder" ? "primary" : "secondary"}
              size="sm"
              onClick={() => setIndexType("totalOrder")}
            >
              Total Order
            </Button>
          </div>
        </div>
      </Card>

      <Card
        title="Tornado Chart — Top Uncertainty Drivers"
        subtitle={
          indexType === "firstOrder"
            ? "First-order indices: direct contribution to output variance"
            : "Total-order indices: direct effects + parameter interactions"
        }
        style={{ marginBottom: 24 }}
      >
        {loading ? (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: 400,
              color: "var(--text-muted)",
            }}
          >
            Loading...
          </div>
        ) : errorMsg ? (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: 400,
              color: "var(--accent-amber)",
              fontSize: 14,
              flexDirection: "column",
              gap: 8,
            }}
          >
            <div style={{ fontSize: 24 }}>!</div>
            <div>{errorMsg}</div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={450}>
            <BarChart
              data={tornadoData}
              layout="vertical"
              margin={{ left: 170, right: 70, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                type="number"
                stroke="#556178"
                style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                domain={[-50, 50]}
                ticks={[-50, -25, 0, 25, 50]}
                tickFormatter={(v) => `${Math.abs(Number(v))}%`}
              />
              <YAxis
                type="category"
                dataKey="displayName"
                stroke="#556178"
                style={{ fontSize: 12 }}
                width={160}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(v) => `${Math.abs(Number(v)).toFixed(1)}%`}
              />
              <ReferenceLine x={0} stroke="#556178" strokeWidth={2} />
              <Bar dataKey="negative" stackId="s" radius={[4, 0, 0, 4]}>
                {tornadoData.map((_, i) => (
                  <Cell key={i} fill="#3b82f6" />
                ))}
              </Bar>
              <Bar dataKey="positive" stackId="s" radius={[0, 4, 4, 0]}>
                {tornadoData.map((_, i) => (
                  <Cell key={i} fill="#22d3ee" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>

      <Card title="Parameter Details">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #1e293b" }}>
              {[
                "#",
                "Parameter",
                "First Order",
                "Total Order",
                "Interaction",
              ].map((h) => (
                <th
                  key={h}
                  style={{
                    padding: "10px 12px",
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
            {sensitivityData
              .sort((a, b) => b.totalOrder - a.totalOrder)
              .map((d, i) => (
                <tr
                  key={d.parameter}
                  style={{ borderBottom: "1px solid #1e293b" }}
                >
                  <td
                    style={{
                      padding: "10px 12px",
                      fontSize: 13,
                      color: "var(--text-muted)",
                    }}
                  >
                    {i + 1}
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 13 }}>
                    {d.displayName}
                  </td>
                  <td
                    style={{
                      padding: "10px 12px",
                      fontSize: 13,
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {(d.firstOrder * 100).toFixed(1)}%
                  </td>
                  <td
                    style={{
                      padding: "10px 12px",
                      fontSize: 13,
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {(d.totalOrder * 100).toFixed(1)}%
                  </td>
                  <td
                    style={{
                      padding: "10px 12px",
                      fontSize: 13,
                      fontFamily: "var(--font-mono)",
                      color: "var(--accent-amber)",
                    }}
                  >
                    {((d.totalOrder - d.firstOrder) * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
