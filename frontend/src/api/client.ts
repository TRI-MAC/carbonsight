const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  // Demo
  getDemo: () =>
    request<{
      baseline: {
        trajectory: Array<{
          year: number;
          ghg: number;
          production: number;
          usage: number;
          disposal: number;
        }>;
        composition: Array<{
          year: number;
          total_vehicles: number;
          ICEV: number;
          HEV: number;
          PHEV: number;
          BEV: number;
        }>;
      };
      intervention: {
        trajectory: Array<{
          year: number;
          ghg: number;
          production: number;
          usage: number;
          disposal: number;
        }>;
        composition: Array<{
          year: number;
          total_vehicles: number;
          ICEV: number;
          HEV: number;
          PHEV: number;
          BEV: number;
        }>;
      };
      deltas: Array<{
        year: number;
        baseline_ghg: number;
        intervention_ghg: number;
        absolute_delta: number;
        percentage_delta: number;
      }>;
      cumulative_avoided_mt: number;
      intervention_description: {
        name: string;
        components: Array<{ type: string; description: string }>;
      };
      wall_clock_seconds: number;
    }>("/demo"),

  // Dashboard
  getDashboard: () =>
    request<{
      metrics: {
        fleet_size: number;
        annual_ghg: number;
        bev_share: number;
        bev_share_final: number;
        total_vmt: number;
      };
      trajectory: Array<{
        year: number;
        ghg: number;
        production: number;
        usage: number;
        disposal: number;
      }>;
      composition: Array<{
        year: number;
        total_vehicles: number;
        total_vmt: number;
        ICEV: number;
        HEV: number;
        PHEV: number;
        BEV: number;
      }>;
      wall_clock_seconds: number;
    }>("/dashboard"),

  // Interventions
  listInterventions: () =>
    request<
      Array<{
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
      }>
    >("/interventions"),

  // Scenarios
  listScenarios: () =>
    request<
      Array<{
        name: string;
        overrides: Record<string, unknown>;
        metadata: Record<string, unknown>;
      }>
    >("/scenarios"),
  getScenario: (name: string) =>
    request<{
      name: string;
      overrides: Record<string, unknown>;
      metadata: Record<string, unknown>;
    }>(`/scenarios/${encodeURIComponent(name)}`),
  createScenario: (data: {
    name: string;
    overrides?: Record<string, unknown>;
    metadata?: Record<string, unknown>;
    interventions?: Array<{ type: string; params: Record<string, unknown> }>;
  }) =>
    request<{ name: string }>("/scenarios", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateScenario: (
    name: string,
    data: {
      overrides?: Record<string, unknown>;
      metadata?: Record<string, unknown>;
      interventions?: Array<{ type: string; params: Record<string, unknown> }>;
    },
  ) =>
    request<{ name: string }>(`/scenarios/${encodeURIComponent(name)}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteScenario: (name: string) =>
    request<void>(`/scenarios/${encodeURIComponent(name)}`, {
      method: "DELETE",
    }),

  // Execution (returns immediately with job_id, simulation runs in background)
  runScenario: (
    name: string,
    opts?: {
      mode?: string;
      num_years?: number;
      start_year?: number;
      uq_samples?: number;
    },
  ) =>
    request<{ job_id: string; status: string; scenario: string; mode: string }>(
      `/scenarios/${encodeURIComponent(name)}/run`,
      {
        method: "POST",
        body: JSON.stringify({
          mode: "deterministic",
          num_years: 10,
          start_year: 2024,
          ...opts,
        }),
      },
    ),

  // Job polling
  getJobStatus: (jobId: string) =>
    request<{
      job_id: string;
      status: string;
      scenario: string;
      mode: string;
      result?: import("../types").RunResult;
      error?: string;
    }>(`/jobs/${encodeURIComponent(jobId)}`),

  pollJob: async (
    jobId: string,
    intervalMs = 1000,
  ): Promise<{
    status: string;
    result?: import("../types").RunResult;
    error?: string;
  }> => {
    while (true) {
      const job = await request<{
        job_id: string;
        status: string;
        result?: import("../types").RunResult;
        error?: string;
      }>(`/jobs/${encodeURIComponent(jobId)}`);
      if (job.status === "completed" || job.status === "failed") {
        return job;
      }
      await new Promise((r) => setTimeout(r, intervalMs));
    }
  },

  // Comparison
  compare: (baseline: string, interventions: string[]) =>
    request<import("../types").ComparisonResult>("/compare", {
      method: "POST",
      body: JSON.stringify({
        baseline_name: baseline,
        intervention_names: interventions,
      }),
    }),

  // Graph
  listNodes: () => request<import("../types").GraphNode[]>("/graph/nodes"),
  getNode: (name: string) =>
    request<import("../types").GraphNode>(
      `/graph/nodes/${encodeURIComponent(name)}`,
    ),

  // Provenance
  getProvenance: (scenario: string, node: string) =>
    request<{ scenario: string; node: string; report: string }>(
      `/scenarios/${encodeURIComponent(scenario)}/provenance/${encodeURIComponent(node)}`,
    ),

  // Sensitivity
  getSensitivity: (name: string) =>
    request<Record<string, unknown>>(
      `/scenarios/${encodeURIComponent(name)}/sensitivity`,
    ),

  // Node Trace
  getTrace: (scenario: string, nodeName: string) =>
    request<import("../types").TraceResponse>(
      `/scenarios/${encodeURIComponent(scenario)}/trace/${encodeURIComponent(nodeName)}`,
    ),

  // Export
  exportScenario: (name: string, format: string) =>
    request<Record<string, unknown>>(
      `/scenarios/${encodeURIComponent(name)}/export?format=${format}`,
    ),
};
