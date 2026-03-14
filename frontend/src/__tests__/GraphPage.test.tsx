import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { BrowserRouter } from "react-router-dom";
import GraphPage from "../pages/GraphPage";

// ReactFlow needs ResizeObserver
beforeAll(() => {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

// Mock fetch — reject so we get demo data
globalThis.fetch = vi.fn(() =>
  Promise.reject(new Error("No API")),
) as unknown as typeof fetch;

function renderPage() {
  return render(
    <BrowserRouter>
      <GraphPage />
    </BrowserRouter>,
  );
}

describe("GraphPage", () => {
  it("renders causal graph title", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Causal Graph")).toBeInTheDocument();
    });
  });

  it("renders node count", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/nodes/)).toBeInTheDocument();
    });
  });

  it("renders highlight button", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Highlight Causal Path")).toBeInTheDocument();
    });
  });
});
