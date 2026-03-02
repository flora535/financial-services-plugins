import { setTimeout as sleep } from "node:timers/promises";
import { FileCache } from "./cache.js";
import type { SecConfig } from "./config.js";

function normalizeCik(cik: string): string {
  const digits = cik.replace(/\D/g, "");
  return digits.padStart(10, "0");
}

interface RecentFilings {
  accessionNumber: string[];
  filingDate: string[];
  reportDate: string[];
  form: string[];
  primaryDocument: string[];
}

interface SubmissionsResponse {
  cik: string;
  name: string;
  tickers?: string[];
  sic?: string;
  fiscalYearEnd?: string;
  filings?: { recent?: RecentFilings };
}

export class SecClient {
  private lastRequestAt = 0;

  constructor(
    private readonly config: SecConfig,
    private readonly cache: FileCache
  ) {}

  private async rateGate(): Promise<void> {
    const now = Date.now();
    const waitMs = this.config.minIntervalMs - (now - this.lastRequestAt);
    if (waitMs > 0) {
      await sleep(waitMs);
    }
    this.lastRequestAt = Date.now();
  }

  private async fetchJson<T>(url: string): Promise<T> {
    const cached = await this.cache.get<T>(url);
    if (cached) {
      return cached;
    }

    let lastError: unknown;
    for (let attempt = 0; attempt <= this.config.maxRetries; attempt += 1) {
      try {
        await this.rateGate();
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.config.timeoutMs);

        const response = await fetch(url, {
          signal: controller.signal,
          headers: {
            "User-Agent": this.config.userAgent,
            "Accept": "application/json"
          }
        });
        clearTimeout(timeout);

        if (!response.ok) {
          throw new Error(`SEC request failed (${response.status}) for ${url}`);
        }

        const payload = await response.json() as T;
        await this.cache.set(url, payload);
        return payload;
      } catch (error) {
        lastError = error;
      }
    }

    throw new Error(`SEC request failed after retries: ${String(lastError)}`);
  }

  private async fetchText(url: string): Promise<string> {
    let lastError: unknown;
    for (let attempt = 0; attempt <= this.config.maxRetries; attempt += 1) {
      try {
        await this.rateGate();
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.config.timeoutMs);

        const response = await fetch(url, {
          signal: controller.signal,
          headers: {
            "User-Agent": this.config.userAgent,
            "Accept": "text/html,application/xhtml+xml"
          }
        });
        clearTimeout(timeout);

        if (!response.ok) {
          throw new Error(`SEC request failed (${response.status}) for ${url}`);
        }

        return await response.text();
      } catch (error) {
        lastError = error;
      }
    }

    throw new Error(`SEC text request failed after retries: ${String(lastError)}`);
  }

  async getTickerDirectory(): Promise<Array<{ cik: string; ticker: string; title: string }>> {
    const payload = await this.fetchJson<Record<string, { cik_str: number; ticker: string; title: string }>>(
      "https://www.sec.gov/files/company_tickers.json"
    );

    return Object.values(payload).map((row) => ({
      cik: normalizeCik(String(row.cik_str)),
      ticker: row.ticker,
      title: row.title
    }));
  }

  async getSubmissions(cik: string): Promise<SubmissionsResponse> {
    const normalized = normalizeCik(cik);
    return this.fetchJson<SubmissionsResponse>(`https://data.sec.gov/submissions/CIK${normalized}.json`);
  }

  async getCompanyFacts(cik: string): Promise<Record<string, unknown>> {
    const normalized = normalizeCik(cik);
    return this.fetchJson<Record<string, unknown>>(`https://data.sec.gov/api/xbrl/companyfacts/CIK${normalized}.json`);
  }

  async getPrimaryDocumentHtml(cik: string, accession: string, primaryDocument: string): Promise<string> {
    const normalized = normalizeCik(cik);
    const cleanAccession = accession.replace(/-/g, "");
    const url = `https://www.sec.gov/Archives/edgar/data/${Number(normalized)}/${cleanAccession}/${primaryDocument}`;
    return this.fetchText(url);
  }
}
