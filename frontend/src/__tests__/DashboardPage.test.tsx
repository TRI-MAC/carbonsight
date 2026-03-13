import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import DashboardPage from "../pages/DashboardPage";

// Mock fetch — reject so we get demo fallback
globalThis.fetch = vi.fn(() =>
  Promise.reject(new Error("No API")),
) as unknown as typeof fetch;

function renderPage() {
  return render(
    <BrowserRouter>
      <DashboardPage />
    </BrowserRouter>,
  );
}

describe("DashboardPage", () => {
  it("renders metric cards after loading", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Total Fleet Size")).toBeInTheDocument();
      expect(screen.getByText(/Annual GHG/)).toBeInTheDocument();
      expect(screen.getByText("BEV Share")).toBeInTheDocument();
      expect(screen.getByText("Total VMT")).toBeInTheDocument();
    });
  });

  it("renders chart sections", async () => {
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText("GHG Emissions by Component"),
      ).toBeInTheDocument();
      expect(screen.getByText("Fleet Composition")).toBeInTheDocument();
    });
  });

  it("renders quick action buttons", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Run Simulation")).toBeInTheDocument();
      expect(screen.getByText("Compare Scenarios")).toBeInTheDocument();
      expect(screen.getByText("Explore Causal Graph")).toBeInTheDocument();
    });
  });

  it("falls back to Demo Mode when API is down", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Demo Mode")).toBeInTheDocument();
    });
  });
});
