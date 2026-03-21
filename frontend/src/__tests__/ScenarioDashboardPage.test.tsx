import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import ScenarioDashboardPage from "../pages/ScenarioDashboardPage";

const mockScenarios = [
  { name: "baseline", description: "", overrides: {}, metadata: {} },
  {
    name: "ev-grid-intervention",
    description: "",
    overrides: {},
    metadata: {},
  },
];

const mockDashboard = {
  metrics: {
    fleet_size: 280000000,
    annual_ghg: 1270.8,
    bev_share: 2.0,
    bev_share_final: 5.5,
    total_vmt: 2.85e12,
  },
  trajectory: [
    { year: 2024, ghg: 1270, production: 73, usage: 1150, disposal: 47 },
    { year: 2025, ghg: 1260, production: 74, usage: 1140, disposal: 46 },
  ],
  composition: [
    { year: 2024, ICEV: 93.9, HEV: 3.4, PHEV: 0.6, BEV: 2.0 },
    { year: 2025, ICEV: 93.4, HEV: 3.4, PHEV: 0.6, BEV: 2.5 },
  ],
  wall_clock_seconds: 1.5,
};

const mockTraceEmissions = (scenario: string) => ({
  scenario,
  node: "total_emissions",
  years: [2024, 2025, 2026],
  values: scenario === "baseline" ? [100e9, 102e9, 104e9] : [100e9, 99e9, 97e9],
  fields: [
    "total_ghg",
    "usage_ghg_gas",
    "usage_ghg_electric",
    "production_ghg",
  ],
  field_values: {
    total_ghg:
      scenario === "baseline" ? [100e9, 102e9, 104e9] : [100e9, 99e9, 97e9],
    usage_ghg_gas:
      scenario === "baseline" ? [50e9, 51e9, 52e9] : [50e9, 49e9, 48e9],
    usage_ghg_electric:
      scenario === "baseline" ? [30e9, 31e9, 32e9] : [30e9, 30e9, 29e9],
    production_ghg:
      scenario === "baseline" ? [20e9, 20e9, 20e9] : [20e9, 20e9, 20e9],
  },
});

const mockTraceGrid = (scenario: string) => ({
  scenario,
  node: "grid_ghg_per_kwh",
  years: [2024, 2025, 2026],
  values: scenario === "baseline" ? [0.4, 0.39, 0.38] : [0.4, 0.36, 0.32],
  fields: null,
  field_values: null,
});

const mockCompare = {
  baseline: "baseline",
  comparisons: { "ev-grid-intervention": { deltas: [] } },
};

beforeEach(() => {
  vi.restoreAllMocks();
  globalThis.fetch = vi.fn((url: string | URL | Request) => {
    const u = typeof url === "string" ? url : url.toString();
    if (u.endsWith("/dashboard")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDashboard),
      });
    }
    if (
      u.includes("/scenarios") &&
      !u.includes("/trace") &&
      !u.includes("/compare")
    ) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockScenarios),
      });
    }
    if (u.includes("/trace/total_emissions")) {
      const scenario = u.includes("baseline")
        ? "baseline"
        : "ev-grid-intervention";
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockTraceEmissions(scenario)),
      });
    }
    if (u.includes("/trace/grid_ghg_per_kwh")) {
      const scenario = u.includes("baseline")
        ? "baseline"
        : "ev-grid-intervention";
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockTraceGrid(scenario)),
      });
    }
    if (u.includes("/compare")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockCompare),
      });
    }
    return Promise.reject(new Error("Unknown endpoint"));
  }) as unknown as typeof fetch;
});

function renderPage() {
  return render(
    <BrowserRouter>
      <ScenarioDashboardPage />
    </BrowserRouter>,
  );
}

describe("ScenarioDashboardPage", () => {
  it("renders Overview tab with headline metrics by default", async () => {
    renderPage();
    await waitFor(
      () => {
        expect(screen.getByText("Scenario Dashboard")).toBeInTheDocument();
        expect(screen.getByText("Total Fleet Size")).toBeInTheDocument();
        expect(screen.getByText("Annual GHG (Year 1)")).toBeInTheDocument();
        expect(screen.getByText("BEV Share")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("shows Overview and Compare tabs", () => {
    renderPage();
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Compare")).toBeInTheDocument();
  });

  it("switches to Compare tab on click", async () => {
    renderPage();
    fireEvent.click(screen.getByText("Compare"));
    await waitFor(() => {
      expect(screen.getByText("Compare Against")).toBeInTheDocument();
    });
  });

  it("does not show the old flat delta table", async () => {
    renderPage();
    fireEvent.click(screen.getByText("Compare"));
    await waitFor(() => {
      expect(screen.getByText("Compare Against")).toBeInTheDocument();
    });
    expect(screen.queryByText("Delta Breakdown")).not.toBeInTheDocument();
  });
});
