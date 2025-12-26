import fs from "node:fs";
import path from "node:path";

type EnvMap = Record<string, string>;

const ENV_FILES = [
  path.resolve(process.cwd(), "..", "..", "env", ".env"),
  path.resolve(process.cwd(), "..", "..", "ops", "docker", ".env"),
];

function parseEnvFile(contents: string): EnvMap {
  const result: EnvMap = {};
  for (const line of contents.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("=");
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    const value = trimmed.slice(idx + 1).trim();
    if (!key) continue;
    result[key] = value.replace(/^"|"$/g, "");
  }
  return result;
}

export function loadEnv(): EnvMap {
  const loaded: EnvMap = {};
  for (const envPath of ENV_FILES) {
    if (!fs.existsSync(envPath)) continue;
    const contents = fs.readFileSync(envPath, "utf-8");
    const parsed = parseEnvFile(contents);
    for (const [key, value] of Object.entries(parsed)) {
      if (!(key in process.env)) {
        process.env[key] = value;
      }
      loaded[key] = process.env[key] ?? value;
    }
  }
  return loaded;
}
