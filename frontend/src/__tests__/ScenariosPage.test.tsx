import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import ScenariosPage from "../pages/ScenariosPage";

// Mock fetch — reject so we get demo mode
globalThis.fetch = vi.fn(() =>
  Promise.reject(new Error("No API")),
) as unknown as typeof fetch;

function renderPage() {
  return render(
    <BrowserRouter>
      <ScenariosPage />
    </BrowserRouter>,
  );
}

describe("ScenariosPage", () => {
  it("renders scenario list header", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Scenarios")).toBeInTheDocument();
    });
  });

  it("renders new scenario button", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("+ New Scenario")).toBeInTheDocument();
    });
  });

  it("shows demo mode indicator when API unavailable", async () => {
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText("Demo Mode: API unavailable"),
      ).toBeInTheDocument();
    });
  });
});
