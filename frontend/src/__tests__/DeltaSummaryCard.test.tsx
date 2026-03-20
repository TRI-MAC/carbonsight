import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import DeltaSummaryCard from "../components/DeltaSummaryCard";

const years = [2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033];
const baselineValues = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118];
const interventionValues = [100, 101, 101, 100, 99, 97, 95, 93, 91, 89];

describe("DeltaSummaryCard", () => {
  it("renders metric name and delta values", () => {
    render(
      <DeltaSummaryCard
        metric="Total GHG"
        baselineValues={baselineValues}
        interventionValues={interventionValues}
        years={years}
      />,
    );
    expect(screen.getByText("Total GHG")).toBeInTheDocument();
    // Final delta: 89 - 118 = -29
    expect(screen.getByText(/\-29\.00/)).toBeInTheDocument();
  });

  it("shows green color and down arrow for reduction", () => {
    const { container } = render(
      <DeltaSummaryCard
        metric="Total GHG"
        baselineValues={baselineValues}
        interventionValues={interventionValues}
        years={years}
      />,
    );
    // Down arrow for reduction
    expect(container.textContent).toContain("\u2193");
  });

  it("shows red color and up arrow for increase", () => {
    const { container } = render(
      <DeltaSummaryCard
        metric="Production"
        baselineValues={interventionValues}
        interventionValues={baselineValues}
        years={years}
      />,
    );
    // Up arrow for increase
    expect(container.textContent).toContain("\u2191");
  });

  it("renders sparkline container (recharts ResponsiveContainer)", () => {
    const { container } = render(
      <DeltaSummaryCard
        metric="Total GHG"
        baselineValues={baselineValues}
        interventionValues={interventionValues}
        years={years}
      />,
    );
    // ResponsiveContainer renders a wrapper div even when SVG can't size in jsdom
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("expands and collapses on click", () => {
    render(
      <DeltaSummaryCard
        metric="Total GHG"
        baselineValues={baselineValues}
        interventionValues={interventionValues}
        years={years}
      />,
    );
    // Detail table not visible initially
    expect(screen.queryByText("Baseline")).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByText("Baseline")).toBeInTheDocument();
    expect(screen.getByText("Intervention")).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(screen.getByRole("button"));
    expect(screen.queryByText("Baseline")).not.toBeInTheDocument();
  });

  it("supports controlled accordion via expanded/onToggle", () => {
    const onToggle = vi.fn();
    render(
      <DeltaSummaryCard
        metric="Total GHG"
        baselineValues={baselineValues}
        interventionValues={interventionValues}
        years={years}
        expanded={true}
        onToggle={onToggle}
      />,
    );
    // Table visible when expanded=true
    expect(screen.getByText("Baseline")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button"));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });
});
