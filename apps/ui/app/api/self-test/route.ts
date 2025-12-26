import { getSelfTest, startSelfTest } from "@/lib/server/selfTestRunner";

export async function POST() {
  const run = startSelfTest();
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
