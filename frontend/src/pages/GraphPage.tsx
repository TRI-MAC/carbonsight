import { useEffect, useState, useCallback, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
} from "reactflow";
import type { Node, Edge } from "reactflow";
import dagre from "@dagrejs/dagre";
import "reactflow/dist/style.css";
import { api } from "../api/client";
import type { GraphNode, TraceResponse } from "../types";
import NodeTraceChart from "../components/NodeTraceChart";
import type { Trace } from "../components/NodeTraceChart";

// Demo data for offline/fallback mode
const DEMO_NODES: GraphNode[] = [
  {
    name: "fleet_inventory",
    type: "input",
    is_input: true,
    upstream: [],
    temporal: [],
    tags: ["fleet"],
    display_name: "Fleet Inventory",
    description:
      "Initial US light-duty vehicle stock (~280M vehicles) by powertrain, age, and VMT bucket.",
    data_source: {
      name: "IEA Global EV Outlook 2024",
      publication_date: "2024-04-15",
      url: "https://www.iea.org/reports/global-ev-outlook-2024",
    },
    assumptions: [
      {
        description: "Current fleet composition by vehicle type and age",
        rationale:
          "IEA provides the most comprehensive global vehicle stock data",
        confidence: "high",
      },
    ],
  },
  {
    name: "survival_curves",
    type: "input",
    is_input: true,
    upstream: [],
    temporal: [],
    tags: ["fleet"],
    display_name: "Survival Curves",
    description:
      "Age-based probability of a vehicle remaining in service. From Greene & Leard survival model.",
    data_source: {
      name: "EPA Vehicle Survival Rates",
      publication_date: "2023-11-01",
      url: "https://www.epa.gov/",
    },
    assumptions: [
      {
        description: "Weibull distribution parameters for vehicle lifetime",
        rationale: "EPA survival curves based on historical registration data",
        confidence: "medium",
      },
    ],
  },
  {
    name: "oil_price",
    type: "input",
    is_input: true,
    upstream: [],
    temporal: [],
    tags: ["macro"],
    display_name: "Oil Price",
    description: "Crude oil price projection from EIA Short-Term Energy Outlook.",
    data_source: {
      name: "EIA Short-Term Energy Outlook",
      publication_date: "2024-01-10",
    },
  },
  {
    name: "grid_intensity",
    type: "input",
    is_input: true,
    upstream: [],
    temporal: [],
    tags: ["emissions", "macro"],
    display_name: "Grid Carbon Intensity",
    description:
      "CO2 emitted per kWh of electricity from the grid.",
    data_source: {
      name: "IEA World Energy Outlook 2024",
      publication_date: "2024-10-24",
    },
  },
  {
    name: "aged_fleet",
    type: "compute",
    is_input: false,
    upstream: ["fleet_inventory"],
    temporal: ["aged_fleet"],
    tags: ["fleet"],
    display_name: "Aged Fleet",
    description:
      "All vehicles aged by one year. Reads prior year's **Fleet Inventory** and increments each vehicle's age.",
  },
  {
    name: "post_scrappage",
    type: "compute",
    is_input: false,
    upstream: ["aged_fleet", "survival_curves"],
    temporal: [],
    tags: ["fleet"],
    display_name: "Surviving Fleet",
    description:
      "Vehicles remaining after age-based retirement. Applies **Survival Curves** to the **Aged Fleet** to probabilistically remove end-of-life vehicles.",
    assumptions: [
      {
        description: "Scrappage applied uniformly across vehicle types",
        rationale: "Simplification for computational efficiency",
        confidence: "medium",
      },
    ],
  },
  {
    name: "new_vehicles",
    type: "input",
    is_input: true,
    upstream: [],
    temporal: [],
    tags: ["fleet"],
    display_name: "New Vehicle Sales",
    description:
      "New vehicles entering the fleet this year by powertrain type.",
    data_source: {
      name: "BloombergNEF EV Forecast",
      publication_date: "2024-06-12",
    },
  },
  {
    name: "fleet_snapshot",
    type: "compute",
    is_input: false,
    upstream: ["post_scrappage", "new_vehicles"],
    temporal: [],
    tags: ["fleet"],
    display_name: "Fleet Composition",
    description:
      "Annual summary of fleet size, powertrain shares, and average age. Computed from **Surviving Fleet** and **New Vehicle Sales**.",
  },
  {
    name: "production_emissions",
    type: "compute",
    is_input: false,
    upstream: ["new_vehicles", "grid_intensity"],
    temporal: [],
    tags: ["emissions"],
    display_name: "Manufacturing Emissions",
    description:
      "Total emissions from producing this year's vehicles. Combines **New Vehicle Sales** with **Grid Carbon Intensity**.",
  },
  {
    name: "usage_emissions",
    type: "compute",
    is_input: false,
    upstream: ["fleet_snapshot", "oil_price", "grid_intensity"],
    temporal: [],
    tags: ["emissions"],
    display_name: "Driving Emissions",
    description:
      "Emissions from all vehicles on the road this year. Applies **Oil Price** and **Grid Carbon Intensity** to **Fleet Composition**.",
  },
  {
    name: "disposal_emissions",
    type: "compute",
    is_input: false,
    upstream: ["post_scrappage"],
    temporal: [],
    tags: ["emissions"],
    display_name: "End-of-Life Emissions",
    description:
      "Emissions from vehicles leaving the fleet this year, derived from **Surviving Fleet** scrappage data.",
  },
  {
    name: "total_emissions",
    type: "compute",
    is_input: false,
    upstream: ["production_emissions", "usage_emissions", "disposal_emissions"],
    temporal: [],
    tags: ["emissions"],
    display_name: "Total Emissions",
    description:
      "Sum of all lifecycle emissions: **Manufacturing Emissions** + **Driving Emissions** + **End-of-Life Emissions**.",
  },
];

