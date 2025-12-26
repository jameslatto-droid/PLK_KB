import { getBackendStatus } from "@/lib/server/status";

export async function GET() {
  const status = await getBackendStatus();
  return Response.json(status);
}
