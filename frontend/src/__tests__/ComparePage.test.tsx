import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import ComparePage from "../pages/ComparePage";

const mockScenarios = [
  { name: "baseline", description: "", overrides: {}, metadata: {} },
  {
    name: "ev-grid-intervention",
    description: "",
    overrides: {},
    metadata: {},
  },
];

const mockTraceEmissions = (scenario: string) => ({
  scenario,
  node: "total_emissions",
  years: [2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033],
  values:
    scenario === "baseline"
      ? [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
      : [100, 101, 101, 100, 99, 97, 95, 93, 91, 89],
  fields: [
    "total_ghg",
    "usage_ghg_gas",
    "usage_ghg_electric",
    "production_ghg",
  ],
  field_values: {
    total_ghg:
      scenario === "baseline"
        ? [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
        : [100, 101, 101, 100, 99, 97, 95, 93, 91, 89],
    usage_ghg_gas:
      scenario === "baseline"
        ? [50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
        : [50, 50, 49, 48, 47, 46, 45, 44, 43, 42],
    usage_ghg_electric:
      scenario === "baseline"
        ? [30, 31, 32, 33, 34, 35, 36, 37, 38, 39]
        : [30, 31, 32, 32, 32, 31, 30, 29, 28, 27],
    production_ghg:
      scenario === "baseline"
        ? [20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
        : [20, 20, 20, 20, 20, 20, 20, 20, 20, 20],
  },
});

const mockTraceGrid = (scenario: string) => ({
  scenario,
  node: "grid_ghg_per_kwh",
  years: [2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033],
  values:
    scenario === "baseline"
      ? [0.4, 0.39, 0.38, 0.37, 0.36, 0.35, 0.34, 0.33, 0.32, 0.31]
      : [0.4, 0.38, 0.36, 0.34, 0.32, 0.3, 0.28, 0.26, 0.24, 0.22],
  fields: null,
  field_values: null,
});

const mockCompare = {
  baseline: "baseline",
  comparisons: {
    "ev-grid-intervention": {
      deltas: [],
    },
  },
};

beforeEach(() => {
  vi.restoreAllMocks();
  globalThis.fetch = vi.fn((url: string | URL | Request) => {
    const u = typeof url === "string" ? url : url.toString();
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
      <ComparePage />
    </BrowserRouter>,
  );
}

describe("ComparePage", () => {
  it("renders summary cards after auto-comparison", async () => {
    renderPage();
    await waitFor(
      () => {
        expect(screen.getByText("Total GHG")).toBeInTheDocument();
        expect(screen.getByText("Gas Usage Emissions")).toBeInTheDocument();
        expect(
          screen.getByText("Electric Usage Emissions"),
        ).toBeInTheDocument();
        expect(screen.getByText("Production Emissions")).toBeInTheDocument();
        expect(screen.getByText("Grid Carbon Intensity")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("does not render the flat delta table", async () => {
    renderPage();
    await waitFor(
      () => {
        expect(screen.getByText("Total GHG")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(screen.queryByText("Delta Breakdown")).not.toBeInTheDocument();
  });
});
