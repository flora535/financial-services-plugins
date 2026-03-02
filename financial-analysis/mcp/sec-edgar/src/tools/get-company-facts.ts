import type { CallToolResult } from "@modelcontextprotocol/server";
import { CompanyFactsInput, buildMeta } from "../types.js";
import type { SecClient } from "../sec-client.js";
import { extractMetrics } from "../mappers/company-facts.js";

const DEFAULT_METRICS: Record<string, string[]> = {
  revenue: ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
  netIncome: ["NetIncomeLoss"],
  totalAssets: ["Assets"],
  totalLiabilities: ["Liabilities"],
  sharesDiluted: ["WeightedAverageNumberOfDilutedSharesOutstanding"]
};

export async function getCompanyFactsTool(client: SecClient, input: unknown): Promise<CallToolResult> {
  const parsed = CompanyFactsInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const { cik, metrics } = parsed.data;
  const companyFacts = await client.getCompanyFacts(cik);

  const metricMap = metrics
    ? Object.fromEntries(metrics.map((name: string) => [name, [name]]))
    : DEFAULT_METRICS;

  const extracted = extractMetrics(companyFacts, metricMap);
  const missing = Object.entries(extracted)
    .filter(([, v]) => v.value === null)
    .map(([k]) => k);

  const output = {
    cik,
    facts: extracted,
    meta: buildMeta({
      source: "SEC companyfacts",
      confidence: missing.length > 0 ? "medium" : "high",
      missing_fields: missing
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
