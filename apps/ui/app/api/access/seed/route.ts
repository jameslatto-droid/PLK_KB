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

export async function POST(request: Request) {
  await request.json().catch(() => ({}));
  loadEnv();
  const script = [
    "-c",
    [
      "import json",
      "from modules.metadata.app.db import connection_cursor",
      "",
      "def ensure_rule(cur, document_id, allowed_roles, classification):",
      "    cur.execute(\"\"\"",
      "        SELECT rule_id, allowed_roles, classification",
      "        FROM access_rules",
      "        WHERE document_id = %s",
      "    \"\"\", (document_id,))",
      "    rows = cur.fetchall()",
      "    for row in rows:",
      "        roles = set(row['allowed_roles'] or [])",
      "        if set(allowed_roles).issubset(roles) and (row['classification'] or None) == classification:",
      "            return False",
      "    cur.execute(",
      "        \"\"\"",
      "        INSERT INTO access_rules (document_id, project_code, discipline, classification, commercial_sensitivity, allowed_roles)",
      "        VALUES (%s, NULL, NULL, %s, NULL, %s)",
      "        \"\"\", (document_id, classification, allowed_roles)",
      "    )",
      "    return True",
      "",
      "with connection_cursor(dict_cursor=True) as cur:",
      "    cur.execute(\"SELECT document_id FROM documents\")",
      "    docs = [r['document_id'] for r in cur.fetchall()]",
      "    created_super = 0",
      "    created_user = 0",
      "    for doc_id in docs:",
      "        if ensure_rule(cur, doc_id, ['SUPERUSER'], None):",
      "            created_super += 1",
      "        if ensure_rule(cur, doc_id, ['USER'], 'REFERENCE'):",
      "            created_user += 1",
      "    result = {",
      "        'seeded_superuser': created_super,",
      "        'seeded_user': created_user,",
      "        'documents_seen': len(docs)",
      "    }",
      "print(json.dumps(result, default=str))",
    ].join("\n"),
  ];
  try {
    const output = await runPython(script);
    const parsed = output ? JSON.parse(output) : {};
    return Response.json(parsed);
  } catch (err) {
    const message = err instanceof Error ? err.message : "failed to seed rules";
    return Response.json({ error: message }, { status: 500 });
  }
}
