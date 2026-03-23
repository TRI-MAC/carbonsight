export interface GraphNode {
  name: string;
  type: string;
  is_input: boolean;
  upstream: string[];
  temporal: string[];
  tags: string[];
  display_name?: string;
  description?: string;
  data_source?: {
    name: string;
    publication_date?: string;
    url?: string;
  };
  assumptions?: Array<{
    description: string;
    rationale: string;
    confidence: string;
  }>;
}

export interface ScenarioConfig {
  name: string;
  overrides: Record<string, unknown>;
  metadata: Record<string, unknown>;
  interventions?: Array<{ type: string; params: Record<string, unknown> }>;
}

export interface YearOutput {
  [nodeName: string]: number | Record<string, number>;
}

export interface RunResult {
  scenario: string;
  mode: string;
  years: number[];
  wall_clock_seconds: number;
  performance_warning: boolean;
  outputs: Record<number, YearOutput>;
}

export interface ComparisonDelta {
  node_name: string;
  year: number;
  absolute_delta: number;
  percentage_delta: number;
}

export interface ComparisonResult {
  baseline: string;
  comparisons: Record<string, { deltas: ComparisonDelta[] }>;
}

export interface SensitivityDriver {
  name: string;
  label: string;
  first_order: number;
  total_order: number;
}

export interface AttributionSegment {
  intervention: string;
  contribution: number;
  percentage: number;
  direction: "increase" | "decrease";
}

export interface UncertaintyBand {
  year: number;
  median: number;
  p5: number;
  p25: number;
  p75: number;
  p95: number;
}

export interface TraceResponse {
  scenario: string;
  node: string;
  years: number[];
  values: number[];
  fields: string[] | null;
  field_values: Record<string, number[]> | null;
}
