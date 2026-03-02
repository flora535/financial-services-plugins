import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

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
      return JSON.parse(raw) as T;
    } catch {
      return null;
    }
  }

  async set<T>(key: string, value: T): Promise<void> {
    await mkdir(this.cacheDir, { recursive: true });
    const filePath = this.keyToPath(key);
    await writeFile(filePath, JSON.stringify(value), "utf8");
  }
}
