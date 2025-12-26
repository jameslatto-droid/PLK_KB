import { spawn } from "node:child_process";
import path from "node:path";

import { loadEnv } from "@/lib/server/env";

const DEFAULT_ROOT = path.resolve(process.cwd(), "..", "..");
const ROOT = process.env.PLK_ROOT || DEFAULT_ROOT;
const PYTHON = process.env.PLK_PYTHON || path.join(ROOT, ".venv", "bin", "python");
const MAX_OUTPUT_BYTES = 500_000;
const MAX_MS = 30_000;

type ContextPayload = {
  actor?: string;
  roles?: string[];
  classification?: string;
};

async function runSearch(query: string, topK: number, context?: ContextPayload) {
  loadEnv();
  const env = {
    ...process.env,
    PLK_ACTOR: context?.actor ?? "jim",
    PLK_CONTEXT_ROLES: Array.isArray(context?.roles) && context?.roles?.length
      ? context?.roles.join(",")
      : "SUPERUSER",
    PLK_CONTEXT_CLASSIFICATION: context?.classification ?? "REFERENCE",
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
    const timer = setTimeout(() => {
      proc.kill("SIGKILL");
      reject(new Error("search failed: python execution timed out"));
    }, MAX_MS);
    proc.stdout.on("data", (data) => {
      stdout += data.toString();
      if (stdout.length > MAX_OUTPUT_BYTES) {
        proc.kill("SIGKILL");
        reject(new Error("search failed: python output exceeded limit"));
      }
    });
    proc.stderr.on("data", (data) => {
      stderr += data.toString();
      if (stderr.length > MAX_OUTPUT_BYTES) {
        proc.kill("SIGKILL");
        reject(new Error("search failed: python error output exceeded limit"));
      }
    });
    proc.on("error", (err) => {
      clearTimeout(timer);
      reject(new Error(`search failed to start: ${err.message}`));
    });
    proc.on("close", (code) => {
      clearTimeout(timer);
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
  const context = (body.context ?? {}) as ContextPayload;
  if (!query) {
    return Response.json({ error: "query required" }, { status: 400 });
  }
  try {
    const result = await runSearch(query, topK, context);
    return Response.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "search failed";
    return Response.json({ error: message }, { status: 500 });
  }
}
