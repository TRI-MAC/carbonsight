import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../App";

describe("App", () => {
  it("renders the navigation with CarbonSight branding", () => {
    render(<App />);
    // Both nav and dashboard have "Carbon" + "Sight"
    const carbons = screen.getAllByText("Carbon");
    expect(carbons.length).toBeGreaterThanOrEqual(1);
  });

  it("renders nav links", () => {
    render(<App />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Causal Graph")).toBeInTheDocument();
    expect(screen.getByText("Scenarios")).toBeInTheDocument();
    expect(screen.getByText("Compare")).toBeInTheDocument();
    expect(screen.getByText("Sensitivity")).toBeInTheDocument();
  });

  it("renders dashboard page by default", () => {
    render(<App />);
    const observatories = screen.getAllByText("Fleet Carbon Observatory");
    expect(observatories.length).toBeGreaterThanOrEqual(1);
  });
});