// Dagre layout algorithm
const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction = "TB",
) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, ranksep: 80, nodesep: 60 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 200, height: 80 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 100,
        y: nodeWithPosition.y - 40,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

// Get node styling based on type and tags
const getNodeStyle = (graphNode: GraphNode) => {
  let borderColor = "var(--accent-blue)";
  let backgroundColor = "var(--bg-surface)";

  if (graphNode.is_input) {
    borderColor = "var(--accent-cyan)";
  }

  // Apply tag-based tint
  if (graphNode.tags.includes("fleet")) {
    backgroundColor = "rgba(52, 211, 153, 0.1)"; // green tint
  } else if (graphNode.tags.includes("emissions")) {
    backgroundColor = "rgba(251, 191, 36, 0.1)"; // amber tint
  } else if (graphNode.tags.includes("macro")) {
    backgroundColor = "rgba(167, 139, 250, 0.1)"; // violet tint
  }

  return {
    background: backgroundColor,
    border: `2px solid ${borderColor}`,
    borderRadius: "8px",
    padding: "12px 16px",
    color: "var(--text-primary)",
    fontSize: "13px",
    fontWeight: "500",
    minWidth: "180px",
  };
};

export default function GraphPage() {
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [highlightMode, setHighlightMode] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Trace state
  const [scenarioNames, setScenarioNames] = useState<string[]>([]);
  const [selectedTraceScenarios, setSelectedTraceScenarios] = useState<
    string[]
  >([]);
  const [traceResponses, setTraceResponses] = useState<
    Record<string, TraceResponse>
  >({});
  const [traceField, setTraceField] = useState<string | null>(null);
  const [traceLoading, setTraceLoading] = useState(false);
  const [traceError, setTraceError] = useState<string | null>(null);

  // Fetch nodes from API
  useEffect(() => {
    const fetchNodes = async () => {
      try {
        setLoading(true);
        const data = await api.listNodes();
        setGraphNodes(data);
        setError(null);
      } catch (err) {
        console.warn("Failed to fetch nodes from API, using demo data:", err);
        setGraphNodes(DEMO_NODES);
        setError("Using demo data (API unavailable)");
      } finally {
        setLoading(false);
      }
    };

    fetchNodes();
  }, []);

  // Build ReactFlow nodes and edges
  useEffect(() => {
    if (graphNodes.length === 0) return;

    const flowNodes: Node[] = graphNodes.map((gn) => ({
      id: gn.name,
      type: "default",
      data: {
        label: (
          <div style={{ textAlign: "center" }}>
            <div style={{ fontWeight: "600", marginBottom: "2px" }}>
              {gn.display_name ?? gn.name}
            </div>
            <div
              style={{
                fontSize: "10px",
                color: "var(--text-muted)",
                fontFamily: "var(--font-mono)",
                marginBottom: "4px",
              }}
            >
              {gn.name}
            </div>
            <div
              style={{
                fontSize: "11px",
                color: "var(--text-secondary)",
                textTransform: "uppercase",
              }}
            >
              {gn.is_input ? "input" : "compute"}
            </div>
          </div>
        ),
        graphNode: gn,
      },
      position: { x: 0, y: 0 },
      style: getNodeStyle(gn),
    }));

    const flowEdges: Edge[] = [];
    graphNodes.forEach((gn) => {
      gn.upstream.forEach((upstreamName) => {
        flowEdges.push({
          id: `${upstreamName}-${gn.name}`,
          source: upstreamName,
          target: gn.name,
          type: "smoothstep",
          animated: false,
          style: { stroke: "var(--border-subtle)", strokeWidth: 2 },
        });
      });
    });

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      flowNodes,
      flowEdges,
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [graphNodes, setNodes, setEdges]);

  // Calculate ancestors and descendants for highlight mode
  const { ancestors, descendants } = useMemo(() => {
    if (!selectedNode || !highlightMode) {
      return { ancestors: new Set<string>(), descendants: new Set<string>() };
    }

    const ancestorSet = new Set<string>();
    const descendantSet = new Set<string>();

    const nodeMap = new Map(graphNodes.map((n) => [n.name, n]));

    // Find all ancestors (upstream recursively)
    const findAncestors = (nodeName: string) => {
      const node = nodeMap.get(nodeName);
      if (!node) return;
      node.upstream.forEach((upstreamName) => {
        if (!ancestorSet.has(upstreamName)) {
          ancestorSet.add(upstreamName);
          findAncestors(upstreamName);
        }
      });
    };

    // Find all descendants (downstream recursively)
    const findDescendants = (nodeName: string) => {
      graphNodes.forEach((gn) => {
        if (gn.upstream.includes(nodeName) && !descendantSet.has(gn.name)) {
          descendantSet.add(gn.name);
          findDescendants(gn.name);
        }
      });
    };

    findAncestors(selectedNode.name);
    findDescendants(selectedNode.name);

    return { ancestors: ancestorSet, descendants: descendantSet };
  }, [selectedNode, highlightMode, graphNodes]);

  // Update node styles for highlight mode
  useEffect(() => {
    if (!highlightMode || !selectedNode) {
      // Reset to normal styles
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          style: {
            ...getNodeStyle(node.data.graphNode),
            opacity: 1,
          },
        })),
      );
      setEdges((eds) =>
        eds.map((edge) => ({
          ...edge,
          animated: false,
          style: { stroke: "var(--border-subtle)", strokeWidth: 2 },
        })),
      );
      return;
    }

    // Apply highlight styles
    setNodes((nds) =>
      nds.map((node) => {
        const isSelected = node.id === selectedNode.name;
        const isAncestor = ancestors.has(node.id);
        const isDescendant = descendants.has(node.id);
        const isInPath = isSelected || isAncestor || isDescendant;

        return {
          ...node,
          style: {
            ...getNodeStyle(node.data.graphNode),
            opacity: isInPath ? 1 : 0.25,
            boxShadow: isSelected ? "0 0 0 3px var(--accent-cyan)" : undefined,
          },
        };
      }),
    );

    setEdges((eds) =>
      eds.map((edge) => {
        const isInPath =
          (edge.source === selectedNode.name ||
            ancestors.has(edge.source) ||
            descendants.has(edge.source)) &&
          (edge.target === selectedNode.name ||
            ancestors.has(edge.target) ||
            descendants.has(edge.target));

        return {
          ...edge,
          animated: isInPath,
          style: {
            stroke: isInPath ? "var(--accent-cyan)" : "var(--border-subtle)",
            strokeWidth: isInPath ? 3 : 2,
            opacity: isInPath ? 1 : 0.25,
          },
        };
      }),
    );
  }, [highlightMode, selectedNode, ancestors, descendants, setNodes, setEdges]);

  // Fetch scenario names for trace selector
  useEffect(() => {
    api
      .listScenarios()
      .then((list) => setScenarioNames(list.map((s) => s.name)))
      .catch(() => setScenarioNames([]));
  }, []);

  // Fetch traces when selected node or scenarios change
  useEffect(() => {
    if (!selectedNode || selectedTraceScenarios.length === 0) {
      setTraceResponses({});
      setTraceError(null);
      return;
    }
    setTraceLoading(true);
    setTraceError(null);
    setTraceField(null);

    Promise.all(
      selectedTraceScenarios.map((scenario) =>
        api
          .getTrace(scenario, selectedNode.name)
          .then((resp) => ({ scenario, resp }))
          .catch(() => ({ scenario, resp: null })),
      ),
    ).then((results) => {
      const responses: Record<string, TraceResponse> = {};
      let anySuccess = false;
      for (const { scenario, resp } of results) {
        if (resp) {
          responses[scenario] = resp;
          anySuccess = true;
        }
      }
      setTraceResponses(responses);
      if (!anySuccess && selectedTraceScenarios.length > 0) {
        setTraceError("Run a scenario to see value traces");
      }
      setTraceLoading(false);
    });
  }, [selectedNode, selectedTraceScenarios]);

  // Derive trace data for chart
  const traceFields = useMemo(() => {
    const first = Object.values(traceResponses)[0];
    return first?.fields ?? null;
  }, [traceResponses]);

  const traces: Trace[] = useMemo(() => {
    return Object.entries(traceResponses).map(([scenario, resp]) => {
      let values = resp.values;
      if (resp.fields && resp.field_values) {
        const field = traceField ?? resp.fields[0];
        values = resp.field_values[field] ?? resp.values;
      }
      return { scenario, years: resp.years, values };
    });
  }, [traceResponses, traceField]);

  // Handle node click
  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node.data.graphNode);
    setSelectedTraceScenarios([]);
  }, []);

  // Get upstream and downstream node names for detail panel
  const getUpstreamNodes = (nodeName: string): string[] => {
    const node = graphNodes.find((n) => n.name === nodeName);
    return node?.upstream || [];
  };

  const getDownstreamNodes = (nodeName: string): string[] => {
    return graphNodes
      .filter((n) => n.upstream.includes(nodeName))
      .map((n) => n.name);
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading causal graph...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.graphContainer}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
          minZoom={0.1}
          maxZoom={2}
          defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
        >
          <Background color="var(--border-subtle)" gap={16} />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const gn = node.data.graphNode as GraphNode;
              return gn.is_input ? "#22d3ee" : "#3b82f6";
            }}
            maskColor="rgba(10, 14, 23, 0.8)"
            style={{
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
            }}
          />
          <Panel position="top-left" style={styles.panel}>
            <h1 style={styles.title}>Causal Graph</h1>
            {error && <div style={styles.error}>{error}</div>}
            <div style={styles.stats}>
              {graphNodes.length} nodes • {edges.length} edges
            </div>
          </Panel>
          <Panel position="top-right" style={styles.panel}>
            <button
              onClick={() => setHighlightMode(!highlightMode)}
              disabled={!selectedNode}
              style={{
                ...styles.button,
                ...(highlightMode ? styles.buttonActive : {}),
              }}
            >
              {highlightMode ? "Clear Highlight" : "Highlight Causal Path"}
            </button>
          </Panel>
        </ReactFlow>
      </div>

      {selectedNode && (
        <div style={styles.detailPanel}>
          <div style={styles.detailHeader}>
            <div style={{ flex: 1 }}>
              <h2 style={styles.detailTitle}>
                {selectedNode.display_name ?? selectedNode.name}
              </h2>
              <div
                style={{
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--text-muted)",
                  marginTop: "4px",
                }}
              >
                {selectedNode.name}
              </div>
            </div>
            <button
              onClick={() => {
                setSelectedNode(null);
                setHighlightMode(false);
              }}
              style={styles.closeButton}
            >
              ✕
            </button>
          </div>

          <div style={styles.detailSection}>
            <div style={styles.detailLabel}>Type</div>
            <div style={styles.detailValue}>
              <span
                style={{
                  ...styles.badge,
                  backgroundColor: selectedNode.is_input
                    ? "rgba(34, 211, 238, 0.2)"
                    : "rgba(59, 130, 246, 0.2)",
                  color: selectedNode.is_input
                    ? "var(--accent-cyan)"
                    : "var(--accent-blue)",
                }}
              >
                {selectedNode.is_input ? "INPUT" : "COMPUTE"}
              </span>
            </div>
          </div>

          {selectedNode.tags.length > 0 && (
            <div style={styles.detailSection}>
              <div style={styles.detailLabel}>Tags</div>
              <div style={styles.tagContainer}>
                {selectedNode.tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      ...styles.badge,
                      backgroundColor:
                        tag === "fleet"
                          ? "rgba(52, 211, 153, 0.2)"
                          : tag === "emissions"
                            ? "rgba(251, 191, 36, 0.2)"
                            : tag === "macro"
                              ? "rgba(167, 139, 250, 0.2)"
                              : "rgba(139, 149, 168, 0.2)",
                      color:
                        tag === "fleet"
                          ? "var(--accent-green)"
                          : tag === "emissions"
                            ? "var(--accent-amber)"
                            : tag === "macro"
                              ? "var(--accent-violet)"
                              : "var(--text-secondary)",
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {selectedNode.description && (
            <div style={styles.detailSection}>
              <div style={styles.detailLabel}>Description</div>
              <div
                style={{ fontSize: "13px", lineHeight: "1.6" }}
                dangerouslySetInnerHTML={{
                  __html: selectedNode.description.replace(
                    /\*\*(.+?)\*\*/g,
                    '<strong style="color: var(--accent-cyan)">$1</strong>',
                  ),
                }}
              />
            </div>
          )}

          {selectedNode.data_source && (
            <div style={styles.detailSection}>
              <div style={styles.detailLabel}>Data Source</div>
              <div style={styles.detailValue}>
                {selectedNode.data_source.url ? (
                  <a
                    href={selectedNode.data_source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={styles.link}
                  >
                    {selectedNode.data_source.name}
                  </a>
                ) : (
                  selectedNode.data_source.name
                )}
                {selectedNode.data_source.publication_date && (
                  <div style={styles.subtext}>
                    Published: {selectedNode.data_source.publication_date}
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedNode.assumptions && selectedNode.assumptions.length > 0 && (
            <div style={styles.detailSection}>
              <div style={styles.detailLabel}>Assumptions</div>
              {selectedNode.assumptions.map((assumption, idx) => (
                <div key={idx} style={styles.assumption}>
                  <div style={styles.assumptionDesc}>
                    {assumption.description}
                  </div>
                  <div style={styles.subtext}>{assumption.rationale}</div>
                  <div style={styles.subtext}>
                    Confidence:{" "}
                    <span
                      style={{
                        color:
                          assumption.confidence === "high"
                            ? "var(--accent-green)"
                            : assumption.confidence === "medium"
                              ? "var(--accent-amber)"
                              : "var(--text-secondary)",
                        fontWeight: "500",
                      }}
                    >
                      {assumption.confidence}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={styles.detailSection}>
            <div style={styles.detailLabel}>
              Upstream Connections ({getUpstreamNodes(selectedNode.name).length}
              )
            </div>
            {getUpstreamNodes(selectedNode.name).length > 0 ? (
              <div style={styles.connectionList}>
                {getUpstreamNodes(selectedNode.name).map((name) => (
                  <div key={name} style={styles.connectionItem}>
                    {name}
                  </div>
                ))}
              </div>
            ) : (
              <div style={styles.subtext}>No upstream dependencies</div>
            )}
          </div>

          <div style={styles.detailSection}>
            <div style={styles.detailLabel}>
              Downstream Connections (
              {getDownstreamNodes(selectedNode.name).length})
            </div>
            {getDownstreamNodes(selectedNode.name).length > 0 ? (
              <div style={styles.connectionList}>
                {getDownstreamNodes(selectedNode.name).map((name) => (
                  <div key={name} style={styles.connectionItem}>
                    {name}
                  </div>
                ))}
              </div>
            ) : (
              <div style={styles.subtext}>No downstream dependents</div>
            )}
          </div>

          {/* Value Trace */}
          <div style={styles.detailSection}>
            <div style={styles.detailLabel}>Value Trace</div>
            {scenarioNames.length === 0 ? (
              <div style={styles.subtext}>
                Run a scenario to see value traces
              </div>
            ) : (
              <>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                    marginBottom: 12,
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--text-muted)",
                      marginBottom: 4,
                    }}
                  >
                    Select scenarios:
                  </div>
                  {scenarioNames.map((name) => (
                    <label
                      key={name}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        fontSize: 12,
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={selectedTraceScenarios.includes(name)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTraceScenarios((prev) => [
                              ...prev,
                              name,
                            ]);
                          } else {
                            setSelectedTraceScenarios((prev) =>
                              prev.filter((n) => n !== name),
                            );
                          }
                        }}
                      />
                      {name}
                    </label>
                  ))}
                </div>
                {traceFields && (
                  <div style={{ marginBottom: 12 }}>
                    <select
                      value={traceField ?? traceFields[0] ?? ""}
                      onChange={(e) => setTraceField(e.target.value)}
                      style={{
                        padding: "4px 8px",
                        background: "var(--bg-elevated)",
                        border: "1px solid var(--border-subtle)",
                        borderRadius: "var(--radius-sm)",
                        color: "var(--text-primary)",
                        fontSize: 12,
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {traceFields.map((f) => (
                        <option key={f} value={f}>
                          {f}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                {traceLoading ? (
                  <div style={styles.subtext}>Loading traces...</div>
                ) : traceError ? (
                  <div style={styles.subtext}>{traceError}</div>
                ) : traces.length > 0 ? (
                  <NodeTraceChart
                    traces={traces}
                    nodeName={selectedNode.name}
                    fieldName={
                      traceFields ? (traceField ?? traceFields[0]) : undefined
                    }
                  />
                ) : selectedTraceScenarios.length > 0 ? (
                  <div style={styles.subtext}>
                    No trace data for selected scenarios
                  </div>
                ) : null}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Inline styles using CSS variables
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    height: "100vh",
    backgroundColor: "var(--bg-primary)",
    color: "var(--text-primary)",
  },
  graphContainer: {
    flex: 1,
    position: "relative",
  },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    fontSize: "18px",
    color: "var(--text-secondary)",
  },
  panel: {
    backgroundColor: "var(--bg-surface)",
    padding: "16px",
    borderRadius: "8px",
    border: "1px solid var(--border-subtle)",
  },
  title: {
    margin: 0,
    fontSize: "20px",
    fontWeight: "600",
    marginBottom: "8px",
  },
  stats: {
    fontSize: "13px",
    color: "var(--text-secondary)",
  },
  error: {
    fontSize: "12px",
    color: "var(--accent-amber)",
    marginTop: "4px",
    marginBottom: "8px",
  },
  button: {
    backgroundColor: "var(--bg-elevated)",
    color: "var(--text-primary)",
    border: "1px solid var(--border-subtle)",
    borderRadius: "6px",
    padding: "10px 16px",
    fontSize: "14px",
    fontWeight: "500",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  buttonActive: {
    backgroundColor: "var(--accent-cyan)",
    color: "var(--bg-primary)",
    borderColor: "var(--accent-cyan)",
  },
  detailPanel: {
    width: "380px",
    backgroundColor: "var(--bg-surface)",
    borderLeft: "1px solid var(--border-subtle)",
    overflowY: "auto",
    padding: "24px",
  },
  detailHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "24px",
  },
  detailTitle: {
    margin: 0,
    fontSize: "20px",
    fontWeight: "600",
    flex: 1,
    wordBreak: "break-word",
  },
  closeButton: {
    backgroundColor: "transparent",
    border: "none",
    color: "var(--text-secondary)",
    fontSize: "20px",
    cursor: "pointer",
    padding: "0 0 0 12px",
    lineHeight: "1",
  },
  detailSection: {
    marginBottom: "24px",
  },
  detailLabel: {
    fontSize: "12px",
    fontWeight: "600",
    textTransform: "uppercase",
    color: "var(--text-secondary)",
    marginBottom: "8px",
    letterSpacing: "0.5px",
  },
  detailValue: {
    fontSize: "14px",
    lineHeight: "1.6",
  },
  badge: {
    display: "inline-block",
    padding: "4px 10px",
    borderRadius: "4px",
    fontSize: "11px",
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  tagContainer: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
  },
  link: {
    color: "var(--accent-cyan)",
    textDecoration: "none",
  },
  subtext: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    marginTop: "4px",
  },
  assumption: {
    backgroundColor: "var(--bg-elevated)",
    padding: "12px",
    borderRadius: "6px",
    marginBottom: "8px",
    border: "1px solid var(--border-subtle)",
  },
  assumptionDesc: {
    fontSize: "13px",
    lineHeight: "1.5",
    marginBottom: "4px",
  },
  connectionList: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  connectionItem: {
    backgroundColor: "var(--bg-elevated)",
    padding: "8px 12px",
    borderRadius: "4px",
    fontSize: "13px",
    border: "1px solid var(--border-subtle)",
  },
};
