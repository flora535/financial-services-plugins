import { z } from "zod";

export const ResolveCompanyInput = z.object({
  ticker: z.string().trim().min(1).optional(),
  cik: z.string().trim().min(1).optional()
}).refine((v: { ticker?: string; cik?: string }) => Boolean(v.ticker || v.cik), {
  message: "Provide ticker or cik"
});

export const ListFilingsInput = z.object({
  cik: z.string().trim().min(1),
  forms: z.array(z.string().trim().min(1)).default(["10-K", "10-Q"]),
  limit: z.number().int().positive().max(50).default(10)
});

export const CompanyFactsInput = z.object({
  cik: z.string().trim().min(1),
  taxonomy: z.enum(["us-gaap", "dei", "both"]).default("both"),
  metrics: z.array(z.string().trim().min(1)).optional()
});

export const FinancialStatementsInput = z.object({
  cik: z.string().trim().min(1),
  accession: z.string().trim().min(1),
  periodMode: z.enum(["annual", "quarterly"]).default("annual"),
  normalize: z.boolean().default(true)
});

export const FilingSectionInput = z.object({
  cik: z.string().trim().min(1),
  accession: z.string().trim().min(1),
  section: z.enum(["md&a", "risk_factors", "debt_note", "segment_note"])
});

export interface SourceMeta {
  source: string;
  as_of: string;
  freshness: "live" | "eod" | "delayed" | "stale";
  confidence: "high" | "medium" | "low";
  fallback_used: boolean;
  missing_fields: string[];
}

export function buildMeta(partial?: Partial<SourceMeta>): SourceMeta {
  return {
    source: partial?.source || "SEC EDGAR",
    as_of: partial?.as_of || new Date().toISOString(),
    freshness: partial?.freshness || "eod",
    confidence: partial?.confidence || "high",
    fallback_used: partial?.fallback_used || false,
    missing_fields: partial?.missing_fields || []
  };
}
