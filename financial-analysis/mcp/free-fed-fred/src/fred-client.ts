import { setTimeout as sleep } from "node:timers/promises";
import { FileCache } from "./cache.js";
import type { FredConfig } from "./config.js";

type QueryValue = string | number | undefined;

interface FredErrorPayload {
  error_code?: number;
  error_message?: string;
}

interface SearchSeriesParams {
  search_text: string;
  limit?: number;
  offset?: number;
  order_by?: string;
  sort_order?: "asc" | "desc";
  filter_variable?: string;
  filter_value?: string;
  realtime_start?: string;
  realtime_end?: string;
}

interface SeriesParams {
  series_id: string;
  realtime_start?: string;
  realtime_end?: string;
}

interface ObservationParams {
  series_id: string;
  observation_start?: string;
  observation_end?: string;
  realtime_start?: string;
  realtime_end?: string;
  frequency?: string;
  units?: string;
  aggregation_method?: string;
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

interface VintageParams {
  series_id: string;
  realtime_start?: string;
  realtime_end?: string;
  limit?: number;
  offset?: number;
}

interface ReleaseObservationParams {
  release_id: number;
  series_id?: string;
  observation_start?: string;
  observation_end?: string;
  realtime_start?: string;
  realtime_end?: string;
  units?: string;
  frequency?: string;
  aggregation_method?: string;
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

function buildQuery(params: Record<string, QueryValue>): URLSearchParams {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) {
      continue;
    }
    query.set(key, String(value));
  }
  return query;
}

export class FredClient {
  private readonly baseUrl = "https://api.stlouisfed.org/fred";
  private lastRequestAt = 0;

  constructor(
    private readonly config: FredConfig,
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

  private async fetchJson<T>(
    endpointPath: string,
    params: Record<string, QueryValue>,
    ttlMs: number
  ): Promise<T> {
    const query = buildQuery({
      ...params,
      api_key: this.config.apiKey,
      file_type: "json"
    });
    const url = `${this.baseUrl}${endpointPath}?${query.toString()}`;

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
          headers: { Accept: "application/json" }
        });
        clearTimeout(timeout);

        if (!response.ok) {
          throw new Error(`FRED request failed (${response.status}) for ${endpointPath}`);
        }

        const payload = (await response.json()) as T & FredErrorPayload;
        if (payload.error_code || payload.error_message) {
          throw new Error(
            `FRED API error (${payload.error_code ?? "unknown"}): ${payload.error_message ?? "unknown"}`
          );
        }

        await this.cache.set(url, payload, ttlMs);
        return payload;
      } catch (error) {
        lastError = error;
      }
    }

    throw new Error(`FRED request failed after retries for ${endpointPath}: ${String(lastError)}`);
  }

  async searchSeries(params: SearchSeriesParams): Promise<Record<string, unknown>> {
    return this.fetchJson<Record<string, unknown>>(
      "/series/search",
      params,
      this.config.cacheTtlMsMetadata
    );
  }

  async getSeries(params: SeriesParams): Promise<Record<string, unknown>> {
    return this.fetchJson<Record<string, unknown>>(
      "/series",
      params,
      this.config.cacheTtlMsMetadata
    );
  }

  async getObservations(params: ObservationParams): Promise<Record<string, unknown>> {
    return this.fetchJson<Record<string, unknown>>(
      "/series/observations",
      params,
      this.config.cacheTtlMsObservations
    );
  }

  async getVintageDates(params: VintageParams): Promise<Record<string, unknown>> {
    return this.fetchJson<Record<string, unknown>>(
      "/series/vintagedates",
      params,
      this.config.cacheTtlMsMetadata
    );
  }

  async getReleaseObservations(params: ReleaseObservationParams): Promise<Record<string, unknown>> {
    return this.fetchJson<Record<string, unknown>>(
      "/release/observations",
      params,
      this.config.cacheTtlMsObservations
    );
  }
}
