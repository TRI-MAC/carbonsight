import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import NodeTraceChart from "../components/NodeTraceChart";

describe("NodeTraceChart", () => {
  it("renders empty state when no traces", () => {
    render(<NodeTraceChart traces={[]} nodeName="test_node" />);
    expect(screen.getByText("No trace data available")).toBeInTheDocument();
  });

  it("renders node name label", () => {
    render(
      <NodeTraceChart
        traces={[
          { scenario: "Baseline", years: [2024, 2025], values: [10, 20] },
        ]}
        nodeName="fleet_snapshot"
      />,
    );
    expect(screen.getByText("fleet_snapshot")).toBeInTheDocument();
  });

  it("renders field name when provided", () => {
    render(
      <NodeTraceChart
        traces={[
          { scenario: "Baseline", years: [2024, 2025], values: [10, 20] },
        ]}
        nodeName="total_emissions"
        fieldName="total_ghg"
      />,
    );
    expect(screen.getByText("total_emissions")).toBeInTheDocument();
    expect(screen.getByText(/total_ghg/)).toBeInTheDocument();
  });
});
