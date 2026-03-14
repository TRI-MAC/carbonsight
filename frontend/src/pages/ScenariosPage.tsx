import { useState, useEffect, useMemo } from "react";
import Button from "../components/Button";
import Card from "../components/Card";
import NodeTraceChart from "../components/NodeTraceChart";
import type { Trace } from "../components/NodeTraceChart";
import { api } from "../api/client";
import type { ScenarioConfig, RunResult } from "../types";

interface InterventionValue {
  category: string;
  name: string;
  value: number;
  unit: string;
  min?: number;
  max?: number;
}

interface ScenarioWithStatus extends ScenarioConfig {
  status?: "idle" | "running" | "completed" | "error";
  runResult?: RunResult;
  error?: string;
}

const INTERVENTION_CATEGORIES = {
  Policy: [
    { name: "carbon_pricing", label: "Carbon pricing", unit: "$/ton", min: 0 },
    { name: "ev_subsidy", label: "EV subsidy", unit: "$", min: 0 },
    { name: "zev_mandate", label: "ZEV mandate", unit: "%", min: 0, max: 100 },
    { name: "cafe_standard", label: "CAFE standard", unit: "mpg", min: 0 },
  ],
  Technology: [
    {
      name: "battery_cost_reduction",
      label: "Battery cost reduction",
      unit: "%",
      min: 0,
      max: 100,
    },
    {
      name: "vehicle_lightweighting",
      label: "Vehicle lightweighting",
      unit: "%",
      min: 0,
      max: 100,
    },
  ],
  Behavioral: [
    {
      name: "vmt_reduction",
      label: "VMT reduction",
      unit: "%",
      min: 0,
      max: 100,
    },
    {
      name: "phev_charging_improvement",
      label: "PHEV charging improvement",
      unit: "%",
      min: 0,
      max: 100,
    },
  ],
  "Grid/Energy": [
    {
      name: "grid_decarbonization_rate",
      label: "Grid decarbonization rate",
      unit: "%",
      min: 0,
      max: 100,
    },
  ],
};

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<ScenarioWithStatus[]>([]);
  const [selectedScenario, setSelectedScenario] =
    useState<ScenarioWithStatus | null>(null);
  const [isNewScenario, setIsNewScenario] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form state
  const [scenarioName, setScenarioName] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("Policy");
  const [interventions, setInterventions] = useState<
    Record<string, InterventionValue>
  >({});
  const [customOverrides, setCustomOverrides] = useState<
    Array<{ key: string; value: string }>
  >([{ key: "", value: "" }]);
  const [runMode, setRunMode] = useState<"deterministic" | "uq">(
    "deterministic",
  );
  const [numYears, setNumYears] = useState(10);
  const [traceNode, setTraceNode] = useState<string | null>(null);
  const [traceField, setTraceField] = useState<string | null>(null);

  // Load scenarios on mount
  useEffect(() => {
    loadScenarios();
  }, []);

  async function loadScenarios() {
    try {
      setLoading(true);
      const data = await api.listScenarios();
      const scenariosWithStatus: ScenarioWithStatus[] = data.map((s) => ({
        ...s,
        status: "idle" as const,
      }));
      setScenarios(scenariosWithStatus);
      setDemoMode(false);
    } catch (error) {
      console.warn("API unavailable, using demo mode:", error);
      setDemoMode(true);
      setScenarios([]);
    } finally {
      setLoading(false);
    }
  }

  function handleNewScenario() {
    setIsNewScenario(true);
    setSelectedScenario(null);
    setScenarioName("");
    setInterventions({});
    setCustomOverrides([{ key: "", value: "" }]);
    setRunMode("deterministic");
    setNumYears(10);
  }

  function handleSelectScenario(scenario: ScenarioWithStatus) {
    setIsNewScenario(false);
    setSelectedScenario(scenario);
    setScenarioName(scenario.name);

    // Parse overrides into interventions
    const parsed: Record<string, InterventionValue> = {};
    Object.entries(scenario.overrides).forEach(([key, value]) => {
      // Find matching intervention
      for (const [category, interventionList] of Object.entries(
        INTERVENTION_CATEGORIES,
      )) {
        const intervention = interventionList.find((i) => i.name === key);
        if (intervention) {
          parsed[key] = {
            category,
            name: key,
            value: Number(value),
            unit: intervention.unit,
            min: intervention.min,
            max: intervention.max,
          };
        }
      }
    });
    setInterventions(parsed);

    // Custom overrides
    const customKeys = Object.keys(scenario.overrides).filter((key) => {
      return !Object.values(INTERVENTION_CATEGORIES)
        .flat()
        .some((i) => i.name === key);
    });
    if (customKeys.length > 0) {
      setCustomOverrides(
        customKeys.map((key) => ({
          key,
          value: String(scenario.overrides[key]),
        })),
      );
    } else {
      setCustomOverrides([{ key: "", value: "" }]);
    }
  }

  function handleInterventionChange(
    category: string,
    name: string,
    value: number,
    unit: string,
    min?: number,
    max?: number,
  ) {
    setInterventions((prev) => ({
      ...prev,
      [name]: { category, name, value, unit, min, max },
    }));
  }

  function handleRemoveIntervention(name: string) {
    setInterventions((prev) => {
      const copy = { ...prev };
      delete copy[name];
      return copy;
    });
  }

  function handleCustomOverrideChange(
    index: number,
    field: "key" | "value",
    value: string,
  ) {
    setCustomOverrides((prev) => {
      const copy = [...prev];
      copy[index][field] = value;
      return copy;
    });
  }

  function handleAddCustomOverride() {
    setCustomOverrides((prev) => [...prev, { key: "", value: "" }]);
  }

  function handleRemoveCustomOverride(index: number) {
    setCustomOverrides((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSaveScenario() {
    if (!scenarioName.trim()) {
      alert("Please enter a scenario name");
      return;
    }

    const overrides: Record<string, unknown> = {};
    Object.values(interventions).forEach((intervention) => {
      overrides[intervention.name] = intervention.value;
    });

    customOverrides.forEach(({ key, value }) => {
      if (key.trim() && value.trim()) {
        try {
          overrides[key] = JSON.parse(value);
        } catch {
          overrides[key] = value;
        }
      }
    });

    try {
      if (isNewScenario) {
        await api.createScenario({
          name: scenarioName,
          overrides,
          metadata: {},
        });
      } else {
        await api.updateScenario(scenarioName, { overrides, metadata: {} });
      }
      await loadScenarios();
      setIsNewScenario(false);
    } catch (error) {
      if (demoMode) {
        // In demo mode, just add to local state
        const newScenario: ScenarioWithStatus = {
          name: scenarioName,
          overrides,
          metadata: {},
          status: "idle",
        };
        if (isNewScenario) {
          setScenarios((prev) => [...prev, newScenario]);
        } else {
          setScenarios((prev) =>
            prev.map((s) => (s.name === scenarioName ? newScenario : s)),
          );
        }
        setSelectedScenario(newScenario);
        setIsNewScenario(false);
      } else {
        alert(`Failed to save scenario: ${error}`);
      }
    }
  }

  async function handleDeleteScenario() {
    if (!selectedScenario) return;
    if (
      !confirm(
        `Are you sure you want to delete scenario "${selectedScenario.name}"?`,
      )
    ) {
      return;
    }

    try {
      await api.deleteScenario(selectedScenario.name);
      await loadScenarios();
      setSelectedScenario(null);
      setIsNewScenario(false);
    } catch (error) {
      if (demoMode) {
        setScenarios((prev) =>
          prev.filter((s) => s.name !== selectedScenario.name),
        );
        setSelectedScenario(null);
        setIsNewScenario(false);
      } else {
        alert(`Failed to delete scenario: ${error}`);
      }
    }
  }

  async function handleRunScenario() {
    if (!scenarioName.trim()) {
      alert("Please save the scenario before running");
      return;
    }

    // Update status
    setScenarios((prev) =>
      prev.map((s) =>
        s.name === scenarioName ? { ...s, status: "running" as const } : s,
      ),
    );

    if (selectedScenario) {
      setSelectedScenario({ ...selectedScenario, status: "running" });
    }

    try {
      const result = await api.runScenario(scenarioName, {
        mode: runMode,
        num_years: numYears,
        uq_samples: runMode === "uq" ? 1000 : undefined,
      });

      setScenarios((prev) =>
        prev.map((s) =>
          s.name === scenarioName
            ? { ...s, status: "completed" as const, runResult: result }
            : s,
        ),
      );

      if (selectedScenario) {
        setSelectedScenario({
          ...selectedScenario,
          status: "completed",
          runResult: result,
        });
      }
    } catch (error) {
      const errorMsg = String(error);
      setScenarios((prev) =>
        prev.map((s) =>
          s.name === scenarioName
            ? { ...s, status: "error" as const, error: errorMsg }
            : s,
        ),
      );

      if (selectedScenario) {
        setSelectedScenario({
          ...selectedScenario,
          status: "error",
          error: errorMsg,
        });
      }
    }
  }

  // Extract node list and trace from run result
  const runResult = selectedScenario?.runResult ?? null;
  const nodeNames = useMemo(() => {
    if (!runResult) return [];
    const firstYear = runResult.years[0];
    const outputs = runResult.outputs[firstYear];
    return outputs ? Object.keys(outputs).sort() : [];
  }, [runResult]);

  const traceFields = useMemo(() => {
    if (!runResult || !traceNode) return null;
    const firstYear = runResult.years[0];
    const val = runResult.outputs[firstYear]?.[traceNode];
    if (val && typeof val === "object" && !Array.isArray(val)) {
      return Object.keys(val as Record<string, number>);
    }
    return null;
  }, [runResult, traceNode]);

  const traceData: Trace | null = useMemo(() => {
    if (!runResult || !traceNode) return null;
    const years = runResult.years;
    const values = years.map((yr) => {
      const val = runResult.outputs[yr]?.[traceNode];
      if (val === undefined || val === null) return 0;
      if (typeof val === "number") return val;
      if (typeof val === "object" && !Array.isArray(val)) {
        const dict = val as Record<string, number>;
        const field = traceField ?? traceFields?.[0] ?? null;
        return field ? (dict[field] ?? 0) : 0;
      }
      return 0;
    });
    return { scenario: selectedScenario?.name ?? "", years, values };
  }, [runResult, traceNode, traceField, traceFields, selectedScenario]);

  // Reset trace field when node changes
  useEffect(() => {
    setTraceField(null);
  }, [traceNode]);

  const activeScenario = isNewScenario
    ? {
        name: scenarioName,
        overrides: {},
        metadata: {},
        status: "idle" as const,
      }
    : selectedScenario;

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
      {/* Left Panel - Scenario List */}
      <div
        style={{
          width: 300,
          borderRight: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          background: "var(--bg-surface)",
        }}
      >
        <div
          style={{
            padding: "16px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <h2
            style={{
              fontSize: 16,
              fontWeight: 600,
              marginBottom: 12,
              color: "var(--text-primary)",
            }}
          >
            Scenarios
          </h2>
          <Button
            variant="primary"
            onClick={handleNewScenario}
            style={{ width: "100%" }}
          >
            + New Scenario
          </Button>
          {demoMode && (
            <div
              style={{
                marginTop: 8,
                padding: "6px 10px",
                background: "rgba(251, 191, 36, 0.1)",
                border: "1px solid rgba(251, 191, 36, 0.3)",
                borderRadius: "var(--radius-md)",
                fontSize: 11,
                color: "#fbbf24",
              }}
            >
              Demo Mode: API unavailable
            </div>
          )}
        </div>
        <div style={{ flex: 1, overflow: "auto" }}>
          {loading ? (
            <div
              style={{
                padding: 16,
                color: "var(--text-muted)",
                fontSize: 13,
              }}
            >
              Loading...
            </div>
          ) : scenarios.length === 0 ? (
            <div
              style={{
                padding: 16,
                color: "var(--text-muted)",
                fontSize: 13,
              }}
            >
              No scenarios yet. Create one to get started.
            </div>
          ) : (
            scenarios.map((scenario) => (
              <div
                key={scenario.name}
                onClick={() => handleSelectScenario(scenario)}
                style={{
                  padding: "12px 16px",
                  borderBottom: "1px solid var(--border-subtle)",
                  cursor: "pointer",
                  background:
                    selectedScenario?.name === scenario.name
                      ? "var(--bg-elevated)"
                      : "transparent",
                  transition: "background 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  if (selectedScenario?.name !== scenario.name) {
                    e.currentTarget.style.background = "var(--bg-hover)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedScenario?.name !== scenario.name) {
                    e.currentTarget.style.background = "transparent";
                  }
                }}
              >
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 500,
                    color: "var(--text-primary)",
                    marginBottom: 4,
                  }}
                >
                  {scenario.name}
                </div>
                <div
                  style={{
                    fontSize: 11,
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

      {/* Right Panel - Scenario Editor */}
      <div
        style={{
          flex: 1,
          overflow: "auto",
          padding: 24,
        }}
      >
        {!activeScenario ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "var(--text-muted)",
              fontSize: 14,
            }}
          >
            Select a scenario or create a new one
          </div>
        ) : (
          <div style={{ maxWidth: 800 }}>
            <Card
              title="Scenario Configuration"
              actions={
                !isNewScenario && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={handleDeleteScenario}
                  >
                    Delete
                  </Button>
                )
              }
            >
              <div
                style={{ display: "flex", flexDirection: "column", gap: 20 }}
              >
                {/* Name */}
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: 12,
                      fontWeight: 500,
                      color: "var(--text-secondary)",
                      marginBottom: 6,
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
                      padding: "8px 12px",
                      background: isNewScenario
                        ? "var(--bg-primary)"
                        : "var(--bg-elevated)",
                      border: "1px solid var(--border-default)",
                      borderRadius: "var(--radius-md)",
                      color: "var(--text-primary)",
                      fontSize: 13,
                      fontFamily: "var(--font-body)",
                      opacity: isNewScenario ? 1 : 0.6,
                    }}
                  />
                </div>

                {/* Interventions */}
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: 12,
                      fontWeight: 500,
                      color: "var(--text-secondary)",
                      marginBottom: 6,
                    }}
                  >
                    Interventions
                  </label>
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      marginBottom: 12,
                    }}
                  >
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      style={{
                        flex: 1,
                        padding: "8px 12px",
                        background: "var(--bg-primary)",
                        border: "1px solid var(--border-default)",
                        borderRadius: "var(--radius-md)",
                        color: "var(--text-primary)",
                        fontSize: 13,
                        fontFamily: "var(--font-body)",
                      }}
                    >
                      {Object.keys(INTERVENTION_CATEGORIES).map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Available Interventions */}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 8,
                      marginBottom: 12,
                    }}
                  >
                    {INTERVENTION_CATEGORIES[
                      selectedCategory as keyof typeof INTERVENTION_CATEGORIES
                    ].map((intervention) => {
                      const isActive = interventions[intervention.name];
                      return (
                        <div
                          key={intervention.name}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                            padding: "8px 12px",
                            background: isActive
                              ? "var(--bg-elevated)"
                              : "var(--bg-primary)",
                            border: "1px solid var(--border-default)",
                            borderRadius: "var(--radius-md)",
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={!!isActive}
                            onChange={(e) => {
                              if (e.target.checked) {
                                handleInterventionChange(
                                  selectedCategory,
                                  intervention.name,
                                  0,
                                  intervention.unit,
                                  intervention.min,
                                  intervention.max,
                                );
                              } else {
                                handleRemoveIntervention(intervention.name);
                              }
                            }}
                            style={{ cursor: "pointer" }}
                          />
                          <label
                            style={{
                              flex: 1,
                              fontSize: 13,
                              color: "var(--text-primary)",
                              cursor: "pointer",
                            }}
                            onClick={() => {
                              if (isActive) {
                                handleRemoveIntervention(intervention.name);
                              } else {
                                handleInterventionChange(
                                  selectedCategory,
                                  intervention.name,
                                  0,
                                  intervention.unit,
                                  intervention.min,
                                  intervention.max,
                                );
                              }
                            }}
                          >
                            {intervention.label}
                          </label>
                          {isActive && (
                            <>
                              <input
                                type="number"
                                value={isActive.value}
                                onChange={(e) =>
                                  handleInterventionChange(
                                    selectedCategory,
                                    intervention.name,
                                    Number(e.target.value),
                                    intervention.unit,
                                    intervention.min,
                                    intervention.max,
                                  )
                                }
                                min={intervention.min}
                                max={intervention.max}
                                step={intervention.unit === "%" ? 1 : 0.1}
                                style={{
                                  width: 80,
                                  padding: "4px 8px",
                                  background: "var(--bg-primary)",
                                  border: "1px solid var(--border-default)",
                                  borderRadius: "var(--radius-md)",
                                  color: "var(--text-primary)",
                                  fontSize: 13,
                                  fontFamily: "var(--font-mono)",
                                }}
                              />
                              <span
                                style={{
                                  fontSize: 12,
                                  color: "var(--text-muted)",
                                  minWidth: 40,
                                }}
                              >
                                {intervention.unit}
                              </span>
                            </>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Custom Overrides */}
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: 12,
                      fontWeight: 500,
                      color: "var(--text-secondary)",
                      marginBottom: 6,
                    }}
                  >
                    Custom Node Overrides
                  </label>
                  <div
                    style={{ display: "flex", flexDirection: "column", gap: 8 }}
                  >
                    {customOverrides.map((override, index) => (
                      <div
                        key={index}
                        style={{
                          display: "flex",
                          gap: 8,
                          alignItems: "center",
                        }}
                      >
                        <input
                          type="text"
                          value={override.key}
                          onChange={(e) =>
                            handleCustomOverrideChange(
                              index,
                              "key",
                              e.target.value,
                            )
                          }
                          placeholder="Node name"
                          style={{
                            flex: 1,
                            padding: "8px 12px",
                            background: "var(--bg-primary)",
                            border: "1px solid var(--border-default)",
                            borderRadius: "var(--radius-md)",
                            color: "var(--text-primary)",
                            fontSize: 13,
                            fontFamily: "var(--font-mono)",
                          }}
                        />
                        <input
                          type="text"
                          value={override.value}
                          onChange={(e) =>
                            handleCustomOverrideChange(
                              index,
                              "value",
                              e.target.value,
                            )
                          }
                          placeholder="Value (JSON)"
                          style={{
                            flex: 1,
                            padding: "8px 12px",
                            background: "var(--bg-primary)",
                            border: "1px solid var(--border-default)",
                            borderRadius: "var(--radius-md)",
                            color: "var(--text-primary)",
                            fontSize: 13,
                            fontFamily: "var(--font-mono)",
                          }}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveCustomOverride(index)}
                          disabled={customOverrides.length === 1}
                        >
                          ×
                        </Button>
                      </div>
                    ))}
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleAddCustomOverride}
                      style={{ alignSelf: "flex-start" }}
                    >
                      + Add Override
                    </Button>
                  </div>
                </div>

                {/* Save Button */}
                <div style={{ display: "flex", gap: 8 }}>
                  <Button variant="primary" onClick={handleSaveScenario}>
                    {isNewScenario ? "Create Scenario" : "Save Changes"}
                  </Button>
                </div>
              </div>
            </Card>

            {/* Run Controls */}
            {!isNewScenario && selectedScenario && (
              <Card title="Run Simulation" style={{ marginTop: 20 }}>
                <div
                  style={{ display: "flex", flexDirection: "column", gap: 16 }}
                >
                  <div style={{ display: "flex", gap: 16 }}>
                    <div style={{ flex: 1 }}>
                      <label
                        style={{
                          display: "block",
                          fontSize: 12,
                          fontWeight: 500,
                          color: "var(--text-secondary)",
                          marginBottom: 6,
                        }}
                      >
                        Mode
                      </label>
                      <select
                        value={runMode}
                        onChange={(e) =>
                          setRunMode(e.target.value as "deterministic" | "uq")
                        }
                        style={{
                          width: "100%",
                          padding: "8px 12px",
                          background: "var(--bg-primary)",
                          border: "1px solid var(--border-default)",
                          borderRadius: "var(--radius-md)",
                          color: "var(--text-primary)",
                          fontSize: 13,
                          fontFamily: "var(--font-body)",
                        }}
                      >
                        <option value="deterministic">Deterministic</option>
                        <option value="uq">Uncertainty Quantification</option>
                      </select>
                    </div>
                    <div style={{ flex: 1 }}>
                      <label
                        style={{
                          display: "block",
                          fontSize: 12,
                          fontWeight: 500,
                          color: "var(--text-secondary)",
                          marginBottom: 6,
                        }}
                      >
                        Years
                      </label>
                      <input
                        type="number"
                        value={numYears}
                        onChange={(e) => setNumYears(Number(e.target.value))}
                        min={1}
                        max={50}
                        style={{
                          width: "100%",
                          padding: "8px 12px",
                          background: "var(--bg-primary)",
                          border: "1px solid var(--border-default)",
                          borderRadius: "var(--radius-md)",
                          color: "var(--text-primary)",
                          fontSize: 13,
                          fontFamily: "var(--font-mono)",
                        }}
                      />
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    onClick={handleRunScenario}
                    disabled={selectedScenario.status === "running"}
                  >
                    {selectedScenario.status === "running"
                      ? "Running..."
                      : "Run Simulation"}
                  </Button>

                  {/* Run Results */}
                  {selectedScenario.runResult && (
                    <div
                      style={{
                        marginTop: 16,
                        padding: 12,
                        background: "var(--bg-primary)",
                        border: "1px solid var(--border-default)",
                        borderRadius: "var(--radius-md)",
                      }}
                    >
                      <div
                        style={{
                          fontSize: 12,
                          fontWeight: 600,
                          color: "var(--text-primary)",
                          marginBottom: 8,
                        }}
                      >
                        Run Summary
                      </div>
                      <div
                        style={{
                          fontSize: 12,
                          color: "var(--text-secondary)",
                          display: "flex",
                          flexDirection: "column",
                          gap: 4,
                        }}
                      >
                        <div>
                          Mode:{" "}
                          <strong>{selectedScenario.runResult.mode}</strong>
                        </div>
                        <div>
                          Years:{" "}
                          <strong>
                            {selectedScenario.runResult.years.join(", ")}
                          </strong>
                        </div>
                        <div>
                          Runtime:{" "}
                          <strong>
                            {selectedScenario.runResult.wall_clock_seconds.toFixed(
                              2,
                            )}
                            s
                          </strong>
                        </div>
                        <div>
                          Outputs:{" "}
                          <strong>
                            {
                              Object.keys(
                                selectedScenario.runResult.outputs[
                                  selectedScenario.runResult.years[0]
                                ] || {},
                              ).length
                            }{" "}
                            nodes
                          </strong>
                        </div>
                        {selectedScenario.runResult.performance_warning && (
                          <div
                            style={{
                              color: "var(--accent-red)",
                              marginTop: 4,
                            }}
                          >
                            ⚠ Performance warning
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Node Trace */}
                  {selectedScenario.runResult && nodeNames.length > 0 && (
                    <Card title="Node Value Trace" style={{ marginTop: 20 }}>
                      <div
                        style={{
                          display: "flex",
                          gap: 16,
                        }}
                      >
                        <div
                          style={{
                            width: 180,
                            maxHeight: 300,
                            overflow: "auto",
                            borderRight: "1px solid var(--border-subtle)",
                            paddingRight: 12,
                          }}
                        >
                          <div
                            style={{
                              fontSize: 11,
                              color: "var(--text-muted)",
                              textTransform: "uppercase",
                              marginBottom: 8,
                            }}
                          >
                            Nodes
                          </div>
                          {nodeNames.map((name) => (
                            <div
                              key={name}
                              onClick={() => setTraceNode(name)}
                              style={{
                                padding: "6px 8px",
                                fontSize: 12,
                                fontFamily: "var(--font-mono)",
                                cursor: "pointer",
                                borderRadius: "var(--radius-sm)",
                                background:
                                  traceNode === name
                                    ? "var(--bg-elevated)"
                                    : "transparent",
                                color:
                                  traceNode === name
                                    ? "var(--text-primary)"
                                    : "var(--text-secondary)",
                              }}
                            >
                              {name}
                            </div>
                          ))}
                        </div>
                        <div style={{ flex: 1 }}>
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
                          {traceData ? (
                            <NodeTraceChart
                              traces={[traceData]}
                              nodeName={traceNode ?? ""}
                              fieldName={
                                traceFields
                                  ? (traceField ?? traceFields[0])
                                  : undefined
                              }
                            />
                          ) : (
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "center",
                                alignItems: "center",
                                height: 200,
                                color: "var(--text-muted)",
                                fontSize: 13,
                              }}
                            >
                              Select a node to view its trace
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  )}

                  {selectedScenario.error && (
                    <div
                      style={{
                        marginTop: 16,
                        padding: 12,
                        background: "rgba(248, 113, 113, 0.1)",
                        border: "1px solid rgba(248, 113, 113, 0.3)",
                        borderRadius: "var(--radius-md)",
                        color: "var(--accent-red)",
                        fontSize: 12,
                      }}
                    >
                      <strong>Error:</strong> {selectedScenario.error}
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
