import path from "node:path";

import { getIngest, startIngest, type UserContextInput } from "@/lib/server/ingestRunner";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const defaultRoot = path.join(process.env.HOME ?? "/home/jim", "PLK_KB/tmp/testdata");
  const rawRoot = typeof body.rootPath === "string" && body.rootPath.trim().length > 0
    ? body.rootPath.trim()
    : defaultRoot;

  const home = process.env.HOME ?? "/home/jim";
  const rootPath = path.resolve(
    rawRoot
      .replace(/^~(?=\/|$)/, home)
      .replace(/\$\{HOME\}/g, home)
  );
  const ctx = body.context as Partial<UserContextInput> | undefined;
  const context: UserContextInput = {
    actor: ctx?.actor ?? "jim",
    roles: Array.isArray(ctx?.roles) && ctx?.roles.length ? ctx!.roles : ["SUPERUSER"],
    classification: ctx?.classification ?? "REFERENCE",
  };
  const job = startIngest(rootPath, context);
  return Response.json(job);
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const jobId = searchParams.get("job_id");
  if (!jobId) {
    return Response.json({ error: "job_id required" }, { status: 400 });
  }
  const job = getIngest(jobId);
  if (!job) {
    return Response.json({ error: "job_id not found" }, { status: 404 });
  }
  return Response.json(job);
}
