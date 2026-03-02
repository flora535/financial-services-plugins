import type { CallToolResult } from "@modelcontextprotocol/server";
import type { FredClient } from "../fred-client.js";
import { ReleaseObservationsInput, buildMeta, normalizeObservationValue } from "../types.js";

function toRecordArray(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null);
}

export async function getReleaseObservationsTool(client: FredClient, input: unknown): Promise<CallToolResult> {
  const parsed = ReleaseObservationsInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const payload = await client.getReleaseObservations({
    release_id: parsed.data.release_id,
    series_id: parsed.data.series_id,
    observation_start: parsed.data.observation_start,
    observation_end: parsed.data.observation_end,
    realtime_start: parsed.data.realtime_start,
    realtime_end: parsed.data.realtime_end,
    units: parsed.data.units,
    frequency: parsed.data.frequency,
    aggregation_method: parsed.data.aggregation_method,
    sort_order: parsed.data.sort_order,
    limit: parsed.data.limit,
    offset: parsed.data.offset
  });

  const observations = toRecordArray(payload.observations).map((row) => ({
    date: row.date ?? null,
    value: normalizeObservationValue(row.value),
    realtime_start: row.realtime_start ?? null,
    realtime_end: row.realtime_end ?? null,
    series_id: row.series_id ?? parsed.data.series_id ?? null
  }));

  const missingCount = observations.filter((row) => row.value === null).length;
  const output = {
    release_id: parsed.data.release_id,
    count: observations.length,
    offset: parsed.data.offset,
    limit: parsed.data.limit,
    observations,
    meta: buildMeta({
      source: "FRED release observations",
      freshness: "delayed",
      confidence: missingCount > 0 ? "medium" : "high",
      missing_fields: missingCount > 0 ? ["observations.value"] : []
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
