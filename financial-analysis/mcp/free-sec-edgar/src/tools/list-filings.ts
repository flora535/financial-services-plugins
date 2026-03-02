import { ListFilingsInput, buildMeta } from "../types.js";
import type { SecClient } from "../sec-client.js";

export async function listFilingsTool(client: SecClient, input: unknown): Promise<any> {
  const parsed = ListFilingsInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const { cik, forms, limit } = parsed.data;
  const submissions = await client.getSubmissions(cik);
  const recent = submissions.filings?.recent;
  if (!recent) {
    const output = {
      filings: [],
      meta: buildMeta({ confidence: "low", missing_fields: ["filings.recent"] })
    };
    return {
      content: [{ type: "text", text: JSON.stringify(output) }],
      structuredContent: output
    };
  }

  const filings = recent.form
    .map((form, idx) => ({
      form,
      accession: recent.accessionNumber[idx],
      filingDate: recent.filingDate[idx],
      reportDate: recent.reportDate[idx] || null,
      primaryDocument: recent.primaryDocument[idx] || null,
      primaryDocUrl: recent.primaryDocument[idx]
        ? `https://www.sec.gov/Archives/edgar/data/${Number(cik)}/${recent.accessionNumber[idx].replace(/-/g, "")}/${recent.primaryDocument[idx]}`
        : null
    }))
    .filter((row) => forms.includes(row.form))
    .slice(0, limit);

  const output = {
    filings,
    meta: buildMeta({
      source: "SEC submissions recent filings",
      as_of: filings[0]?.filingDate || new Date().toISOString().slice(0, 10)
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
