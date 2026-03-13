import { useState, useEffect } from "react";
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

interface DashboardMetrics {
  fleetSize: number;
  annualGHG: number;
  bevShare: number;
  simulationStatus: string;
}

interface TrajectoryPoint {
  year: number;
  ghg: number;
  p5: number;
  p25: number;
  p75: number;
  p95: number;
}

interface FleetCompositionPoint {
  year: number;
  ICEV: number;
  HEV: number;
  PHEV: number;
  BEV: number;
}

const DEMO_METRICS: DashboardMetrics = {
  fleetSize: 285000000,
  annualGHG: 1542.3,
  bevShare: 12.8,
  simulationStatus: "healthy",
};

const generateDemoTrajectory = (): TrajectoryPoint[] => {
  const data: TrajectoryPoint[] = [];
  for (let i = 0; i <= 10; i++) {
    const year = 2024 + i;
    const ghg = 1500 - i * 45;
    data.push({
      year,
      ghg,
      p5: ghg - 80,
      p25: ghg - 40,
      p75: ghg + 40,
      p95: ghg + 80,
    });
  }
  return data;
};

const generateDemoFleetComposition = (): FleetCompositionPoint[] => {
  const data: FleetCompositionPoint[] = [];
  for (let i = 0; i <= 10; i++) {
    const year = 2024 + i;
    const bevGrowth = i * 3.5;
    const phevGrowth = i * 2.2;
    const hevGrowth = i * 1.8;
    data.push({
      year,
      BEV: 8 + bevGrowth,
      PHEV: 4 + phevGrowth,
      HEV: 12 + hevGrowth,
      ICEV: 76 - bevGrowth - phevGrowth - hevGrowth,
    });
  }
  return data;
};

export default function DashboardPage() {
  const [metrics] = useState<DashboardMetrics>(DEMO_METRICS);
  const [trajectoryData] = useState<TrajectoryPoint[]>(
    generateDemoTrajectory(),
  );
  const [fleetComposition] = useState<FleetCompositionPoint[]>(
    generateDemoFleetComposition(),
  );
  const [apiHealthy, setApiHealthy] = useState(false);

  useEffect(() => {
    api
      .health()
      .then((h) => setApiHealthy(h.status === "ok"))
      .catch(() => setApiHealthy(false));
  }, []);

  const formatNumber = (num: number): string => {
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
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
            {apiHealthy ? "API Connected" : "Demo Mode"}
          </span>
        </div>
      </div>

      {/* Metric Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 20,
          marginBottom: 24,
        }}
      >
        {[
          {
            label: "Total Fleet Size",
            value: formatNumber(metrics.fleetSize),
            sub: "vehicles",
          },
          {
            label: "Annual GHG",
            value: metrics.annualGHG.toFixed(1),
            sub: "Mt CO2e",
          },
          {
            label: "BEV Share",
            value: `${metrics.bevShare.toFixed(1)}%`,
            sub: "of total fleet",
          },
          {
            label: "Status",
            value: metrics.simulationStatus,
            sub: "simulation engine",
            color: "var(--accent-green)",
          },
        ].map((m) => (
          <Card key={m.label}>
            <div
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                marginBottom: 10,
              }}
            >
              {m.label}
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 32,
                fontWeight: 700,
                color: m.color ?? "var(--text-primary)",
                marginBottom: 4,
              }}
            >
              {m.value}
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
              {m.sub}
            </div>
          </Card>
        ))}
      </div>

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
          title="GHG Emissions Trajectory"
          subtitle="10-year projection with confidence bands"
        >
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={trajectoryData}>
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
              <Area
                type="monotone"
                dataKey="p95"
                stroke="none"
                fill="#22d3ee"
                fillOpacity={0.08}
              />
              <Area
                type="monotone"
                dataKey="p75"
                stroke="none"
                fill="#22d3ee"
                fillOpacity={0.15}
              />
              <Area
                type="monotone"
                dataKey="ghg"
                stroke="#22d3ee"
                strokeWidth={2}
                fill="#22d3ee"
                fillOpacity={0.05}
              />
              <Area
                type="monotone"
                dataKey="p25"
                stroke="none"
                fill="transparent"
              />
              <Area
                type="monotone"
                dataKey="p5"
                stroke="none"
                fill="transparent"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Fleet Composition" subtitle="Powertrain share evolution">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={fleetComposition}>
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
              <Legend wrapperStyle={{ fontSize: 12, color: "#8b95a8" }} />
              <Area
                type="monotone"
                dataKey="BEV"
                stackId="1"
                stroke="#34d399"
                fill="#34d399"
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="PHEV"
                stackId="1"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="HEV"
                stackId="1"
                stroke="#fbbf24"
                fill="#fbbf24"
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="ICEV"
                stackId="1"
                stroke="#f87171"
                fill="#f87171"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Quick Actions">
        <div style={{ display: "flex", gap: 12 }}>
          <Button variant="primary">Run Simulation</Button>
          <Button>Compare Scenarios</Button>
          <Button>Sensitivity Analysis</Button>
          <Button>Export Report</Button>
        </div>
      </Card>
    </div>
  );
}
