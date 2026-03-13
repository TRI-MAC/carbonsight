import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api/client";
import Card from "../components/Card";
import Button from "../components/Button";

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

export default function DashboardPage() {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [trajectory, setTrajectory] = useState<TrajectoryPoint[]>([]);
  const [composition, setComposition] = useState<CompositionPoint[]>([]);
  const [apiHealthy, setApiHealthy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [simTime, setSimTime] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .getDashboard()
      .then((data) => {
        setMetrics(data.metrics);
        setTrajectory(data.trajectory);
        setComposition(data.composition);
        setSimTime(data.wall_clock_seconds);
        setApiHealthy(true);
      })
      .catch(() => {
        setApiHealthy(false);
        // Demo fallback
        setMetrics({
          fleet_size: 285000000,
          annual_ghg: 1176,
          bev_share: 1.9,
          bev_share_final: 1.9,
          total_vmt: 2.85e12,
        });
        const demoTraj: TrajectoryPoint[] = [];
        const demoComp: CompositionPoint[] = [];
        for (let i = 0; i < 10; i++) {
          demoTraj.push({
            year: 2024 + i,
            ghg: 1176 - i * 2,
            production: 73,
            usage: 1062 - i * 2,
            disposal: 41,
          });
          demoComp.push({
            year: 2024 + i,
            ICEV: 94 - i * 0.5,
            HEV: 3.4,
            PHEV: 0.6,
            BEV: 1.9 + i * 0.5,
          });
        }
        setTrajectory(demoTraj);
        setComposition(demoComp);
      })
      .finally(() => setLoading(false));
  }, []);

  const fmt = (num: number): string => {
    if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
    return num.toFixed(0);
  };

  const tooltipStyle = {
    backgroundColor: "#1f2a3f",
    border: "1px solid #1e293b",
    borderRadius: "8px",
    color: "#e8ecf4",
  };

  return (
    <div style={{ padding: 32, minHeight: "100vh" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 32,
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 48,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              marginBottom: 4,
            }}
          >
            Carbon<span style={{ color: "var(--accent-cyan)" }}>Sight</span>
          </h1>
          <p style={{ fontSize: 18, color: "var(--text-secondary)" }}>
            Fleet Carbon Observatory
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: apiHealthy
                ? "var(--accent-green)"
                : "var(--accent-red)",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 13,
              color: "var(--text-secondary)",
            }}
          >
            {loading ? "Loading..." : apiHealthy ? "Live Data" : "Demo Mode"}
          </span>
          {simTime !== null && (
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                color: "var(--text-muted)",
                marginLeft: 8,
              }}
            >
              sim: {simTime.toFixed(2)}s
            </span>
          )}
        </div>
      </div>

      {/* Metric Cards */}
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
              Mt CO2e (production + usage + disposal)
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
          subtitle="10-year baseline trajectory (Mt CO2e)"
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
          <Button onClick={() => navigate("/compare")}>
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
    </div>
  );
}
