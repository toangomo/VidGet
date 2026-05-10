"use client"

import { useState } from "react"
import Link from "next/link"
import {
  Download,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Loader2,
  ArrowLeft,
} from "lucide-react"

// ── Types ────────────────────────────────────────────────────────────────

type Status = "pending" | "downloading" | "done" | "error"

interface Job {
  localId: string
  url: string
  platform: string
  title: string
  percent: number
  speed: string
  status: Status
  downloadUrl?: string
}

// ── Constants ─────────────────────────────────────────────────────────────

const PLATFORMS = [
  { name: "YouTube",    color: "#FF0000" },
  { name: "TikTok",     color: "#010101" },
  { name: "Facebook",   color: "#1877F2" },
  { name: "Instagram",  color: "#C13584" },
  { name: "Twitter/X",  color: "#1DA1F2" },
  { name: "Khác",       color: "#6B7280" },
]

// ── Page ──────────────────────────────────────────────────────────────────

export default function DownloadPage() {
  const [platform, setPlatform] = useState("YouTube")
  const [url, setUrl]           = useState("")
  const [jobs, setJobs]         = useState<Job[]>([])

  function updateJob(localId: string, patch: Partial<Job>) {
    setJobs((prev) => prev.map((j) => (j.localId === localId ? { ...j, ...patch } : j)))
  }

  async function runDownload(localId: string, jobUrl: string, jobPlatform: string) {
    try {
      const res = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: jobUrl, platform: jobPlatform }),
      })
      if (!res.ok) throw new Error("Server error")
      const { job_id } = await res.json()

      updateJob(localId, { status: "downloading" })

      const es = new EventSource(`/api/progress/${job_id}`)

      es.onmessage = (e) => {
        const d = JSON.parse(e.data)
        if (d.type === "progress") {
          updateJob(localId, {
            percent: d.percent ?? 0,
            speed: d.speed ?? "",
            title: d.title || "Đang tải...",
            status: "downloading",
          })
        } else if (d.type === "done") {
          updateJob(localId, {
            status: "done",
            percent: 100,
            title: d.title,
            downloadUrl: `http://localhost:8000/api/file/${job_id}`,
          })
          es.close()
        } else if (d.type === "error") {
          updateJob(localId, { status: "error" })
          es.close()
        }
      }

      es.onerror = () => {
        updateJob(localId, { status: "error" })
        es.close()
      }
    } catch {
      updateJob(localId, { status: "error" })
    }
  }

  function handleDownload() {
    const trimmed = url.trim()
    if (!trimmed) return
    setUrl("")

    const localId = crypto.randomUUID()
    setJobs((prev) => [
      {
        localId,
        url: trimmed,
        platform,
        title: "Đang lấy thông tin...",
        percent: 0,
        speed: "",
        status: "pending",
      },
      ...prev,
    ])

    runDownload(localId, trimmed, platform)
  }

  function handleRetry(job: Job) {
    updateJob(job.localId, {
      status: "pending",
      percent: 0,
      speed: "",
      downloadUrl: undefined,
    })
    runDownload(job.localId, job.url, job.platform)
  }

  return (
    <div className="min-h-screen bg-[#07070f] text-white antialiased">

      {/* Navbar */}
      <nav className="h-14 border-b border-white/[0.06] px-6 flex items-center gap-3">
        <Link
          href="/"
          className="text-gray-500 hover:text-white transition-colors p-1 rounded-md hover:bg-white/5"
        >
          <ArrowLeft size={18} />
        </Link>
        <span className="text-lg font-bold tracking-tight">
          Vid<span className="text-violet-400">Get</span>
        </span>
        <span className="text-gray-600 text-sm hidden sm:block">
          Video Downloader
        </span>
      </nav>

      <main className="max-w-2xl mx-auto px-5 py-10">

        {/* Platform tabs */}
        <div className="flex flex-wrap gap-2 mb-5">
          {PLATFORMS.map((p) => (
            <button
              key={p.name}
              onClick={() => setPlatform(p.name)}
              className="px-4 py-1.5 rounded-full text-sm font-medium border transition-all"
              style={
                platform === p.name
                  ? { backgroundColor: p.color, borderColor: p.color, color: "#fff" }
                  : { backgroundColor: "transparent", borderColor: "rgba(255,255,255,0.1)", color: "#9ca3af" }
              }
            >
              {p.name}
            </button>
          ))}
        </div>

        {/* URL input */}
        <div className="flex gap-2 p-1.5 bg-white/[0.05] border border-white/[0.08] rounded-xl mb-8 focus-within:border-violet-500/50 transition-colors">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleDownload()}
            placeholder="Dán link video vào đây…"
            className="flex-1 bg-transparent px-3 py-2.5 text-sm placeholder-gray-600 focus:outline-none"
          />
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm font-semibold transition-colors whitespace-nowrap"
          >
            <Download size={15} />
            Tải xuống
          </button>
        </div>

        {/* Job list */}
        {jobs.length === 0 ? (
          <div className="py-24 text-center">
            <Download size={36} className="mx-auto mb-3 text-white/[0.08]" />
            <p className="text-gray-600 text-sm">
              Dán link video và nhấn <span className="text-gray-400">Tải xuống</span> để bắt đầu
            </p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {jobs.map((job) => (
              <JobRow
                key={job.localId}
                job={job}
                onRetry={() => handleRetry(job)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

// ── JobRow ────────────────────────────────────────────────────────────────

function JobRow({ job, onRetry }: { job: Job; onRetry: () => void }) {
  const color = PLATFORMS.find((p) => p.name === job.platform)?.color ?? "#6B7280"
  const isActive = job.status === "pending" || job.status === "downloading"

  return (
    <div className="flex items-center gap-3 px-4 py-3.5 rounded-xl bg-white/[0.04] border border-white/[0.07] hover:border-white/[0.12] transition-colors">

      {/* Platform badge */}
      <div
        className="w-9 h-9 rounded-lg flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0"
        style={{ backgroundColor: color }}
      >
        {job.platform.slice(0, 2).toUpperCase()}
      </div>

      {/* Title + progress */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-100 truncate">{job.title}</p>

        {job.status === "downloading" && (
          <div className="mt-2">
            <div className="h-[3px] bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-violet-500 rounded-full transition-all duration-500"
                style={{ width: `${job.percent}%` }}
              />
            </div>
            <p className="text-[11px] text-gray-600 mt-1">
              {job.percent.toFixed(0)}%
              {job.speed ? ` · ${job.speed}` : ""}
            </p>
          </div>
        )}

        {job.status === "pending" && (
          <p className="text-[11px] text-gray-600 mt-0.5 flex items-center gap-1">
            <Loader2 size={10} className="animate-spin" />
            Đang chuẩn bị...
          </p>
        )}

        {job.status === "done" && (
          <p className="text-[11px] text-emerald-500 mt-0.5">
            Hoàn thành · Nhấn{" "}
            <span className="text-emerald-400 font-medium">Lưu về</span> để tải file
          </p>
        )}

        {job.status === "error" && (
          <p className="text-[11px] text-red-400 mt-0.5">
            Tải thất bại · Nhấn <span className="font-medium">Thử lại</span>
          </p>
        )}
      </div>

      {/* Spinner / status icon */}
      <div className="flex-shrink-0">
        {isActive     && <Loader2    size={18} className="animate-spin text-violet-400" />}
        {job.status === "done"  && <CheckCircle2 size={18} className="text-emerald-400" />}
        {job.status === "error" && <XCircle      size={18} className="text-red-400" />}
      </div>

      {/* Action buttons */}
      {job.status === "done" && job.downloadUrl && (
        <a
          href={job.downloadUrl}
          download
          className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold transition-colors"
        >
          <Download size={12} /> Lưu về
        </a>
      )}
      {job.status === "error" && (
        <button
          onClick={onRetry}
          className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-orange-600 hover:bg-orange-500 text-xs font-semibold transition-colors"
        >
          <RefreshCw size={12} /> Thử lại
        </button>
      )}
    </div>
  )
}
