import { useMemo } from "react";
import type { GraphNode } from "../types";

interface Props {
  targetNode: string;
  graphNodes: GraphNode[];
}

function bfsPath(
  from: string,
  to: string,
  adjacency: Map<string, string[]>,
): string[] | null {
  const queue: string[][] = [[from]];
  const visited = new Set<string>([from]);
  while (queue.length > 0) {
    const path = queue.shift()!;
    const current = path[path.length - 1];
    if (current === to) return path;
    for (const neighbor of adjacency.get(current) ?? []) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push([...path, neighbor]);
      }
    }
  }
  return null;
}

export default function CausalPathChips({ targetNode, graphNodes }: Props) {
  const path = useMemo(() => {
    const downstream = new Map<string, string[]>();
    for (const node of graphNodes) {
      for (const up of node.upstream) {
        if (!downstream.has(up)) downstream.set(up, []);
        downstream.get(up)!.push(node.name);
      }
    }
    return bfsPath(targetNode, "total_emissions", downstream);
  }, [targetNode, graphNodes]);

  if (!path || path.length === 0) return null;

  const nameMap = new Map(
    graphNodes.map((n) => [n.name, n.display_name ?? n.name]),
  );

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: 2,
        marginTop: 4,
      }}
    >
      {path.map((node, i) => (
        <span
          key={node}
          style={{ display: "flex", alignItems: "center", gap: 2 }}
        >
          <span
            style={{
              fontSize: 10,
              padding: "1px 6px",
              borderRadius: 8,
              background: "var(--bg-elevated)",
              color: "var(--text-muted)",
              fontFamily: "var(--font-mono)",
              whiteSpace: "nowrap",
            }}
          >
            {nameMap.get(node) ?? node}
          </span>
          {i < path.length - 1 && (
            <span style={{ fontSize: 9, color: "var(--text-muted)" }}>
              &rarr;
            </span>
          )}
        </span>
      ))}
    </div>
  );
}
