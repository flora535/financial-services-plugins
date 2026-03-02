import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import { loadConfig } from "./config.js";
import { FileCache } from "./cache.js";
import { SecClient } from "./sec-client.js";
import {
  CompanyFactsInput,
  FilingSectionInput,
  FinancialStatementsInput,
  ListFilingsInput,
  ResolveCompanyInput
} from "./types.js";
import { resolveCompanyTool } from "./tools/resolve-company.js";
import { listFilingsTool } from "./tools/list-filings.js";
import { getCompanyFactsTool } from "./tools/get-company-facts.js";
import { getFinancialStatementsTool } from "./tools/get-financial-statements.js";
import { getFilingSectionTool } from "./tools/get-filing-section.js";

async function main(): Promise<void> {
  const config = loadConfig();
  const cache = new FileCache(config.cacheDir);
  const client = new SecClient(config, cache);

  const server = new McpServer({
    name: "free-sec-edgar",
    version: "0.1.0"
  });

  server.registerTool(
    "sec.resolve_company",
    {
      title: "Resolve SEC company",
      description: "Resolve ticker/CIK to normalized SEC company identity",
      inputSchema: ResolveCompanyInput
    },
    async (args: unknown) => resolveCompanyTool(client, args)
  );

  server.registerTool(
    "sec.list_filings",
    {
      title: "List SEC filings",
      description: "List recent SEC filings by CIK and form",
      inputSchema: ListFilingsInput
    },
    async (args: unknown) => listFilingsTool(client, args)
  );

  server.registerTool(
    "sec.get_company_facts",
    {
      title: "Get SEC company facts",
      description: "Fetch and normalize SEC companyfacts XBRL payload",
      inputSchema: CompanyFactsInput
    },
    async (args: unknown) => getCompanyFactsTool(client, args)
  );

  server.registerTool(
    "sec.get_financial_statements",
    {
      title: "Get normalized SEC statements",
      description: "Build normalized IS/BS/CF blocks from SEC XBRL data",
      inputSchema: FinancialStatementsInput
    },
    async (args: unknown) => getFinancialStatementsTool(client, args)
  );

  server.registerTool(
    "sec.get_filing_section",
    {
      title: "Extract SEC filing section",
      description: "Extract targeted section snippets from filing primary document",
      inputSchema: FilingSectionInput
    },
    async (args: unknown) => getFilingSectionTool(client, args)
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  process.stderr.write(`free-sec-edgar MCP failed: ${String(error)}\n`);
  process.exit(1);
});
