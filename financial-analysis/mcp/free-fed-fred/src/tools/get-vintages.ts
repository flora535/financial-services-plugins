import type { CallToolResult } from "@modelcontextprotocol/server";
import type { FredClient } from "../fred-client.js";
import { VintagesInput, buildMeta } from "../types.js";

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

export async function getVintagesTool(client: FredClient, input: unknown): Promise<CallToolResult> {
  const parsed = VintagesInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const payload = await client.getVintageDates({
    series_id: parsed.data.series_id,
    realtime_start: parsed.data.realtime_start,
    realtime_end: parsed.data.realtime_end,
    limit: parsed.data.limit,
    offset: parsed.data.offset
  });

  const vintage_dates = toStringArray(payload.vintage_dates);
  const output = {
    series_id: parsed.data.series_id,
    count: vintage_dates.length,
    vintage_dates,
    range: {
      first: vintage_dates[0] ?? null,
      last: vintage_dates[vintage_dates.length - 1] ?? null
    },
    meta: buildMeta({
      source: "FRED series vintagedates",
      freshness: "delayed"
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
