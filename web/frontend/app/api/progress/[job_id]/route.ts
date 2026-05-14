export const runtime = "nodejs"
export const dynamic = "force-dynamic"

function resolveBackend(): string {
  const raw = (process.env.BACKEND_URL || "").trim()
  if (!raw) return "http://localhost:8000"
  const noScheme = raw.replace(/^https?:\/\//, "")
  if (noScheme.includes(".railway.internal")) return `http://${noScheme}`
  return `https://${noScheme}`
}
const BACKEND = resolveBackend()

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ job_id: string }> },
) {
  const { job_id } = await params

  const upstream = await fetch(`${BACKEND}/api/progress/${job_id}`, {
    headers: { Accept: "text/event-stream", "Cache-Control": "no-cache" },
  })

  if (!upstream.ok || !upstream.body) {
    return new Response(
      `data: ${JSON.stringify({ type: "error", message: "Backend unreachable" })}\n\n`,
      { status: 502, headers: { "Content-Type": "text/event-stream" } },
    )
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
      Connection: "keep-alive",
    },
  })
}
