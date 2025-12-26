import { spawn } from "node:child_process";

import { loadEnv } from "@/lib/server/env";

const PYTHON = "/home/jim/PLK_KB/.venv/bin/python";
const ROOT = "/home/jim/PLK_KB";

async function runSearch(query: string, topK: number) {
  loadEnv();
  const env = {
    ...process.env,
    PLK_ACTOR: "jim",
    PLK_CONTEXT_ROLES: "SUPERUSER",
    PLK_CONTEXT_CLASSIFICATION: "REFERENCE",
  };

  const script = [
    "-c",
    [
      "import json, sys",
      "from modules.hybrid_search.app.search import hybrid_search",
      "from modules.metadata.app.db import connection_cursor",
      "query = sys.argv[1]",
      "top_k = int(sys.argv[2])",
      "response = hybrid_search(query, top_k=top_k)",
      "query_id = response.get('query_id')",
      "outcome = {'evaluated': 0, 'denied': 0, 'allowed': 0}",
      "with connection_cursor(dict_cursor=True) as cur:",
      "    cur.execute(\"\"\"",
      "        SELECT details FROM audit_log",
      "        WHERE action='AUTHORITY_EVALUATED' AND details->>'query_id' = %s",
      "        ORDER BY audit_id DESC LIMIT 1",
      "    \"\"\", (query_id,))",
      "    row = cur.fetchone()",
      "    if row and row.get('details') and row['details'].get('outcome'):",
      "        outcome = row['details']['outcome']",
      "print(json.dumps({'response': response, 'authority_summary': outcome}))",
    ].join("\n"),
    query,
    String(topK),
  ];

  return new Promise<{ response: any; authority_summary: any }>((resolve, reject) => {
    const proc = spawn(PYTHON, script, { cwd: ROOT, env });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });
    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });
    proc.on("error", (err) => {
      reject(new Error(`search failed to start: ${err.message}`));
    });
    proc.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`search failed: ${stderr.trim() || `exit code ${code}`}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout || "{}"));
      } catch (err) {
        reject(new Error("search returned invalid JSON"));
      }
    });
  });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const query = typeof body.query === "string" ? body.query.trim() : "";
  const topK = typeof body.top_k === "number" ? body.top_k : 5;
  if (!query) {
    return Response.json({ error: "query required" }, { status: 400 });
  }
  try {
    const result = await runSearch(query, topK);
    return Response.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "search failed";
    return Response.json({ error: message }, { status: 500 });
  }
}
