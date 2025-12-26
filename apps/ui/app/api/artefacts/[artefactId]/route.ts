import { spawn } from "node:child_process";
import path from "node:path";

import { loadEnv } from "@/lib/server/env";

const DEFAULT_ROOT = path.resolve(process.cwd(), "..", "..");
const ROOT = process.env.PLK_ROOT || DEFAULT_ROOT;
const PYTHON = process.env.PLK_PYTHON || path.join(ROOT, ".venv", "bin", "python");
const MAX_OUTPUT_BYTES = 500_000;
const MAX_MS = 30_000;

function runPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const proc = spawn(PYTHON, args, { cwd: ROOT, env: process.env });
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

export async function GET(_: Request, { params }: { params: { artefactId: string } }) {
  loadEnv();
  const artefactId = params.artefactId;
  const script = [
    "-c",
    [
      "import json, sys",
      "from modules.metadata.app.db import connection_cursor",
      "from modules.indexing.app.opensearch_client import get_client as get_os",
      "from modules.indexing.app.config import settings as os_settings",
      "from modules.vector_indexing.app.qdrant_client import get_client as get_qdr",
      "from modules.vector_indexing.app.config import settings as vec_settings",
      "artefact_id = sys.argv[1]",
      "row = None",
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
      "        WHERE a.artefact_id = %s",
      "    \"\"\", (artefact_id,))",
      "    fetched = cur.fetchone()",
      "    if fetched:",
      "        row = dict(fetched)",
      "if row is None:",
      "    print(json.dumps({'error': 'not_found'}))",
      "    sys.exit(0)",
      "# OpenSearch count",
      "try:",
      "    os_client = get_os()",
      "    os_resp = os_client.count(index=os_settings.index_name, body={'query': {'term': {'artefact_id': artefact_id}}})",
      "    row['opensearch_count'] = os_resp.get('count', 0)",
      "except Exception as exc:",
      "    row['opensearch_error'] = str(exc)",
      "# Qdrant count",
      "try:",
      "    qdr = get_qdr()",
      '    q_count = qdr.count(collection_name=vec_settings.collection_name, count_filter={"must": [{"key": "artefact_id", "match": {"value": artefact_id}}]})',
      "    row['qdrant_count'] = getattr(q_count, 'count', None) or getattr(q_count, 'result', None) or 0",
      "except Exception as exc:",
      "    row['qdrant_error'] = str(exc)",
      "row['last_indexed_at'] = None",
      "print(json.dumps(row, default=str))",
    ].join("\n"),
    artefactId,
  ];
  try {
    const output = await runPython(script);
    if (!output) return Response.json({ error: "empty" }, { status: 500 });
    const parsed = JSON.parse(output);
    if (parsed?.error === "not_found") {
      return Response.json({ error: "not_found" }, { status: 404 });
    }
    return Response.json(parsed);
  } catch (err) {
    const message = err instanceof Error ? err.message : "failed to load artefact";
    return Response.json({ error: message }, { status: 500 });
  }
}
