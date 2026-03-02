export interface FredConfig {
  apiKey: string;
  timeoutMs: number;
  minIntervalMs: number;
  maxRetries: number;
  cacheDir: string;
  cacheTtlMsMetadata: number;
  cacheTtlMsObservations: number;
}

function parsePositiveInt(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return Math.floor(parsed);
}

export function loadConfig(): FredConfig {
  const apiKey = process.env.FRED_API_KEY?.trim();
  if (!apiKey) {
    throw new Error("FRED_API_KEY is required for free-fed-fred MCP");
  }

  return {
    apiKey,
    timeoutMs: parsePositiveInt(process.env.FRED_TIMEOUT_MS, 15000),
    minIntervalMs: parsePositiveInt(process.env.FRED_MIN_INTERVAL_MS, 250),
    maxRetries: parsePositiveInt(process.env.FRED_MAX_RETRIES, 2),
    cacheDir: process.env.FRED_CACHE_DIR?.trim() || ".cache/free-fed-fred",
    cacheTtlMsMetadata: parsePositiveInt(process.env.FRED_CACHE_TTL_METADATA_MS, 24 * 60 * 60 * 1000),
    cacheTtlMsObservations: parsePositiveInt(process.env.FRED_CACHE_TTL_OBSERVATIONS_MS, 60 * 60 * 1000)
  };
}
