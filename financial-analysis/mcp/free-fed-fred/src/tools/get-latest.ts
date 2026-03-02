import type { CallToolResult } from "@modelcontextprotocol/server";
import type { FredClient } from "../fred-client.js";
import { LatestInput, buildMeta, normalizeObservationValue } from "../types.js";

function toRecordArray(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null);
}

export async function getLatestTool(client: FredClient, input: unknown): Promise<CallToolResult> {
  const parsed = LatestInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const payload = await client.getObservations({
    series_id: parsed.data.series_id,
    realtime_start: parsed.data.realtime_start,
    realtime_end: parsed.data.realtime_end,
    frequency: parsed.data.frequency,
    units: parsed.data.units,
    aggregation_method: parsed.data.aggregation_method,
    sort_order: "desc",
    limit: parsed.data.points * 3,
    offset: 0
  });

  const rows = toRecordArray(payload.observations);
  const latest = rows
    .map((row) => ({
      date: row.date ?? null,
      value: normalizeObservationValue(row.value),
      realtime_start: row.realtime_start ?? null,
      realtime_end: row.realtime_end ?? null
    }))
    .filter((row) => row.value !== null)
    .slice(0, parsed.data.points);

  const output = {
    series_id: parsed.data.series_id,
    points_requested: parsed.data.points,
    points_returned: latest.length,
    latest,
    meta: buildMeta({
      source: "FRED latest observations",
      freshness: "delayed",
      confidence: latest.length === parsed.data.points ? "high" : "medium",
      missing_fields: latest.length === parsed.data.points ? [] : ["latest.value"]
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
