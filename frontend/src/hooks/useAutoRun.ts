import { useState, useRef, useCallback, useEffect } from "react";
import { api } from "../api/client";

export interface PreviewData {
  baselineTrajectory: Array<{ year: number; ghg: number }>;
  scenarioTrajectory: Array<{ year: number; ghg: number }>;
  composition: Array<{
    year: number;
    ICEV: number;
    HEV: number;
    PHEV: number;
    BEV: number;
  }>;
  deltas: {
    totalGhg: { value: number; pct: number };
    bevShare: { value: number; pct: number };
    fleetSize: { value: number; pct: number };
    gridIntensity: { value: number; pct: number };
  };
}

export function useAutoRun(scenarioName: string, debounceMs = 800) {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runIdRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const trigger = useCallback(() => {
    if (!scenarioName || scenarioName === "baseline") return;

    if (timerRef.current) clearTimeout(timerRef.current);

    timerRef.current = setTimeout(async () => {
      const thisRunId = ++runIdRef.current;
      setIsRunning(true);
      setError(null);

      try {
        // Submit job (always deterministic for auto-run)
        const job = await api.runScenario(scenarioName, {
          mode: "deterministic",
          num_years: 10,
        });

        // Poll until complete
        const completed = await api.pollJob(job.job_id);
        if (completed.status === "failed") {
          throw new Error(completed.error ?? "Simulation failed");
        }

        if (runIdRef.current !== thisRunId) return;

        const [
          scenarioEmissions,
          baselineEmissions,
          scenarioFleet,
          baselineFleet,
          scenarioGrid,
          baselineGrid,
        ] = await Promise.all([
          api.getTrace(scenarioName, "total_emissions"),
          api.getTrace("baseline", "total_emissions"),
          api.getTrace(scenarioName, "fleet_snapshot"),
          api.getTrace("baseline", "fleet_snapshot"),
          api.getTrace(scenarioName, "grid_ghg_per_kwh").catch(() => null),
          api.getTrace("baseline", "grid_ghg_per_kwh").catch(() => null),
        ]);

        if (runIdRef.current !== thisRunId) return;

        const years = scenarioEmissions.years;
        const baseTraj = years.map((y, i) => ({
          year: y,
          ghg:
            (baselineEmissions.field_values?.total_ghg?.[i] ??
              baselineEmissions.values[i]) / 1e9,
        }));
        const scenTraj = years.map((y, i) => ({
          year: y,
          ghg:
            (scenarioEmissions.field_values?.total_ghg?.[i] ??
              scenarioEmissions.values[i]) / 1e9,
        }));

        const sfv = scenarioFleet.field_values;
        const comp = years.map((y, i) => {
          const total = sfv?.total_vehicles?.[i] ?? 1;
          return {
            year: y,
            ICEV: ((sfv?.icev?.[i] ?? 0) / total) * 100,
            HEV: ((sfv?.hev?.[i] ?? 0) / total) * 100,
            PHEV: ((sfv?.phev?.[i] ?? 0) / total) * 100,
            BEV: ((sfv?.bev?.[i] ?? 0) / total) * 100,
          };
        });

        const last = years.length - 1;
        const baseGhg = baseTraj[last].ghg;
        const scenGhg = scenTraj[last].ghg;

        const bfv = baselineFleet.field_values;
        const baseTotal = bfv?.total_vehicles?.[last] ?? 1;
        const scenTotal = sfv?.total_vehicles?.[last] ?? 1;
        const baseBev = ((bfv?.bev?.[last] ?? 0) / baseTotal) * 100;
        const scenBev = ((sfv?.bev?.[last] ?? 0) / scenTotal) * 100;

        const baseGrid = baselineGrid?.values[last] ?? 0;
        const scenGrid = scenarioGrid?.values[last] ?? 0;

        const pct = (a: number, b: number) =>
          b !== 0 ? ((a - b) / Math.abs(b)) * 100 : 0;

        setPreviewData({
          baselineTrajectory: baseTraj,
          scenarioTrajectory: scenTraj,
          composition: comp,
          deltas: {
            totalGhg: { value: scenGhg - baseGhg, pct: pct(scenGhg, baseGhg) },
            bevShare: {
              value: scenBev - baseBev,
              pct: pct(scenBev, baseBev),
            },
            fleetSize: {
              value: scenTotal - baseTotal,
              pct: pct(scenTotal, baseTotal),
            },
            gridIntensity: {
              value: scenGrid - baseGrid,
              pct: pct(scenGrid, baseGrid),
            },
          },
        });
      } catch (e) {
        if (runIdRef.current === thisRunId) {
          setError(String(e));
        }
      } finally {
        if (runIdRef.current === thisRunId) {
          setIsRunning(false);
        }
      }
    }, debounceMs);
  }, [scenarioName, debounceMs]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { previewData, isRunning, error, trigger };
}
