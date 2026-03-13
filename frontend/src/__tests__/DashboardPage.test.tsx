import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import DashboardPage from "../pages/DashboardPage";

// Mock fetch for API calls
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
  it("renders metric cards", () => {
    renderPage();
    expect(screen.getByText("Total Fleet Size")).toBeInTheDocument();
    expect(screen.getByText("Annual GHG")).toBeInTheDocument();
    expect(screen.getByText("BEV Share")).toBeInTheDocument();
  });

  it("renders GHG trajectory chart section", () => {
    renderPage();
    expect(screen.getByText("GHG Emissions Trajectory")).toBeInTheDocument();
  });

  it("renders fleet composition chart section", () => {
    renderPage();
    expect(screen.getByText("Fleet Composition")).toBeInTheDocument();
  });

  it("renders quick actions", () => {
    renderPage();
    expect(screen.getByText("Run Simulation")).toBeInTheDocument();
    expect(screen.getByText("Compare Scenarios")).toBeInTheDocument();
  });

  it("shows Demo Mode when API is down", () => {
    renderPage();
    expect(screen.getByText("Demo Mode")).toBeInTheDocument();
  });
});
