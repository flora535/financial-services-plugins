import type { CallToolResult } from "@modelcontextprotocol/server";
import type { FredClient } from "../fred-client.js";
import { SeriesMetaInput, buildMeta } from "../types.js";

function toRecordArray(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null);
}

export async function getSeriesMetaTool(client: FredClient, input: unknown): Promise<CallToolResult> {
  const parsed = SeriesMetaInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const payload = await client.getSeries({
    series_id: parsed.data.series_id,
    realtime_start: parsed.data.realtime_start,
    realtime_end: parsed.data.realtime_end
  });

  const rows = toRecordArray(payload.seriess);
  const row = rows[0];
  if (!row) {
    return {
      isError: true,
      content: [{ type: "text", text: `Series not found: ${parsed.data.series_id}` }]
    };
  }

  const output = {
    series_id: parsed.data.series_id,
    series: {
      id: row.id ?? null,
      title: row.title ?? null,
      frequency: row.frequency ?? null,
      frequencyShort: row.frequency_short ?? null,
      units: row.units ?? null,
      unitsShort: row.units_short ?? null,
      seasonalAdjustment: row.seasonal_adjustment ?? null,
      seasonalAdjustmentShort: row.seasonal_adjustment_short ?? null,
      observationStart: row.observation_start ?? null,
      observationEnd: row.observation_end ?? null,
      lastUpdated: row.last_updated ?? null,
      popularity: row.popularity ?? null,
      notes: row.notes ?? null
    },
    meta: buildMeta({
      source: "FRED series metadata",
      freshness: "delayed"
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
