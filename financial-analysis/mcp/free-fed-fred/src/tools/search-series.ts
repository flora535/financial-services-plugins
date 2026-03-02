import type { CallToolResult } from "@modelcontextprotocol/server";
import type { FredClient } from "../fred-client.js";
import { SearchSeriesInput, buildMeta } from "../types.js";

function toRecordArray(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null);
}

export async function searchSeriesTool(client: FredClient, input: unknown): Promise<CallToolResult> {
  const parsed = SearchSeriesInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const payload = await client.searchSeries({
    search_text: parsed.data.query,
    limit: parsed.data.limit,
    offset: parsed.data.offset,
    order_by: parsed.data.order_by,
    sort_order: parsed.data.sort_order,
    filter_variable: parsed.data.filter_variable,
    filter_value: parsed.data.filter_value,
    realtime_start: parsed.data.realtime_start,
    realtime_end: parsed.data.realtime_end
  });

  const seriesRows = toRecordArray(payload.seriess);
  const series = seriesRows.map((row) => ({
    id: row.id ?? null,
    title: row.title ?? null,
    frequency: row.frequency ?? null,
    units: row.units ?? null,
    seasonalAdjustment: row.seasonal_adjustment ?? null,
    observationStart: row.observation_start ?? null,
    observationEnd: row.observation_end ?? null,
    lastUpdated: row.last_updated ?? null,
    popularity: row.popularity ?? null
  }));

  const output = {
    query: parsed.data.query,
    count: series.length,
    total: typeof payload.count === "number" ? payload.count : series.length,
    offset: parsed.data.offset,
    limit: parsed.data.limit,
    series,
    meta: buildMeta({
      source: "FRED series search",
      freshness: "delayed"
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
