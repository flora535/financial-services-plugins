import type { CallToolResult } from "@modelcontextprotocol/server";
import { FilingSectionInput, buildMeta } from "../types.js";
import type { SecClient } from "../sec-client.js";

const SECTION_HINTS: Record<string, string[]> = {
  "md&a": ["management's discussion", "management discussion"],
  "risk_factors": ["risk factors"],
  "debt_note": ["debt", "long-term debt", "notes payable"],
  "segment_note": ["segment", "reportable segments"]
};

function extractSnippet(html: string, needles: string[]): string {
  const lower = html.toLowerCase();
  for (const needle of needles) {
    const idx = lower.indexOf(needle);
    if (idx >= 0) {
      const start = Math.max(0, idx - 350);
      const end = Math.min(html.length, idx + 1200);
      return html.slice(start, end).replace(/\s+/g, " ").trim();
    }
  }
  return "";
}

export async function getFilingSectionTool(client: SecClient, input: unknown): Promise<CallToolResult> {
  const parsed = FilingSectionInput.safeParse(input);
  if (!parsed.success) {
    return {
      isError: true,
      content: [{ type: "text", text: `Invalid input: ${parsed.error.message}` }]
    };
  }

  const { cik, accession, section } = parsed.data;
  const submissions = await client.getSubmissions(cik);
  const recent = submissions.filings?.recent;

  if (!recent) {
    return {
      isError: true,
      content: [{ type: "text", text: "No recent filings found in SEC submissions" }]
    };
  }

  const idx = recent.accessionNumber.findIndex((a) => a === accession);
  if (idx < 0) {
    return {
      isError: true,
      content: [{ type: "text", text: `Accession not found in recent filings: ${accession}` }]
    };
  }

  const primaryDocument = recent.primaryDocument[idx];
  const html = await client.getPrimaryDocumentHtml(cik, accession, primaryDocument);
  const snippet = extractSnippet(html, SECTION_HINTS[section]);

  const output = {
    cik,
    accession,
    section,
    sectionText: snippet || "",
    missingFields: snippet ? [] : [section],
    meta: buildMeta({
      source: "SEC filing primary document",
      confidence: snippet ? "medium" : "low",
      missing_fields: snippet ? [] : [section]
    })
  };

  return {
    content: [{ type: "text", text: JSON.stringify(output) }],
    structuredContent: output
  };
}
