import type { NextConfig } from "next"

function normalizeBackendUrl(raw: string | undefined): string {
  const url = (raw || "http://localhost:8000").trim()
  if (url.startsWith("http://") || url.startsWith("https://")) return url
  // Auto-add https:// if user forgot the scheme
  return `https://${url}`
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
