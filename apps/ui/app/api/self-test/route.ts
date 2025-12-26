import { getSelfTest, startSelfTest } from "@/lib/server/selfTestRunner";

type ContextPayload = {
  actor?: string;
  roles?: string[];
  classification?: string;
};

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({} as any));
  const context = body?.context as ContextPayload;
  const run = startSelfTest(
    context
      ? {
          actor: context.actor ?? "jim",
          roles: Array.isArray(context.roles) && context.roles.length ? context.roles : ["SUPERUSER"],
          classification: context.classification ?? "REFERENCE",
        }
      : undefined
  );
  return Response.json(run);
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const runId = searchParams.get("run_id");
  if (!runId) {
    return Response.json({ error: "run_id required" }, { status: 400 });
  }
  const run = getSelfTest(runId);
  if (!run) {
    return Response.json({ error: "run_id not found" }, { status: 404 });
  }
  return Response.json(run);
}
