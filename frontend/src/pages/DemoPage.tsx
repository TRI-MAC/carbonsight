import { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
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

type DemoData = Awaited<ReturnType<typeof api.getDemo>>;

const FALLBACK_DATA: DemoData = {
  baseline: {
    trajectory: [
      {
        year: 2024,
        ghg: 1270.8,
        production: 86.8,
        usage: 1142.3,
        disposal: 41.7,
      },
      {
        year: 2025,
        ghg: 1261.7,
        production: 86.2,
        usage: 1133.9,
        disposal: 41.6,
      },
      {
        year: 2026,
        ghg: 1253.5,
        production: 85.7,
        usage: 1126.3,
        disposal: 41.5,
      },
      {
        year: 2027,
        ghg: 1246.3,
        production: 85.2,
        usage: 1119.7,
        disposal: 41.4,
      },
      {
        year: 2028,
        ghg: 1239.9,
        production: 84.8,
        usage: 1113.8,
        disposal: 41.3,
      },
      {
        year: 2029,
        ghg: 1234.4,
        production: 84.4,
        usage: 1108.7,
        disposal: 41.3,
      },
      {
        year: 2030,
        ghg: 1229.7,
        production: 84.1,
        usage: 1104.4,
        disposal: 41.2,
      },
      {
        year: 2031,
        ghg: 1225.7,
        production: 83.8,
        usage: 1100.8,
        disposal: 41.1,
      },
      {
        year: 2032,
        ghg: 1222.4,
        production: 83.6,
        usage: 1097.8,
        disposal: 41.0,
      },
      {
        year: 2033,
        ghg: 1219.7,
        production: 83.4,
        usage: 1095.4,
        disposal: 40.9,
      },
    ],
    composition: [
      {
        year: 2024,
        total_vehicles: 280921221,
        ICEV: 93.94,
        HEV: 3.41,
        PHEV: 0.64,
        BEV: 2.01,
      },
      {
        year: 2025,
        total_vehicles: 281837796,
        ICEV: 93.42,
        HEV: 3.56,
        PHEV: 0.69,
        BEV: 2.33,
      },
      {
        year: 2026,
        total_vehicles: 282748794,
        ICEV: 92.9,
        HEV: 3.71,
        PHEV: 0.74,
        BEV: 2.65,
      },
      {
        year: 2027,
        total_vehicles: 283653098,
        ICEV: 92.39,
        HEV: 3.86,
        PHEV: 0.79,
        BEV: 2.96,
      },
      {
        year: 2028,
        total_vehicles: 284549376,
        ICEV: 91.89,
        HEV: 4.0,
        PHEV: 0.84,
        BEV: 3.27,
      },
      {
        year: 2029,
        total_vehicles: 285436034,
        ICEV: 91.4,
        HEV: 4.13,
        PHEV: 0.89,
        BEV: 3.58,
      },
      {
        year: 2030,
        total_vehicles: 286311184,
        ICEV: 90.92,
        HEV: 4.26,
        PHEV: 0.94,
        BEV: 3.88,
      },
      {
        year: 2031,
        total_vehicles: 287172589,
        ICEV: 90.45,
        HEV: 4.38,
        PHEV: 0.98,
        BEV: 4.19,
      },
      {
        year: 2032,
        total_vehicles: 288017630,
        ICEV: 89.99,
        HEV: 4.5,
        PHEV: 1.02,
        BEV: 4.49,
      },
      {
        year: 2033,
        total_vehicles: 288843257,
        ICEV: 89.54,
        HEV: 4.61,
        PHEV: 1.06,
        BEV: 4.79,
      },
    ],
  },
  intervention: {
    trajectory: [
      {
        year: 2024,
        ghg: 1270.8,
        production: 86.8,
        usage: 1142.3,
        disposal: 41.7,
      },
      {
        year: 2025,
        ghg: 1250.2,
        production: 87.1,
        usage: 1121.5,
        disposal: 41.6,
      },
      {
        year: 2026,
        ghg: 1230.5,
        production: 87.3,
        usage: 1101.7,
        disposal: 41.5,
      },
      {
        year: 2027,
        ghg: 1212.1,
        production: 87.5,
        usage: 1083.2,
        disposal: 41.4,
      },
      {
        year: 2028,
        ghg: 1194.8,
        production: 87.6,
        usage: 1065.9,
        disposal: 41.3,
      },
      {
        year: 2029,
        ghg: 1178.8,
        production: 87.7,
        usage: 1049.8,
        disposal: 41.3,
      },
      {
        year: 2030,
        ghg: 1163.9,
        production: 87.8,
        usage: 1034.9,
        disposal: 41.2,
      },
      {
        year: 2031,
        ghg: 1150.2,
        production: 87.8,
        usage: 1021.3,
        disposal: 41.1,
      },
      {
        year: 2032,
        ghg: 1137.6,
        production: 87.8,
        usage: 1008.8,
        disposal: 41.0,
      },
      {
        year: 2033,
        ghg: 1126.1,
        production: 87.8,
        usage: 997.4,
        disposal: 40.9,
      },
    ],
    composition: [
      {
        year: 2024,
        total_vehicles: 280921221,
        ICEV: 93.94,
        HEV: 3.41,
        PHEV: 0.64,
        BEV: 2.01,
      },
      {
        year: 2025,
        total_vehicles: 281837796,
        ICEV: 92.42,
        HEV: 3.56,
        PHEV: 0.69,
        BEV: 3.33,
      },
      {
        year: 2026,
        total_vehicles: 282748794,
        ICEV: 90.93,
        HEV: 3.71,
        PHEV: 0.74,
        BEV: 4.62,
      },
      {
        year: 2027,
        total_vehicles: 283653098,
        ICEV: 89.47,
        HEV: 3.86,
        PHEV: 0.79,
        BEV: 5.88,
      },
      {
        year: 2028,
        total_vehicles: 284549376,
        ICEV: 88.05,
        HEV: 4.0,
        PHEV: 0.84,
        BEV: 7.11,
      },
      {
        year: 2029,
        total_vehicles: 285436034,
        ICEV: 86.66,
        HEV: 4.13,
        PHEV: 0.89,
        BEV: 8.32,
      },
      {
        year: 2030,
        total_vehicles: 286311184,
        ICEV: 85.31,
        HEV: 4.26,
        PHEV: 0.94,
        BEV: 9.49,
      },
      {
        year: 2031,
        total_vehicles: 287172589,
        ICEV: 84.0,
        HEV: 4.38,
        PHEV: 0.98,
        BEV: 10.64,
      },
      {
        year: 2032,
        total_vehicles: 288017630,
        ICEV: 82.72,
        HEV: 4.5,
        PHEV: 1.02,
        BEV: 11.76,
      },
      {
        year: 2033,
        total_vehicles: 288843257,
        ICEV: 81.48,
        HEV: 4.61,
        PHEV: 1.06,
        BEV: 12.85,
      },
    ],
  },
  deltas: [
    {
      year: 2024,
      baseline_ghg: 1270.8,
      intervention_ghg: 1270.8,
      absolute_delta: 0,
      percentage_delta: 0,
    },
    {
      year: 2025,
      baseline_ghg: 1261.7,
      intervention_ghg: 1250.2,
      absolute_delta: -11.5,
      percentage_delta: -0.91,
    },
    {
      year: 2026,
      baseline_ghg: 1253.5,
      intervention_ghg: 1230.5,
      absolute_delta: -23.0,
      percentage_delta: -1.84,
    },
    {
      year: 2027,
      baseline_ghg: 1246.3,
      intervention_ghg: 1212.1,
      absolute_delta: -34.2,
      percentage_delta: -2.74,
    },
    {
      year: 2028,
      baseline_ghg: 1239.9,
      intervention_ghg: 1194.8,
      absolute_delta: -45.1,
      percentage_delta: -3.64,
    },
    {
      year: 2029,
      baseline_ghg: 1234.4,
      intervention_ghg: 1178.8,
      absolute_delta: -55.6,
      percentage_delta: -4.5,
    },
    {
      year: 2030,
      baseline_ghg: 1229.7,
      intervention_ghg: 1163.9,
      absolute_delta: -65.8,
      percentage_delta: -5.35,
    },
    {
      year: 2031,
      baseline_ghg: 1225.7,
      intervention_ghg: 1150.2,
      absolute_delta: -75.5,
      percentage_delta: -6.16,
    },
    {
      year: 2032,
      baseline_ghg: 1222.4,
      intervention_ghg: 1137.6,
      absolute_delta: -84.8,
      percentage_delta: -6.94,
    },
    {
      year: 2033,
      baseline_ghg: 1219.7,
      intervention_ghg: 1126.1,
      absolute_delta: -93.6,
      percentage_delta: -7.67,
    },
  ],
  cumulative_avoided_mt: 489.1,
  intervention_description: {
    name: "EV Subsidy + Grid Decarbonization",
    components: [
      {
        type: "ev_subsidy",
        description: "15% BEV proportion shift in new vehicle sales",
      },
      {
        type: "grid_decarbonization",
        description: "Grid carbon intensity declining ~50% by 2033",
      },
    ],
  },
  wall_clock_seconds: 6.5,
};

const STEPS = [
  {
    title: "The US Fleet Today",
    subtitle: "280 million vehicles, 1.27 billion tonnes CO2e/year",
  },
  {
    title: "What If?",
    subtitle: "A combined EV + grid decarbonization scenario",
  },
  {
    title: "The Impact",
    subtitle: "Comparing baseline vs. intervention trajectories",
  },
  {
    title: "Why Trust This?",
    subtitle: "Validated data, traceable assumptions",
  },
];

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

export default function DemoPage() {
  const [step, setStep] = useState(-1); // -1 = intro
  const [data, setData] = useState<DemoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiHealthy, setApiHealthy] = useState(false);

  useEffect(() => {
    setLoading(true);
    api
      .getDemo()
      .then((d) => {
        setData(d);
        setApiHealthy(true);
      })
      .catch(() => {
        setData(FALLBACK_DATA);
        setApiHealthy(false);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div
        style={{
          padding: 32,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 32,
              marginBottom: 16,
            }}
          >
            Running simulations...
          </div>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 13,
              color: "var(--text-muted)",
            }}
          >
            Computing 10-year fleet trajectories for baseline + intervention
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const renderIntro = () => (
    <div
      style={{
        maxWidth: 700,
        margin: "0 auto",
        textAlign: "center",
        paddingTop: 80,
      }}
    >
      <h1
        style={{
          fontFamily: "var(--font-display)",
          fontSize: 56,
          fontWeight: 700,
          letterSpacing: "-0.03em",
          marginBottom: 8,
        }}
      >
        Carbon<span style={{ color: "var(--accent-cyan)" }}>Sight</span>
      </h1>
      <p
        style={{
          fontSize: 20,
          color: "var(--text-secondary)",
          marginBottom: 8,
          lineHeight: 1.5,
        }}
      >
        Counterfactual Carbon Impact Simulator
      </p>
      <p
        style={{
          fontSize: 15,
          color: "var(--text-muted)",
          marginBottom: 40,
          lineHeight: 1.6,
          maxWidth: 520,
          margin: "0 auto 40px",
        }}
      >
        CarbonSight models the US light-duty vehicle fleet over a 10-year
        horizon, tracing carbon from manufacturing through driving and disposal.
        Ask "what if" questions, see the impact, and understand why.
      </p>
      <Button variant="primary" onClick={() => setStep(0)}>
        Start Walkthrough
      </Button>
      <div
        style={{
          marginTop: 24,
          display: "flex",
          justifyContent: "center",
          gap: 8,
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: apiHealthy
              ? "var(--accent-green)"
              : "var(--accent-red)",
          }}
        />
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color: "var(--text-muted)",
          }}
        >
          {apiHealthy
            ? `Live data (${data.wall_clock_seconds.toFixed(1)}s)`
            : "Demo Mode"}
        </span>
      </div>
    </div>
  );

  const renderStep1 = () => (
    <div>
      <p
        style={{
          fontSize: 15,
          color: "var(--text-secondary)",
          lineHeight: 1.7,
          marginBottom: 24,
        }}
      >
        The US has approximately{" "}
        <strong style={{ color: "var(--text-primary)" }}>281 million</strong>{" "}
        light-duty vehicles producing over{" "}
        <strong style={{ color: "var(--text-primary)" }}>
          1.27 billion tonnes
        </strong>{" "}
        of CO2-equivalent emissions annually. Here's the 10-year baseline
        projection.
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 16,
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
              marginBottom: 8,
            }}
          >
            Fleet Size
          </div>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 28,
              fontWeight: 700,
            }}
          >
            {fmt(data.baseline.composition[0].total_vehicles)}
          </div>
        </Card>
        <Card>
          <div
            style={{
              fontSize: 11,
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              marginBottom: 8,
            }}
          >
            Annual GHG
          </div>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 28,
              fontWeight: 700,
            }}
          >
            {data.baseline.trajectory[0].ghg.toFixed(0)} Mt
          </div>
        </Card>
        <Card>
          <div
            style={{
              fontSize: 11,
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              marginBottom: 8,
            }}
          >
            BEV Share
          </div>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 28,
              fontWeight: 700,
              color: "var(--accent-green)",
            }}
          >
            {data.baseline.composition[0].BEV.toFixed(1)}%
          </div>
        </Card>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Card
          title="GHG Emissions Trajectory"
          subtitle="Baseline, by component (Mt CO2e)"
        >
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.baseline.trajectory}>
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
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.baseline.composition}>
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
    </div>
  );

  const renderStep2 = () => (
    <div>
      <p
        style={{
          fontSize: 15,
          color: "var(--text-secondary)",
          lineHeight: 1.7,
          marginBottom: 24,
        }}
      >
        CarbonSight lets you ask{" "}
        <strong style={{ color: "var(--accent-cyan)" }}>"what if"</strong>{" "}
        questions. Here we combine two interventions to see their joint carbon
        impact:
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 16,
          marginBottom: 24,
        }}
      >
        {data.intervention_description.components.map((c, i) => (
          <Card key={i}>
            <div
              style={{
                fontSize: 11,
                color: "var(--accent-cyan)",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                marginBottom: 8,
              }}
            >
              {c.type.replace(/_/g, " ")}
            </div>
            <div
              style={{
                fontSize: 15,
                color: "var(--text-primary)",
                lineHeight: 1.5,
              }}
            >
              {c.description}
            </div>
          </Card>
        ))}
      </div>
      <Card>
        <div
          style={{
            fontSize: 14,
            color: "var(--text-secondary)",
            lineHeight: 1.7,
          }}
        >
          <p style={{ marginBottom: 12 }}>
            <strong style={{ color: "var(--text-primary)" }}>
              Why these two together?
            </strong>
          </p>
          <p style={{ marginBottom: 12 }}>
            EV adoption alone has limited carbon impact if the electricity grid
            remains carbon-intensive. Conversely, a cleaner grid has limited
            impact if most vehicles still burn gasoline. The combination reveals
            the <em>interaction effect</em> — a key insight CarbonSight is
            designed to surface.
          </p>
          <p>
            This intervention shifts new vehicle sales toward 15% BEV share
            while simultaneously reducing grid carbon intensity by ~50% over the
            10-year horizon (from 369 to ~185 g CO2e/kWh).
          </p>
        </div>
      </Card>
    </div>
  );

  const comparisonData = data.deltas.map((d) => ({
    year: d.year,
    Baseline: d.baseline_ghg,
    Intervention: d.intervention_ghg,
  }));

  const renderStep3 = () => {
    const lastDelta = data.deltas[data.deltas.length - 1];
    return (
      <div>
        <p
          style={{
            fontSize: 15,
            color: "var(--text-secondary)",
            lineHeight: 1.7,
            marginBottom: 24,
          }}
        >
          The intervention reduces total fleet GHG by{" "}
          <strong style={{ color: "var(--accent-green)" }}>
            {Math.abs(lastDelta.percentage_delta).toFixed(1)}%
          </strong>{" "}
          by 2033, with{" "}
          <strong style={{ color: "var(--accent-green)" }}>
            {data.cumulative_avoided_mt.toFixed(0)} Mt
          </strong>{" "}
          cumulative emissions avoided over the decade.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 16,
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
                marginBottom: 8,
              }}
            >
              Final Year Reduction
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 28,
                fontWeight: 700,
                color: "var(--accent-green)",
              }}
            >
              {Math.abs(lastDelta.absolute_delta).toFixed(0)} Mt
            </div>
          </Card>
          <Card>
            <div
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                marginBottom: 8,
              }}
            >
              Cumulative Avoided
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 28,
                fontWeight: 700,
                color: "var(--accent-green)",
              }}
            >
              {data.cumulative_avoided_mt.toFixed(0)} Mt
            </div>
          </Card>
          <Card>
            <div
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                marginBottom: 8,
              }}
            >
              BEV Share (2033)
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 28,
                fontWeight: 700,
                color: "var(--accent-cyan)",
              }}
            >
              {data.intervention.composition[
                data.intervention.composition.length - 1
              ].BEV.toFixed(1)}
              %
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
              vs{" "}
              {data.baseline.composition[
                data.baseline.composition.length - 1
              ].BEV.toFixed(1)}
              % baseline
            </div>
          </Card>
        </div>
        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}
        >
          <Card
            title="GHG Trajectory Comparison"
            subtitle="Baseline vs. Intervention (Mt CO2e)"
          >
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="year"
                  stroke="#556178"
                  style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                />
                <YAxis
                  stroke="#556178"
                  style={{ fontSize: 11, fontFamily: "JetBrains Mono" }}
                  domain={["auto", "auto"]}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(v) => `${Number(v).toFixed(1)} Mt`}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: "#8b95a8" }} />
                <Line
                  type="monotone"
                  dataKey="Baseline"
                  stroke="#f87171"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="Intervention"
                  stroke="#34d399"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
          <Card
            title="BEV Share Comparison"
            subtitle="Baseline vs. Intervention (% of fleet)"
          >
            <ResponsiveContainer width="100%" height={280}>
              <LineChart
                data={data.baseline.composition.map((b, i) => ({
                  year: b.year,
                  Baseline: b.BEV,
                  Intervention: data.intervention.composition[i].BEV,
                }))}
              >
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
                  formatter={(v) => `${Number(v).toFixed(1)}%`}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: "#8b95a8" }} />
                <Line
                  type="monotone"
                  dataKey="Baseline"
                  stroke="#f87171"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="Intervention"
                  stroke="#34d399"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </div>
      </div>
    );
  };

  const renderStep4 = () => (
    <div>
      <p
        style={{
          fontSize: 15,
          color: "var(--text-secondary)",
          lineHeight: 1.7,
          marginBottom: 24,
        }}
      >
        Every CarbonSight output is traceable to its data sources and
        assumptions. The model is validated against established industry
        references.
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <Card title="Validation Results">
          <table
            style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid var(--border-subtle)",
                  color: "var(--text-muted)",
                  fontSize: 11,
                  textTransform: "uppercase" as const,
                }}
              >
                <th style={{ textAlign: "left", padding: "8px 0" }}>Check</th>
                <th style={{ textAlign: "left", padding: "8px 0" }}>
                  Reference
                </th>
                <th style={{ textAlign: "center", padding: "8px 0" }}>
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                {
                  check: "ICEV Production Emissions",
                  ref: "GREET 2024",
                  status: "PASS",
                },
                {
                  check: "BEV Production Emissions",
                  ref: "GREET 2024",
                  status: "PASS",
                },
                {
                  check: "ICEV Annual Usage",
                  ref: "GREET 2024",
                  status: "PASS",
                },
                {
                  check: "BEV Annual Usage",
                  ref: "GREET 2024",
                  status: "PASS",
                },
                {
                  check: "Fleet Size Range",
                  ref: "VISION 2024",
                  status: "PASS",
                },
                {
                  check: "BEV Share Growth",
                  ref: "VISION 2024",
                  status: "PASS",
                },
              ].map((row, i) => (
                <tr
                  key={i}
                  style={{ borderBottom: "1px solid var(--border-subtle)" }}
                >
                  <td
                    style={{ padding: "8px 0", color: "var(--text-primary)" }}
                  >
                    {row.check}
                  </td>
                  <td
                    style={{ padding: "8px 0", color: "var(--text-secondary)" }}
                  >
                    {row.ref}
                  </td>
                  <td
                    style={{
                      padding: "8px 0",
                      textAlign: "center",
                      color: "var(--accent-green)",
                      fontFamily: "var(--font-mono)",
                      fontSize: 11,
                    }}
                  >
                    {row.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
        <Card title="Data Sources">
          <table
            style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid var(--border-subtle)",
                  color: "var(--text-muted)",
                  fontSize: 11,
                  textTransform: "uppercase" as const,
                }}
              >
                <th style={{ textAlign: "left", padding: "8px 0" }}>Source</th>
                <th style={{ textAlign: "left", padding: "8px 0" }}>
                  Used For
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                {
                  source: "Argonne GREET 2024",
                  use: "Lifecycle emission factors",
                },
                {
                  source: "Argonne VISION 2024",
                  use: "Fleet projection validation",
                },
                {
                  source: "EPA Standards MY2027+",
                  use: "Powertrain mix assumptions",
                },
                { source: "NHTS 2017", use: "VMT by vehicle age" },
                {
                  source: "Greene & Leard 2024",
                  use: "Vehicle survival curves",
                },
                { source: "EIA AEO 2024", use: "Energy price trajectories" },
              ].map((row, i) => (
                <tr
                  key={i}
                  style={{ borderBottom: "1px solid var(--border-subtle)" }}
                >
                  <td
                    style={{ padding: "8px 0", color: "var(--text-primary)" }}
                  >
                    {row.source}
                  </td>
                  <td
                    style={{ padding: "8px 0", color: "var(--text-secondary)" }}
                  >
                    {row.use}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
      <Card title="Key Assumptions">
        <div
          style={{
            fontSize: 13,
            color: "var(--text-secondary)",
            lineHeight: 1.7,
          }}
        >
          <ul style={{ paddingLeft: 20, margin: 0 }}>
            <li style={{ marginBottom: 8 }}>
              15.5M new vehicles sold annually (2019-2024 US average)
            </li>
            <li style={{ marginBottom: 8 }}>
              Vehicle survival follows Greene & Leard (2024) actuarial model
            </li>
            <li style={{ marginBottom: 8 }}>
              VMT by age from NHTS 2017 (historical patterns persist)
            </li>
            <li style={{ marginBottom: 8 }}>
              Production emissions: ICEV ~5,600 kg, BEV ~11,700 kg CO2e (GREET
              2024)
            </li>
            <li style={{ marginBottom: 8 }}>
              Grid carbon intensity: 369 g CO2e/kWh (2024 US average)
            </li>
            <li>US light-duty fleet only; 10-year horizon (2024-2034)</li>
          </ul>
        </div>
      </Card>
    </div>
  );

  const renderCurrentStep = () => {
    switch (step) {
      case -1:
        return renderIntro();
      case 0:
        return renderStep1();
      case 1:
        return renderStep2();
      case 2:
        return renderStep3();
      case 3:
        return renderStep4();
      default:
        return renderIntro();
    }
  };

  return (
    <div style={{ padding: 32, minHeight: "100vh" }}>
      {step >= 0 && (
        <>
          {/* Stepper */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 0,
              marginBottom: 32,
            }}
          >
            {STEPS.map((s, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  flex: i < STEPS.length - 1 ? 1 : "none",
                }}
              >
                <button
                  onClick={() => setStep(i)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    cursor: "pointer",
                    background: "none",
                    border: "none",
                    padding: 0,
                  }}
                >
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: "50%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontFamily: "var(--font-mono)",
                      fontSize: 12,
                      fontWeight: 600,
                      background:
                        i === step
                          ? "var(--accent-cyan)"
                          : i < step
                            ? "var(--accent-green)"
                            : "var(--bg-elevated)",
                      color:
                        i <= step ? "var(--bg-primary)" : "var(--text-muted)",
                      transition: "all 0.2s ease",
                    }}
                  >
                    {i < step ? "\u2713" : i + 1}
                  </div>
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: i === step ? 600 : 400,
                      color:
                        i === step
                          ? "var(--text-primary)"
                          : "var(--text-muted)",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {s.title}
                  </span>
                </button>
                {i < STEPS.length - 1 && (
                  <div
                    style={{
                      flex: 1,
                      height: 1,
                      margin: "0 12px",
                      background:
                        i < step
                          ? "var(--accent-green)"
                          : "var(--border-subtle)",
                    }}
                  />
                )}
              </div>
            ))}
            <div
              style={{
                marginLeft: "auto",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: apiHealthy
                    ? "var(--accent-green)"
                    : "var(--accent-red)",
                }}
              />
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  color: "var(--text-muted)",
                }}
              >
                {apiHealthy ? "Live" : "Demo"}
              </span>
            </div>
          </div>

          {/* Step title */}
          <div style={{ marginBottom: 24 }}>
            <h2
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 28,
                fontWeight: 700,
                marginBottom: 4,
              }}
            >
              {STEPS[step].title}
            </h2>
            <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
              {STEPS[step].subtitle}
            </p>
          </div>
        </>
      )}

      {/* Content */}
      {renderCurrentStep()}

      {/* Navigation */}
      {step >= 0 && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: 32,
          }}
        >
          <Button onClick={() => setStep(step === 0 ? -1 : step - 1)}>
            {step === 0 ? "Back to Intro" : "Previous"}
          </Button>
          {step < STEPS.length - 1 ? (
            <Button variant="primary" onClick={() => setStep(step + 1)}>
              Next
            </Button>
          ) : (
            <Button variant="primary" onClick={() => setStep(-1)}>
              Restart
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
