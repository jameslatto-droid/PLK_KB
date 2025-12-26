import { spawn } from "node:child_process";
import path from "node:path";

import { loadEnv } from "@/lib/server/env";

const DEFAULT_ROOT = path.resolve(process.cwd(), "..", "..");
const ROOT = process.env.PLK_ROOT || DEFAULT_ROOT;
const PYTHON = process.env.PLK_PYTHON || path.join(ROOT, ".venv", "bin", "python");
const MAX_OUTPUT_BYTES = 500_000;
const MAX_MS = 30_000;

function runPython(script: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const proc = spawn(PYTHON, script, { cwd: ROOT, env: process.env });
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      proc.kill("SIGKILL");
      reject(new Error("python execution timed out"));
    }, MAX_MS);
    proc.stdout.on("data", (d) => {
      stdout += d.toString();
      if (stdout.length > MAX_OUTPUT_BYTES) {
        proc.kill("SIGKILL");
        reject(new Error("python output exceeded limit"));
      }
    });
    proc.stderr.on("data", (d) => {
      stderr += d.toString();
      if (stderr.length > MAX_OUTPUT_BYTES) {
        proc.kill("SIGKILL");
        reject(new Error("python error output exceeded limit"));
      }
    });
    proc.on("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });
    proc.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        reject(new Error(stderr || `python exited ${code}`));
      } else {
        resolve(stdout.trim());
      }
    });
  });
}

export async function GET() {
  loadEnv();
  const script = [
    "-c",
    [
      "import json",
      "from modules.metadata.app.db import connection_cursor",
      "with connection_cursor(dict_cursor=True) as cur:",
      "    cur.execute(\"\"\"",
      "        SELECT",
      "            a.artefact_id,",
      "            a.version_id,",
      "            a.artefact_type,",
      "            a.storage_path,",
      "            a.created_at,",
      "            dv.document_id,",
      "            dv.version_label,",
      "            d.title,",
      "            d.document_type,",
      "            d.authority_level,",
      "            d.project_code,",
      "            (SELECT COUNT(*) FROM chunks c WHERE c.artefact_id = a.artefact_id) AS chunk_count",
      "        FROM artefacts a",
      "        JOIN document_versions dv ON a.version_id = dv.version_id",
      "        JOIN documents d ON dv.document_id = d.document_id",
      "        ORDER BY a.created_at DESC",
      "    \"\"\")",
      "    rows = [dict(r) for r in cur.fetchall()]",
      "print(json.dumps(rows, default=str))",
    ].join("\n"),
  ];
  try {
    const output = await runPython(script);
    const parsed = output ? JSON.parse(output) : [];
    return Response.json(parsed);
  } catch (err) {
    const message = err instanceof Error ? err.message : "failed to load artefacts";
    return Response.json({ error: message }, { status: 500 });
  }
}
