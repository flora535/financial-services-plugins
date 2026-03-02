export interface SecConfig {
  userAgent: string;
  timeoutMs: number;
  minIntervalMs: number;
  maxRetries: number;
  cacheDir: string;
}

function parsePositiveInt(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return Math.floor(parsed);
}

export function loadConfig(): SecConfig {
  const userAgent = process.env.SEC_USER_AGENT?.trim();
  if (!userAgent) {
    throw new Error("SEC_USER_AGENT is required for SEC EDGAR fair-access compliance");
  }

  return {
    userAgent,
    timeoutMs: parsePositiveInt(process.env.SEC_TIMEOUT_MS, 15000),
    minIntervalMs: parsePositiveInt(process.env.SEC_MIN_INTERVAL_MS, 250),
    maxRetries: parsePositiveInt(process.env.SEC_MAX_RETRIES, 1),
    cacheDir: process.env.SEC_CACHE_DIR?.trim() || ".cache/sec-edgar"
  };
}
