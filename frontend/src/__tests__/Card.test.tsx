import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Card from "../components/Card";

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Hello World</Card>);
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("renders title and subtitle", () => {
    render(
      <Card title="Test Title" subtitle="Test Sub">
        Content
      </Card>,
    );
    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Test Sub")).toBeInTheDocument();
  });

  it("renders actions", () => {
    render(
      <Card title="T" actions={<button>Action</button>}>
        Content
      </Card>,
    );
    expect(screen.getByText("Action")).toBeInTheDocument();
  });
});
