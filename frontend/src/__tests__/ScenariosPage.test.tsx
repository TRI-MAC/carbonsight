import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import ScenariosPage from "../pages/ScenariosPage";

// Mock recharts to avoid canvas/SVG issues in tests
vi.mock("recharts", () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => null,
  AreaChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="area-chart">{children}</div>
  ),
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  ReferenceArea: () => null,
}));

const MOCK_CATALOG = [
  {
    type: "carbon_pricing",
    category: "emissions",
    description: "Carbon pricing on gasoline",
    target_node: "gas_ghg_per_gallon",
    params: [
      { name: "price_per_tonne", type: "float", default: 50, min: 0, max: 200 },
      { name: "start_year", type: "int", default: 2025, min: 2024, max: 2034 },
    ],
  },
  {
    type: "ev_subsidy",
    category: "fleet_dynamics",
    description: "EV purchase subsidy",
    target_node: "powertrain_proportions",
    params: [
      {
        name: "proportion_shift",
        type: "dict",
        default: { bev: 0.15 },
        min: 0,
        max: 0.5,
      },
    ],
  },
];

const MOCK_SCENARIOS = [
  { name: "baseline", overrides: {}, metadata: {}, interventions: [] },
  { name: "test-scenario", overrides: {}, metadata: {}, interventions: [] },
];

function mockApiSuccess() {
  globalThis.fetch = vi.fn((url: string) => {
    if (typeof url === "string" && url.includes("/scenarios")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(MOCK_SCENARIOS),
      });
    }
    if (typeof url === "string" && url.includes("/interventions")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(MOCK_CATALOG),
      });
    }
    if (typeof url === "string" && url.includes("/nodes")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  }) as unknown as typeof fetch;
}

function mockApiFailure() {
  globalThis.fetch = vi.fn(() =>
    Promise.reject(new Error("No API")),
  ) as unknown as typeof fetch;
}

function renderPage() {
  return render(
    <BrowserRouter>
      <ScenariosPage />
    </BrowserRouter>,
  );
}

describe("ScenariosPage", () => {
  it("renders three-column layout with scenario list header", async () => {
    mockApiSuccess();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Scenarios")).toBeInTheDocument();
    });
  });

  it("renders new scenario button", async () => {
    mockApiSuccess();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("+ New Scenario")).toBeInTheDocument();
    });
  });

  it("shows demo mode indicator when API unavailable", async () => {
    mockApiFailure();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Demo Mode")).toBeInTheDocument();
    });
  });

  it("shows placeholder when no scenario selected", async () => {
    mockApiSuccess();
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText("Select a scenario or create a new one"),
      ).toBeInTheDocument();
    });
  });

  it("shows baseline informational message in preview", async () => {
    mockApiSuccess();
    renderPage();
    // The default scenarioName is empty which maps to "baseline" in ImpactPreview
    await waitFor(() => {
      expect(screen.getByText(/baseline scenario/i)).toBeInTheDocument();
    });
  });

  it("shows accordion categories when scenario is active", async () => {
    mockApiSuccess();
    renderPage();
    // Click "+ New Scenario" to activate the center column
    await waitFor(() => {
      expect(screen.getByText("+ New Scenario")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("+ New Scenario"));

    await waitFor(() => {
      expect(screen.getByText("Interventions")).toBeInTheDocument();
      // Category headers (formatted from catalog categories)
      expect(screen.getByText("Emissions")).toBeInTheDocument();
      expect(screen.getByText("Fleet/Dynamics")).toBeInTheDocument();
    });
  });

  it("expanding category shows intervention checkboxes", async () => {
    mockApiSuccess();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("+ New Scenario")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("+ New Scenario"));

    await waitFor(() => {
      expect(screen.getByText("Emissions")).toBeInTheDocument();
    });

    // Expand the Emissions category
    fireEvent.click(screen.getByText("Emissions"));

    await waitFor(() => {
      expect(
        screen.getByText("Carbon pricing on gasoline"),
      ).toBeInTheDocument();
    });
  });

  it("toggling intervention shows slider controls", async () => {
    mockApiSuccess();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("+ New Scenario")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("+ New Scenario"));

    await waitFor(() => {
      expect(screen.getByText("Emissions")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Emissions"));

    await waitFor(() => {
      expect(
        screen.getByText("Carbon pricing on gasoline"),
      ).toBeInTheDocument();
    });

    // Click on the intervention to toggle it
    fireEvent.click(screen.getByText("Carbon pricing on gasoline"));

    await waitFor(() => {
      // Should show param labels
      expect(screen.getByText("Carbon Price ($/tonne)")).toBeInTheDocument();
      expect(screen.getByText("Start Year")).toBeInTheDocument();
    });
  });

  it("displays scenario list from API", async () => {
    mockApiSuccess();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("baseline")).toBeInTheDocument();
      expect(screen.getByText("test-scenario")).toBeInTheDocument();
    });
  });
});
