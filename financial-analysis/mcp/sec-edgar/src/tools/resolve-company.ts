import { ResolveCompanyInput, buildMeta } from "../types.js";
import type { SecClient } from "../sec-client.js";

export async function resolveCompanyTool(client: SecClient, input: unknown): Promise<any> {
  const parsed = ResolveCompanyInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const { ticker, cik } = parsed.data;
  if (cik) {
    const submissions = await client.getSubmissions(cik);
    const output = {
      cik: submissions.cik,
      ticker: submissions.tickers?.[0] ?? ticker ?? null,
      name: submissions.name,
      sic: submissions.sic ?? null,
      fiscalYearEnd: submissions.fiscalYearEnd ?? null,
      meta: buildMeta({ source: "SEC submissions" })
    };

    return {
      content: [{ type: "text", text: JSON.stringify(output) }],
      structuredContent: output
    };
  }

  const directory = await client.getTickerDirectory();
  const match = directory.find((row) => row.ticker.toUpperCase() === ticker!.toUpperCase());
  if (!match) {
    return {
      isError: true,
      content: [{ type: "text", text: `Ticker not found in SEC directory: ${ticker}` }]
    };
  }

  const output = {
    cik: match.cik,
    ticker: match.ticker,
    name: match.title,
    sic: null,
    fiscalYearEnd: null,
    meta: buildMeta({ source: "SEC company_tickers" })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
