import { useState, useEffect } from "react";
import Button from "../components/Button";
import CausalPathChips from "../components/CausalPathChips";
import ImpactPreview from "../components/ImpactPreview";
import { useAutoRun } from "../hooks/useAutoRun";
import { api } from "../api/client";
import type { ScenarioConfig, GraphNode } from "../types";

interface CatalogItem {
  type: string;
  category: string;
  description: string;
  target_node: string;
  params: Array<{
    name: string;
    type: string;
    default: unknown;
    min: number | null;
    max: number | null;
  }>;
}

interface ScenarioWithStatus extends ScenarioConfig {
  status?: "idle" | "running" | "completed" | "error";
  error?: string;
}

interface InterventionValues {
  [paramName: string]: number;
}

const PARAM_LABELS: Record<string, string> = {
  price_per_tonne: "Carbon Price ($/tonne)",
  start_year: "Start Year",
  proportion_shift: "BEV Purchase Shift",
  factor: "VMT Factor",
  trajectory: "Intensity Factor",
  age_threshold: "Age Threshold",
  acceleration_factor: "Acceleration Factor",
  duration_years: "Duration (Years)",
  charging_factor: "Charging Factor",
};

export default function ScenariosPage() {
  // Scenario list state
  const [scenarios, setScenarios] = useState<ScenarioWithStatus[]>([]);
  const [selectedScenario, setSelectedScenario] =
    useState<ScenarioWithStatus | null>(null);
  const [isNewScenario, setIsNewScenario] = useState(false);
  const [loading, setLoading] = useState(true);
  const [demoMode, setDemoMode] = useState(false);

  // Intervention state
  const [scenarioName, setScenarioName] = useState("");
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [enabledInterventions, setEnabledInterventions] = useState<
    Record<string, InterventionValues>
  >({});
  const [expandedCategories, setExpandedCategories] = useState<
    Record<string, boolean>
  >({});
  const [runMode, setRunMode] = useState<"deterministic" | "uq">(
    "deterministic",
  );

  // Auto-run
  const autoRun = useAutoRun(scenarioName);

  // Load scenarios, catalog, and graph on mount
  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [scenarioList, interventionCatalog, nodes] = await Promise.all([
        api.listScenarios(),
        api.listInterventions().catch(() => []),
        api.listNodes().catch(() => []),
      ]);
      setScenarios(
        scenarioList.map((s) => ({ ...s, status: "idle" as const })),
      );
      setCatalog(interventionCatalog as CatalogItem[]);
      setGraphNodes(nodes);
      setDemoMode(false);
    } catch {
      setDemoMode(true);
      setScenarios([]);
    } finally {
      setLoading(false);
    }
  }

  // Group catalog by category
  const categories = catalog.reduce(
    (acc, item) => {
      const cat = item.category
        .replace(/_/g, "/")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(item);
      return acc;
    },
    {} as Record<string, CatalogItem[]>,
  );

  function handleNewScenario() {
    setIsNewScenario(true);
    setSelectedScenario(null);
    setScenarioName("");
    setEnabledInterventions({});
  }

  function handleSelectScenario(scenario: ScenarioWithStatus) {
    setIsNewScenario(false);
    setSelectedScenario(scenario);
    setScenarioName(scenario.name);
    // TODO: parse existing overrides into enabledInterventions
    setEnabledInterventions({});
    // Trigger preview for existing scenarios
    if (scenario.name !== "baseline") {
      autoRun.trigger();
    }
  }

  async function handleDeleteScenario() {
    if (!selectedScenario) return;
    if (!confirm(`Delete scenario "${selectedScenario.name}"?`)) return;
    try {
      await api.deleteScenario(selectedScenario.name);
      await loadData();
      setSelectedScenario(null);
      setIsNewScenario(false);
    } catch {
      if (demoMode) {
        setScenarios((prev) =>
          prev.filter((s) => s.name !== selectedScenario.name),
        );
        setSelectedScenario(null);
      }
    }
  }

  function toggleIntervention(item: CatalogItem) {
    setEnabledInterventions((prev) => {
      if (prev[item.type]) {
        const copy = { ...prev };
        delete copy[item.type];
        return copy;
      }
      // Initialize with defaults
      const defaults: InterventionValues = {};
      for (const p of item.params) {
        if (typeof p.default === "number") {
          defaults[p.name] = p.default;
        } else if (
          p.type === "dict" &&
          p.default &&
          typeof p.default === "object"
        ) {
          // For dict types like proportion_shift: {bev: 0.15}, expose the first numeric value
          const vals = Object.values(p.default as Record<string, unknown>);
          defaults[p.name] = typeof vals[0] === "number" ? vals[0] : 0;
        } else {
          defaults[p.name] = 0;
        }
      }
      return { ...prev, [item.type]: defaults };
    });
    // Trigger auto-run after change
    setTimeout(() => autoRun.trigger(), 50);
  }

  function handleParamChange(
    interventionType: string,
    paramName: string,
    value: number,
  ) {
    setEnabledInterventions((prev) => ({
      ...prev,
      [interventionType]: {
        ...prev[interventionType],
        [paramName]: value,
      },
    }));
    autoRun.trigger();
  }

  async function handleSaveScenario() {
    if (!scenarioName.trim()) {
      alert("Please enter a scenario name");
      return;
    }

    const interventionSpecs = Object.entries(enabledInterventions).map(
      ([type, values]) => {
        const item = catalog.find((c) => c.type === type);
        const params: Record<string, unknown> = {};
        for (const p of item?.params ?? []) {
          if (p.type === "dict" && p.name === "proportion_shift") {
            params[p.name] = { bev: values[p.name] ?? 0 };
          } else {
            params[p.name] = values[p.name] ?? p.default;
          }
        }
        return { type, params };
      },
    );

    try {
      if (isNewScenario) {
        await api.createScenario({
          name: scenarioName,
          overrides: {},
          metadata: {},
          interventions: interventionSpecs,
        });
      } else {
        await api.updateScenario(scenarioName, {
          overrides: {},
          metadata: {},
          interventions: interventionSpecs,
        });
      }
      await loadData();
      setIsNewScenario(false);
    } catch (error) {
      if (!demoMode) alert(`Failed to save: ${error}`);
    }
  }

  async function handleRunScenario() {
    if (!scenarioName.trim()) return;
    await handleSaveScenario();
    try {
      setScenarios((prev) =>
        prev.map((s) =>
          s.name === scenarioName ? { ...s, status: "running" as const } : s,
        ),
      );
      await api.runScenario(scenarioName, {
        mode: runMode,
        num_years: 10,
        uq_samples: runMode === "uq" ? 1000 : undefined,
      });
      setScenarios((prev) =>
        prev.map((s) =>
          s.name === scenarioName ? { ...s, status: "completed" as const } : s,
        ),
      );
    } catch (error) {
      setScenarios((prev) =>
        prev.map((s) =>
          s.name === scenarioName
            ? { ...s, status: "error" as const, error: String(error) }
            : s,
        ),
      );
    }
  }

  const hasActiveScenario = isNewScenario || selectedScenario != null;

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        background: "var(--bg-primary)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-body)",
      }}
    >
      {/* Left Column: Scenario List */}
      <div
        style={{
          width: 200,
          borderRight: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          background: "var(--bg-surface)",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: 12,
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <h2
            style={{
              fontSize: 14,
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            Scenarios
          </h2>
          <Button
            variant="primary"
            onClick={handleNewScenario}
            style={{ width: "100%", fontSize: 12 }}
          >
            + New Scenario
          </Button>
          {demoMode && (
            <div
              style={{
                marginTop: 6,
                padding: "4px 8px",
                background: "rgba(251, 191, 36, 0.1)",
                border: "1px solid rgba(251, 191, 36, 0.3)",
                borderRadius: "var(--radius-md)",
                fontSize: 10,
                color: "#fbbf24",
              }}
            >
              Demo Mode
            </div>
          )}
        </div>
        <div style={{ flex: 1, overflow: "auto" }}>
          {loading ? (
            <div
              style={{
                padding: 12,
                color: "var(--text-muted)",
                fontSize: 12,
              }}
            >
              Loading...
            </div>
          ) : scenarios.length === 0 ? (
            <div
              style={{
                padding: 12,
                color: "var(--text-muted)",
                fontSize: 12,
              }}
            >
              No scenarios yet.
            </div>
          ) : (
            scenarios.map((scenario) => (
              <div
                key={scenario.name}
                onClick={() => handleSelectScenario(scenario)}
                style={{
                  padding: "10px 12px",
                  borderBottom: "1px solid var(--border-subtle)",
                  cursor: "pointer",
                  background:
                    selectedScenario?.name === scenario.name
                      ? "var(--bg-elevated)"
                      : "transparent",
                }}
                onMouseEnter={(e) => {
                  if (selectedScenario?.name !== scenario.name)
                    e.currentTarget.style.background = "var(--bg-hover)";
                }}
                onMouseLeave={(e) => {
                  if (selectedScenario?.name !== scenario.name)
                    e.currentTarget.style.background = "transparent";
                }}
              >
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 500,
                    marginBottom: 2,
                  }}
                >
                  {scenario.name}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color:
                      scenario.status === "completed"
                        ? "var(--accent-green)"
                        : scenario.status === "running"
                          ? "var(--accent-blue)"
                          : scenario.status === "error"
                            ? "var(--accent-red)"
                            : "var(--text-muted)",
                  }}
                >
                  {scenario.status === "running" && "Running..."}
                  {scenario.status === "completed" && "Completed"}
                  {scenario.status === "error" && "Error"}
                  {scenario.status === "idle" &&
                    `${Object.keys(scenario.overrides).length} overrides`}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Center Column: Intervention Controls */}
      <div
        style={{
          width: 380,
          borderRight: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
          overflow: "auto",
        }}
      >
        {!hasActiveScenario ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "var(--text-muted)",
              fontSize: 13,
              padding: 24,
            }}
          >
            Select a scenario or create a new one
          </div>
        ) : (
          <div
            style={{
              padding: 16,
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
          >
            {/* Scenario name */}
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: 11,
                  fontWeight: 500,
                  color: "var(--text-secondary)",
                  marginBottom: 4,
                }}
              >
                Scenario Name
              </label>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                disabled={!isNewScenario}
                placeholder="Enter scenario name"
                style={{
                  width: "100%",
                  padding: "6px 10px",
                  background: isNewScenario
                    ? "var(--bg-primary)"
                    : "var(--bg-elevated)",
                  border: "1px solid var(--border-default)",
                  borderRadius: "var(--radius-md)",
                  color: "var(--text-primary)",
                  fontSize: 13,
                  fontFamily: "var(--font-body)",
                  opacity: isNewScenario ? 1 : 0.6,
                  boxSizing: "border-box",
                }}
              />
            </div>

            {/* Intervention categories */}
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: 11,
                  fontWeight: 500,
                  color: "var(--text-secondary)",
                  marginBottom: 8,
                }}
              >
                Interventions
              </label>
              {Object.entries(categories).map(([catName, items]) => (
                <div
                  key={catName}
                  style={{
                    marginBottom: 8,
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    overflow: "hidden",
                  }}
                >
                  {/* Category header */}
                  <div
                    onClick={() =>
                      setExpandedCategories((prev) => ({
                        ...prev,
                        [catName]: !prev[catName],
                      }))
                    }
                    style={{
                      padding: "8px 12px",
                      background: "var(--bg-surface)",
                      cursor: "pointer",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      fontSize: 12,
                      fontWeight: 600,
                      color: "var(--text-primary)",
                    }}
                  >
                    {catName}
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                      {expandedCategories[catName] ? "\u25B2" : "\u25BC"}
                    </span>
                  </div>

                  {/* Category items */}
                  {expandedCategories[catName] && (
                    <div style={{ padding: "8px 12px" }}>
                      {items.map((item) => {
                        const isActive = !!enabledInterventions[item.type];
                        return (
                          <div
                            key={item.type}
                            style={{
                              marginBottom: 12,
                              padding: "8px 10px",
                              background: isActive
                                ? "var(--bg-elevated)"
                                : "var(--bg-primary)",
                              borderRadius: "var(--radius-md)",
                              border: isActive
                                ? "1px solid var(--accent-blue)"
                                : "1px solid var(--border-subtle)",
                            }}
                          >
                            {/* Checkbox + label */}
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 8,
                                cursor: "pointer",
                              }}
                              onClick={() => toggleIntervention(item)}
                            >
                              <input
                                type="checkbox"
                                checked={isActive}
                                readOnly
                                style={{ cursor: "pointer" }}
                              />
                              <span style={{ fontSize: 12, flex: 1 }}>
                                {item.description}
                              </span>
                            </div>

                            {/* Params */}
                            {isActive && (
                              <div style={{ marginTop: 8 }}>
                                {item.params.map((p) => {
                                  const val =
                                    enabledInterventions[item.type]?.[p.name] ??
                                    0;
                                  const hasRange =
                                    p.min != null && p.max != null;
                                  return (
                                    <div
                                      key={p.name}
                                      style={{ marginBottom: 6 }}
                                    >
                                      <div
                                        style={{
                                          fontSize: 10,
                                          color: "var(--text-muted)",
                                          marginBottom: 3,
                                        }}
                                      >
                                        {PARAM_LABELS[p.name] ?? p.name}
                                      </div>
                                      <div
                                        style={{
                                          display: "flex",
                                          alignItems: "center",
                                          gap: 8,
                                        }}
                                      >
                                        {hasRange && (
                                          <input
                                            type="range"
                                            min={p.min!}
                                            max={p.max!}
                                            step={
                                              p.type === "int"
                                                ? 1
                                                : (p.max! - p.min!) / 100
                                            }
                                            value={val}
                                            onChange={(e) =>
                                              handleParamChange(
                                                item.type,
                                                p.name,
                                                Number(e.target.value),
                                              )
                                            }
                                            style={{ flex: 1 }}
                                          />
                                        )}
                                        <input
                                          type="number"
                                          value={val}
                                          onChange={(e) =>
                                            handleParamChange(
                                              item.type,
                                              p.name,
                                              Number(e.target.value),
                                            )
                                          }
                                          min={p.min ?? undefined}
                                          max={p.max ?? undefined}
                                          step={p.type === "int" ? 1 : 0.01}
                                          style={{
                                            width: hasRange ? 70 : "100%",
                                            padding: "3px 6px",
                                            background: "var(--bg-primary)",
                                            border:
                                              "1px solid var(--border-default)",
                                            borderRadius: "var(--radius-md)",
                                            color: "var(--text-primary)",
                                            fontSize: 12,
                                            fontFamily: "var(--font-mono)",
                                          }}
                                        />
                                      </div>
                                    </div>
                                  );
                                })}

                                {/* Causal path */}
                                <CausalPathChips
                                  targetNode={item.target_node}
                                  graphNodes={graphNodes}
                                />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Run settings + actions */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 8,
                paddingTop: 8,
                borderTop: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <label
                  style={{
                    fontSize: 11,
                    color: "var(--text-secondary)",
                  }}
                >
                  Run Mode:
                </label>
                <select
                  value={runMode}
                  onChange={(e) =>
                    setRunMode(e.target.value as "deterministic" | "uq")
                  }
                  style={{
                    padding: "4px 8px",
                    background: "var(--bg-primary)",
                    border: "1px solid var(--border-default)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--text-primary)",
                    fontSize: 12,
                  }}
                >
                  <option value="deterministic">Deterministic</option>
                  <option value="uq">UQ (Monte Carlo)</option>
                </select>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSaveScenario}
                  style={{ flex: 1 }}
                >
                  {isNewScenario ? "Create" : "Save"}
                </Button>
                <Button
                  size="sm"
                  onClick={handleRunScenario}
                  style={{ flex: 1 }}
                >
                  Run {runMode === "uq" ? "(UQ)" : ""}
                </Button>
                {!isNewScenario && selectedScenario && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={handleDeleteScenario}
                  >
                    Delete
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Impact Preview */}
      <div style={{ flex: 1, overflow: "auto" }}>
        <ImpactPreview
          data={autoRun.previewData}
          scenarioName={scenarioName || "baseline"}
          isRunning={autoRun.isRunning}
          error={autoRun.error}
        />
      </div>
    </div>
  );
}
