import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import { loadConfig } from "./config.js";
import { FileCache } from "./cache.js";
import { FredClient } from "./fred-client.js";
import {
  LatestInput,
  ObservationsInput,
  ReleaseObservationsInput,
  SearchSeriesInput,
  SeriesMetaInput,
  VintagesInput
} from "./types.js";
import { searchSeriesTool } from "./tools/search-series.js";
import { getSeriesMetaTool } from "./tools/get-series-meta.js";
import { getObservationsTool } from "./tools/get-observations.js";
import { getLatestTool } from "./tools/get-latest.js";
import { getVintagesTool } from "./tools/get-vintages.js";
import { getReleaseObservationsTool } from "./tools/get-release-observations.js";

async function main(): Promise<void> {
  const config = loadConfig();
  const cache = new FileCache(config.cacheDir);
  const client = new FredClient(config, cache);

  const server = new McpServer({
    name: "free-fed-fred",
    version: "0.1.0"
  });

  server.registerTool(
    "fred.search_series",
    {
      title: "Search FRED series",
      description: "Search FRED series by keyword with filters and sorting",
      inputSchema: SearchSeriesInput
    },
    async (args: unknown) => searchSeriesTool(client, args)
  );

  server.registerTool(
    "fred.get_series_meta",
    {
      title: "Get FRED series metadata",
      description: "Fetch canonical metadata for a FRED series",
      inputSchema: SeriesMetaInput
    },
    async (args: unknown) => getSeriesMetaTool(client, args)
  );

  server.registerTool(
    "fred.get_observations",
    {
      title: "Get FRED observations",
      description: "Fetch normalized time-series observations with realtime options",
      inputSchema: ObservationsInput
    },
    async (args: unknown) => getObservationsTool(client, args)
  );

  server.registerTool(
    "fred.get_latest",
    {
      title: "Get latest FRED observations",
      description: "Fetch latest non-missing observation points for a series",
      inputSchema: LatestInput
    },
    async (args: unknown) => getLatestTool(client, args)
  );

  server.registerTool(
    "fred.get_vintages",
    {
      title: "Get FRED vintages",
      description: "Fetch ALFRED vintage dates for a FRED series",
      inputSchema: VintagesInput
    },
    async (args: unknown) => getVintagesTool(client, args)
  );

  server.registerTool(
    "fred.get_release_observations",
    {
      title: "Get FRED release observations",
      description: "Fetch release-based observations by release_id",
      inputSchema: ReleaseObservationsInput
    },
    async (args: unknown) => getReleaseObservationsTool(client, args)
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  process.stderr.write(`free-fed-fred MCP failed: ${String(error)}\n`);
  process.exit(1);
});
