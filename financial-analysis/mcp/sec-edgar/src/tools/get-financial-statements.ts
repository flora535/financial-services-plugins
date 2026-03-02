import type { CallToolResult } from "@modelcontextprotocol/server";
import { FinancialStatementsInput, buildMeta } from "../types.js";
import type { SecClient } from "../sec-client.js";
import { mapFinancialStatements } from "../mappers/statements.js";

export async function getFinancialStatementsTool(client: SecClient, input: unknown): Promise<CallToolResult> {
  const parsed = FinancialStatementsInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const { cik, accession, periodMode } = parsed.data;
  const companyFacts = await client.getCompanyFacts(cik);
  const mapped = mapFinancialStatements(companyFacts);

  const output = {
    cik,
    accession,
    periodMode,
    incomeStatement: mapped.incomeStatement,
    balanceSheet: mapped.balanceSheet,
    cashFlow: mapped.cashFlow,
    missingFields: mapped.missingFields,
    meta: buildMeta({
      source: "SEC companyfacts (normalized)",
      confidence: mapped.missingFields.length > 0 ? "medium" : "high",
      missing_fields: mapped.missingFields
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
