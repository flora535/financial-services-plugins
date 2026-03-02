import { createHash } from "node:crypto";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";

interface CacheEnvelope<T> {
  expiresAt: number;
  value: T;
}

export class FileCache {
  constructor(private readonly cacheDir: string) {}

  private keyToPath(key: string): string {
    const digest = createHash("sha256").update(key).digest("hex");
    return path.join(this.cacheDir, `${digest}.json`);
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const filePath = this.keyToPath(key);
      const raw = await readFile(filePath, "utf8");
      const envelope = JSON.parse(raw) as CacheEnvelope<T>;
      if (Date.now() > envelope.expiresAt) {
        await rm(filePath, { force: true });
        return null;
      }
      return envelope.value;
    } catch {
      return null;
    }
  }

  async set<T>(key: string, value: T, ttlMs: number): Promise<void> {
    await mkdir(this.cacheDir, { recursive: true });
    const filePath = this.keyToPath(key);
    const envelope: CacheEnvelope<T> = {
      expiresAt: Date.now() + ttlMs,
      value
    };
    await writeFile(filePath, JSON.stringify(envelope), "utf8");
  }
}
