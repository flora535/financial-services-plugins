interface FactPoint {
  end?: string;
  val?: number;
  accn?: string;
  fy?: number;
  fp?: string;
  form?: string;
}

interface TaxonomyObject {
  [tag: string]: {
    units?: Record<string, FactPoint[]>;
  };
}

function latestPoint(points: FactPoint[]): FactPoint | null {
  const valid = points.filter((p) => typeof p.val === "number" && p.end);
  if (valid.length === 0) {
    return null;
  }
  return valid.sort((a, b) => (a.end! < b.end! ? 1 : -1))[0] ?? null;
}

export function extractMetrics(
  companyFacts: Record<string, unknown>,
  metricMap: Record<string, string[]>
): Record<string, { value: number | null; end: string | null; sourceTag: string | null }> {
  const out: Record<string, { value: number | null; end: string | null; sourceTag: string | null }> = {};

  const gaap = (companyFacts["facts"] as Record<string, unknown> | undefined)?.["us-gaap"] as TaxonomyObject | undefined;
  const dei = (companyFacts["facts"] as Record<string, unknown> | undefined)?.["dei"] as TaxonomyObject | undefined;

  for (const [metric, tags] of Object.entries(metricMap)) {
    out[metric] = { value: null, end: null, sourceTag: null };
    for (const tag of tags) {
      const node = gaap?.[tag] ?? dei?.[tag];
      const units = node?.units;
      if (!units) {
        continue;
      }
      const firstUnit = Object.values(units)[0] ?? [];
      const latest = latestPoint(firstUnit);
      if (!latest || typeof latest.val !== "number") {
        continue;
      }

      out[metric] = {
        value: latest.val,
        end: latest.end ?? null,
        sourceTag: tag
      };
      break;
    }
  }

  return out;
}
