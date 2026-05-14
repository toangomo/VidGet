"use client"

import { useState } from "react"
import Link from "next/link"
import { Download, RefreshCw, CheckCircle2, XCircle, ArrowLeft, Square } from "lucide-react"

// ── Types ────────────────────────────────────────────────────────────────────

type Status = "pending" | "downloading" | "done" | "error"

interface Job {
  localId: string
  jobId?: string
  url: string
  platform: string
  title: string
  percent: number
  speed: string
  status: Status
  downloadUrl?: string
  errorMsg?: string
}

// ── Constants ─────────────────────────────────────────────────────────────────

const PLATFORMS = [
  { name: "YouTube",   color: "#FF4444" },
  { name: "TikTok",    color: "#00d4d4" },
  { name: "Facebook",  color: "#4090f7" },
  { name: "Instagram", color: "#e1306c" },
  { name: "Twitter/X", color: "#1d9bf0" },
  { name: "Khác",      color: "#a78bfa" },
]

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DownloadPage() {
  const [platform, setPlatform] = useState("YouTube")
  const [url, setUrl]           = useState("")
  const [jobs, setJobs]         = useState<Job[]>([])

  function updateJob(localId: string, patch: Partial<Job>) {
    setJobs((prev) => prev.map((j) => (j.localId === localId ? { ...j, ...patch } : j)))
  }

  async function stopDownload(job: Job) {
    if (!job.jobId) {
      updateJob(job.localId, { status: "error", errorMsg: "Đã hủy" })
      return
    }
    await fetch(`/api/cancel/${job.jobId}`, { method: "POST" }).catch(() => null)
    updateJob(job.localId, { status: "error", errorMsg: "Đã hủy tải xuống" })
  }

  async function runDownload(localId: string, jobUrl: string, jobPlatform: string) {
    try {
      const res = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: jobUrl, platform: jobPlatform }),
      })
      if (!res.ok) throw new Error("Server error — kiểm tra BACKEND_URL")
      const { job_id } = await res.json()

      updateJob(localId, { status: "downloading", jobId: job_id })

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
            downloadUrl: `/api/file/${job_id}`,
          })
          es.close()
        } else if (d.type === "error") {
          updateJob(localId, { status: "error", errorMsg: d.message })
          es.close()
        }
      }

      es.onerror = () => {
        updateJob(localId, { status: "error", errorMsg: "Mất kết nối đến server." })
        es.close()
      }
    } catch (err) {
      updateJob(localId, {
        status: "error",
        errorMsg: err instanceof Error ? err.message : "Lỗi không xác định.",
      })
    }
  }

  function handleDownload() {
    const trimmed = url.trim()
    if (!trimmed) return
    setUrl("")
    const localId = crypto.randomUUID()
    setJobs((prev) => [
      { localId, url: trimmed, platform, title: "Đang lấy thông tin...", percent: 0, speed: "", status: "pending" },
      ...prev,
    ])
    runDownload(localId, trimmed, platform)
  }

  function handleRetry(job: Job) {
    updateJob(job.localId, { status: "pending", percent: 0, speed: "", downloadUrl: undefined, errorMsg: undefined, jobId: undefined })
    runDownload(job.localId, job.url, job.platform)
  }

  return (
    <div className="min-h-screen bg-[#05050f] text-white antialiased">

      {/* Ambient glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-violet-700/[0.07] rounded-full blur-[100px]" />
        <div className="absolute top-1/2 -left-40 w-[400px] h-[400px] bg-blue-700/[0.04] rounded-full blur-[120px]" />
      </div>

      {/* Navbar */}
      <nav className="relative z-10 h-14 border-b border-white/[0.05] px-6 flex items-center gap-3 bg-black/30 backdrop-blur-xl">
        <Link
          href="/"
          className="text-gray-500 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-white/5"
        >
          <ArrowLeft size={16} />
        </Link>
        <span className="text-base font-bold tracking-tight">
          Vid<span className="text-violet-400">Get</span>
        </span>
        <div className="h-4 w-px bg-white/[0.08] mx-1" />
        <span className="text-gray-600 text-sm">Tải video miễn phí</span>
      </nav>

      <main className="relative z-10 max-w-2xl mx-auto px-5 pt-10 pb-20">

        {/* Platform selector */}
        <div className="flex flex-wrap gap-2 mb-6">
          {PLATFORMS.map((p) => (
            <button
              key={p.name}
              onClick={() => setPlatform(p.name)}
              className="px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all duration-200"
              style={
                platform === p.name
                  ? {
                      backgroundColor: `${p.color}1a`,
                      borderColor: `${p.color}55`,
                      color: p.color,
                      boxShadow: `0 0 16px ${p.color}22`,
                    }
                  : { backgroundColor: "transparent", borderColor: "rgba(255,255,255,0.07)", color: "#4b5563" }
              }
            >
              {p.name}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-2 p-1.5 mb-8 rounded-2xl border border-white/[0.08] bg-white/[0.03] focus-within:border-violet-500/35 focus-within:bg-violet-500/[0.02] transition-all duration-300">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleDownload()}
            placeholder="Dán link video vào đây…"
            className="flex-1 bg-transparent px-4 py-2.5 text-sm placeholder-gray-700 focus:outline-none"
          />
          <button
            onClick={handleDownload}
            disabled={!url.trim()}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              background: "linear-gradient(135deg, #7c3aed, #6d28d9)",
              boxShadow: url.trim() ? "0 0 24px rgba(124,58,237,0.35)" : "none",
            }}
          >
            <Download size={14} />
            Tải xuống
          </button>
        </div>

        {/* Empty state */}
        {jobs.length === 0 ? (
          <div className="py-32 text-center">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl border border-white/[0.06] bg-white/[0.02] flex items-center justify-center">
              <Download size={22} className="text-white/10" />
            </div>
            <p className="text-gray-700 text-sm">
              Dán link và nhấn <span className="text-gray-500">Tải xuống</span> để bắt đầu
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <JobCard
                key={job.localId}
                job={job}
                onRetry={() => handleRetry(job)}
                onStop={() => stopDownload(job)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

// ── JobCard ───────────────────────────────────────────────────────────────────

function JobCard({ job, onRetry, onStop }: { job: Job; onRetry: () => void; onStop: () => void }) {
  const plat  = PLATFORMS.find((p) => p.name === job.platform)
  const color = plat?.color ?? "#a78bfa"
  const isActive = job.status === "pending" || job.status === "downloading"

  return (
    <div
      className="relative flex items-center gap-3 px-4 py-4 rounded-2xl border transition-all duration-300"
      style={{
        backgroundColor: isActive ? `${color}07` : "rgba(255,255,255,0.02)",
        borderColor: isActive ? `${color}30` : "rgba(255,255,255,0.06)",
      }}
    >
      {/* Left accent stripe */}
      <div
        className="absolute left-0 top-3 bottom-3 w-[3px] rounded-r-full transition-opacity duration-300"
        style={{ backgroundColor: color, opacity: isActive ? 0.9 : 0.3 }}
      />

      {/* Platform badge */}
      <div
        className="ml-2 w-10 h-10 rounded-xl flex items-center justify-center text-[10px] font-bold tracking-wider flex-shrink-0"
        style={{ backgroundColor: `${color}18`, color, border: `1px solid ${color}33` }}
      >
        {job.platform.slice(0, 2).toUpperCase()}
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-100 truncate">{job.title}</p>

        {/* Pending */}
        {job.status === "pending" && (
          <div className="flex items-center gap-2 mt-1.5">
            <div className="flex items-end gap-[3px] h-3">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-[3px] rounded-full animate-bounce-dot"
                  style={{
                    height: "10px",
                    backgroundColor: color,
                    animationDelay: `${i * 0.18}s`,
                  }}
                />
              ))}
            </div>
            <span className="text-[11px] text-gray-600">Đang chuẩn bị...</span>
          </div>
        )}

        {/* Downloading */}
        {job.status === "downloading" && (
          <div className="mt-2 space-y-1.5">
            <div className="relative h-1 bg-white/[0.05] rounded-full overflow-hidden">
              {/* Fill */}
              <div
                className="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${job.percent}%`,
                  background: `linear-gradient(90deg, ${color}88, ${color})`,
                  boxShadow: `0 0 8px ${color}55`,
                }}
              />
              {/* Shimmer sweep */}
              <div
                className="absolute inset-y-0 w-1/3 animate-shimmer"
                style={{
                  background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent)",
                }}
              />
            </div>
            <div className="flex items-center gap-1.5 text-[11px]">
              <span className="font-semibold text-gray-300">{job.percent.toFixed(0)}%</span>
              {job.speed && <><span className="text-gray-700">·</span><span className="text-gray-500">{job.speed}</span></>}
            </div>
          </div>
        )}

        {/* Done */}
        {job.status === "done" && (
          <p className="text-[11px] text-emerald-500/80 mt-0.5">
            Hoàn thành · Nhấn <span className="text-emerald-400 font-medium">Lưu về</span> để lưu file
          </p>
        )}

        {/* Error */}
        {job.status === "error" && (
          <p className="text-[11px] text-red-400/80 mt-0.5 break-words line-clamp-2">
            {job.errorMsg || "Tải thất bại"} · Nhấn <span className="font-medium">Thử lại</span>
          </p>
        )}
      </div>

      {/* Right: status icon */}
      <div className="flex-shrink-0">
        {job.status === "downloading" && (
          <div
            className="w-4 h-4 rounded-full border-2 border-transparent animate-spin"
            style={{ borderTopColor: color, borderRightColor: `${color}40` }}
          />
        )}
        {job.status === "pending" && (
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: color }} />
        )}
        {job.status === "done"  && <CheckCircle2 size={17} className="text-emerald-400" />}
        {job.status === "error" && <XCircle      size={17} className="text-red-400/70" />}
      </div>

      {/* Action buttons */}
      {isActive && (
        <button
          onClick={onStop}
          className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 border border-red-500/20 bg-red-500/[0.08] hover:bg-red-500/[0.15] hover:border-red-500/40 text-red-400"
        >
          <Square size={9} fill="currentColor" />
          Stop
        </button>
      )}

      {job.status === "done" && job.downloadUrl && (
        <a
          href={job.downloadUrl}
          download
          className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 border border-emerald-500/20 bg-emerald-500/[0.08] hover:bg-emerald-500/[0.18] hover:border-emerald-500/35 text-emerald-400"
        >
          <Download size={11} />
          Lưu về
        </a>
      )}

      {job.status === "error" && (
        <button
          onClick={onRetry}
          className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 border border-amber-500/20 bg-amber-500/[0.08] hover:bg-amber-500/[0.16] hover:border-amber-500/35 text-amber-400"
        >
          <RefreshCw size={11} />
          Thử lại
        </button>
      )}
    </div>
  )
}
