import { spawn } from "node:child_process";
import path from "node:path";

import { loadEnv } from "@/lib/server/env";

const DEFAULT_ROOT = path.resolve(process.cwd(), "..", "..");
const ROOT = process.env.PLK_ROOT || DEFAULT_ROOT;
const PYTHON = process.env.PLK_PYTHON || path.join(ROOT, ".venv", "bin", "python");
const MAX_OUTPUT_BYTES = 500_000;
const MAX_MS = 30_000;

type AuditQueryParams = {
  actor?: string;
  start?: string;
  end?: string;
  decision?: "ALLOW" | "DENY";
  page: number;
  limit: number;
};

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

export async function GET(request: Request) {
  loadEnv();

  const { searchParams } = new URL(request.url);
  const page = Math.max(parseInt(searchParams.get("page") || "1", 10), 1);
  const limit = Math.min(Math.max(parseInt(searchParams.get("limit") || "50", 10), 1), 200);

  const params: AuditQueryParams = {
    actor: searchParams.get("actor") || undefined,
    start: searchParams.get("start") || undefined,
    end: searchParams.get("end") || undefined,
    decision: (searchParams.get("decision") as "ALLOW" | "DENY" | null) || undefined,
    page,
    limit,
  };

  const script = [
    "-c",
    [
      "import json, sys",
      "from modules.metadata.app.db import connection_cursor",
      "params = json.loads(sys.argv[1])",
      "actor = params.get('actor')",
      "start = params.get('start')",
      "end = params.get('end')",
      "decision = params.get('decision')",
      "page = int(params.get('page', 1))",
      "limit = int(params.get('limit', 50))",
      "offset = (page - 1) * limit",
      "where = []",
      "values = []",
      "if actor:",
      "    where.append(\"actor = %s\")",
      "    values.append(actor)",
      "if start:",
      "    where.append(\"created_at >= %s\")",
      "    values.append(start)",
      "if end:",
      "    where.append(\"created_at <= %s\")",
      "    values.append(end)",
      "if decision in ('ALLOW', 'DENY'):",
      "    # audit.details is expected to contain decision: {decision: ALLOW|DENY, reasons: [...]}",
      "    where.append(\"details->'decision'->>'decision' = %s\")",
      "    values.append(decision)",
      "where_clause = f\" WHERE {' AND '.join(where)}\" if where else \"\"",
      "count_query = f\"SELECT COUNT(*) AS count FROM audit_log{where_clause}\"",
      "data_query = f\"\"\"",
      "SELECT",
      "    audit_id,",
      "    actor,",
      "    action,",
      "    document_id,",
      "    version_id,",
      "    model_version,",
      "    index_version,",
      "    details,",
      "    created_at",
      "FROM audit_log",
      "{where_clause}",
      "ORDER BY created_at DESC",
      "LIMIT %s OFFSET %s",
      "\"\"\"",
      "with connection_cursor(dict_cursor=True) as cur:",
      "    cur.execute(count_query, values)",
      "    total = int(cur.fetchone().get('count', 0))",
      "    cur.execute(data_query, values + [limit, offset])",
      "    entries = [dict(r) for r in cur.fetchall()]",
      "    cur.execute(\"SELECT DISTINCT actor FROM audit_log ORDER BY actor\")",
      "    actors = [r['actor'] for r in cur.fetchall()]",
      "print(json.dumps({'entries': entries, 'total': total, 'page': page, 'limit': limit, 'actors': actors}, default=str))",
    ].join("\n"),
    JSON.stringify(params),
  ];

  try {
    const output = await runPython(script);
    const parsed = output ? JSON.parse(output) : { entries: [], total: 0, actors: [] };
    return Response.json(parsed);
  } catch (err) {
    const message = err instanceof Error ? err.message : "failed to load audit log";
    return Response.json({ error: message }, { status: 500 });
  }
}
