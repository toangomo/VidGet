import type { NextConfig } from "next"

function normalizeBackendUrl(raw: string | undefined): string {
  const url = (raw || "http://localhost:8000").trim()
  if (!url || url === "http://localhost:8000") return "http://localhost:8000"
  // Strip any existing scheme then re-add correct one
  const noScheme = url.replace(/^https?:\/\//, "")
  // Private network (.railway.internal) uses plain http
  if (noScheme.includes(".railway.internal")) return `http://${noScheme}`
  // Everything else (public Railway URLs, custom domains) uses https
  return `https://${noScheme}`
}

const BACKEND_URL = normalizeBackendUrl(process.env.BACKEND_URL)

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
