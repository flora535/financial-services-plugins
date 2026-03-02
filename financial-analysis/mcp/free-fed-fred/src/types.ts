import { z } from "zod";

const DateString = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Expected YYYY-MM-DD");
const SortOrder = z.enum(["asc", "desc"]);
const Units = z.enum(["lin", "chg", "ch1", "pch", "pc1", "pca", "cch", "cch1", "pch1"]);
const AggregationMethod = z.enum(["avg", "sum", "eop"]);

export const SearchSeriesInput = z.object({
  query: z.string().trim().min(1),
  limit: z.number().int().positive().max(1000).default(25),
  offset: z.number().int().nonnegative().default(0),
  order_by: z.string().trim().min(1).optional(),
  sort_order: SortOrder.default("desc"),
  filter_variable: z.string().trim().min(1).optional(),
  filter_value: z.string().trim().min(1).optional(),
  realtime_start: DateString.optional(),
  realtime_end: DateString.optional()
});

export const SeriesMetaInput = z.object({
  series_id: z.string().trim().min(1),
  realtime_start: DateString.optional(),
  realtime_end: DateString.optional()
});

export const ObservationsInput = z.object({
  series_id: z.string().trim().min(1),
  observation_start: DateString.optional(),
  observation_end: DateString.optional(),
  realtime_start: DateString.optional(),
  realtime_end: DateString.optional(),
  frequency: z.string().trim().min(1).optional(),
  units: Units.optional(),
  aggregation_method: AggregationMethod.optional(),
  sort_order: SortOrder.default("asc"),
  limit: z.number().int().positive().max(1000).default(1000),
  offset: z.number().int().nonnegative().default(0)
});

export const LatestInput = z.object({
  series_id: z.string().trim().min(1),
  points: z.number().int().positive().max(50).default(1),
  realtime_start: DateString.optional(),
  realtime_end: DateString.optional(),
  frequency: z.string().trim().min(1).optional(),
  units: Units.optional(),
  aggregation_method: AggregationMethod.optional()
});

export const VintagesInput = z.object({
  series_id: z.string().trim().min(1),
  realtime_start: DateString.optional(),
  realtime_end: DateString.optional(),
  limit: z.number().int().positive().max(1000).default(1000),
  offset: z.number().int().nonnegative().default(0)
});

export const ReleaseObservationsInput = z.object({
  release_id: z.number().int().positive(),
  series_id: z.string().trim().min(1).optional(),
  observation_start: DateString.optional(),
  observation_end: DateString.optional(),
  realtime_start: DateString.optional(),
  realtime_end: DateString.optional(),
  units: Units.optional(),
  frequency: z.string().trim().min(1).optional(),
  aggregation_method: AggregationMethod.optional(),
  sort_order: SortOrder.default("asc"),
  limit: z.number().int().positive().max(1000).default(1000),
  offset: z.number().int().nonnegative().default(0)
});

export interface SourceMeta {
  source: string;
  as_of: string;
  freshness: "live" | "eod" | "delayed" | "stale";
  confidence: "high" | "medium" | "low";
  fallback_used: boolean;
  missing_fields: string[];
}

export function buildMeta(partial?: Partial<SourceMeta>): SourceMeta {
  return {
    source: partial?.source || "FRED API",
    as_of: partial?.as_of || new Date().toISOString(),
    freshness: partial?.freshness || "delayed",
    confidence: partial?.confidence || "high",
    fallback_used: partial?.fallback_used || false,
    missing_fields: partial?.missing_fields || []
  };
}

export function normalizeObservationValue(raw: unknown): number | null {
  if (typeof raw !== "string") {
    return null;
  }
  const trimmed = raw.trim();
  if (!trimmed || trimmed === ".") {
    return null;
  }
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  return parsed;
}
