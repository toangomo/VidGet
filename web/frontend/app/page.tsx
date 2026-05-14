"use client"

import { useState } from "react"
import { Download, Zap, Shield, Globe, Sparkles, CheckCircle2, XCircle, RefreshCw, Square } from "lucide-react"

// ── Types ─────────────────────────────────────────────────────────────────────

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

// ── Data ──────────────────────────────────────────────────────────────────────

const PLATFORMS = [
  { name: "YouTube",   color: "#FF4444" },
  { name: "TikTok",    color: "#00d4d4" },
  { name: "Facebook",  color: "#4090f7" },
  { name: "Instagram", color: "#e1306c" },
  { name: "Twitter/X", color: "#1d9bf0" },
  { name: "Khác",      color: "#a78bfa" },
]

const FEATURES = [
  { icon: Zap,      title: "Tải siêu nhanh",      desc: "Tốc độ tải xuống tối đa, không giới hạn băng thông hay hàng chờ." },
  { icon: Globe,    title: "Đa nền tảng",          desc: "YouTube, TikTok, Facebook, Instagram và hàng trăm trang web khác." },
  { icon: Download, title: "Chất lượng cao",       desc: "Tải video 4K, 1080p với âm thanh lossless. Không nén, không mất chất lượng." },
  { icon: Shield,   title: "Bảo mật & Riêng tư",  desc: "Link video xử lý xong là xoá. Dữ liệu của bạn là của bạn." },
]

const STEPS = [
  { n: "01", title: "Sao chép link",    desc: "Copy link video từ YouTube, TikTok, Facebook hay bất kỳ trang nào." },
  { n: "02", title: "Dán & Tải xuống", desc: "Dán link vào ô bên trên, chọn nền tảng rồi nhấn nút Tải xuống." },
  { n: "03", title: "Lưu về máy",      desc: "Video xử lý trên server và trả về ngay để bạn lưu về thiết bị." },
]

// ── Page ──────────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [platform, setPlatform] = useState("YouTube")
  const [url, setUrl]           = useState("")
  const [jobs, setJobs]         = useState<Job[]>([])

  function updateJob(localId: string, patch: Partial<Job>) {
    setJobs((prev) => prev.map((j) => (j.localId === localId ? { ...j, ...patch } : j)))
  }

  async function stopDownload(job: Job) {
    if (job.jobId) await fetch(`/api/cancel/${job.jobId}`, { method: "POST" }).catch(() => null)
    updateJob(job.localId, { status: "error", errorMsg: "Đã hủy tải xuống" })
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

      updateJob(localId, { status: "downloading", jobId: job_id })

      const es = new EventSource(`/api/progress/${job_id}`)
      es.onmessage = (e) => {
        const d = JSON.parse(e.data)
        if (d.type === "progress") {
          updateJob(localId, { percent: d.percent ?? 0, speed: d.speed ?? "", title: d.title || "Đang tải...", status: "downloading" })
        } else if (d.type === "done") {
          updateJob(localId, { status: "done", percent: 100, title: d.title, downloadUrl: `/api/file/${job_id}` })
          es.close()
        } else if (d.type === "error") {
          updateJob(localId, { status: "error", errorMsg: d.message })
          es.close()
        }
      }
      es.onerror = () => { updateJob(localId, { status: "error", errorMsg: "Mất kết nối đến server." }); es.close() }
    } catch (err) {
      updateJob(localId, { status: "error", errorMsg: err instanceof Error ? err.message : "Lỗi không xác định." })
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
    <div className="min-h-screen bg-[#07070f] text-white antialiased">

      {/* ── Navbar ── */}
      <nav className="fixed top-0 inset-x-0 z-50 h-16 flex items-center px-6 border-b border-white/[0.05] bg-[#07070f]/80 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto w-full flex items-center">
          <span className="text-xl font-bold tracking-tight">
            Vid<span className="text-violet-400">Get</span>
          </span>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative pt-36 pb-20 px-5 overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[500px] bg-violet-600/[0.08] rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-32 left-1/3 w-[350px] h-[350px] bg-blue-600/[0.06] rounded-full blur-[90px] pointer-events-none" />

        <div className="relative max-w-2xl mx-auto">

          {/* Badge */}
          <div className="flex justify-center mb-7">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-medium">
              <Sparkles size={11} />
              Miễn phí · Không đăng ký · Không quảng cáo
            </div>
          </div>

          {/* Heading */}
          <h1 className="text-center text-4xl sm:text-5xl md:text-[58px] font-extrabold leading-[1.1] tracking-tight mb-4">
            Tải video từ{" "}
            <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
              mọi nền tảng
            </span>
          </h1>
          <p className="text-center text-gray-500 text-base mb-10">
            Dán link — nhấn tải — xong.
          </p>

          {/* Platform selector */}
          <div className="flex flex-wrap justify-center gap-2 mb-4">
            {PLATFORMS.map((p) => (
              <button
                key={p.name}
                onClick={() => setPlatform(p.name)}
                className="px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all duration-200"
                style={
                  platform === p.name
                    ? { backgroundColor: `${p.color}1a`, borderColor: `${p.color}55`, color: p.color, boxShadow: `0 0 14px ${p.color}22` }
                    : { backgroundColor: "transparent", borderColor: "rgba(255,255,255,0.07)", color: "#4b5563" }
                }
              >
                {p.name}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="flex gap-2 p-1.5 rounded-2xl border border-white/[0.08] bg-white/[0.03] focus-within:border-violet-500/35 focus-within:bg-violet-500/[0.02] transition-all duration-300 mb-5">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleDownload()}
              placeholder="Dán link video vào đây…"
              className="flex-1 bg-transparent px-4 py-3 text-sm placeholder-gray-700 focus:outline-none"
            />
            <button
              onClick={handleDownload}
              disabled={!url.trim()}
              className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
              style={{
                background: "linear-gradient(135deg,#7c3aed,#6d28d9)",
                boxShadow: url.trim() ? "0 0 24px rgba(124,58,237,0.35)" : "none",
              }}
            >
              <Download size={14} /> Tải xuống
            </button>
          </div>

          {/* Job list */}
          {jobs.length > 0 && (
            <div className="space-y-2.5">
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
        </div>
      </section>

      {/* ── Stats strip ── */}
      <div className="border-y border-white/[0.05] bg-white/[0.01] py-10 px-5">
        <div className="max-w-2xl mx-auto grid grid-cols-3 gap-6 text-center">
          {[
            { value: "500+",  label: "Trang web hỗ trợ" },
            { value: "4K",    label: "Chất lượng tối đa" },
            { value: "0đ",    label: "Hoàn toàn miễn phí" },
          ].map((s) => (
            <div key={s.label}>
              <p className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{s.value}</p>
              <p className="text-xs text-gray-600 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Platform showcase ── */}
      <section className="py-16 px-5">
        <div className="max-w-3xl mx-auto">
          <p className="text-center text-[11px] font-semibold uppercase tracking-widest text-gray-700 mb-6">
            Hỗ trợ tải từ
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              { name: "YouTube",   color: "#FF4444", desc: "Video & Shorts" },
              { name: "TikTok",    color: "#00d4d4", desc: "Video & Story" },
              { name: "Facebook",  color: "#4090f7", desc: "Video & Reels" },
              { name: "Instagram", color: "#e1306c", desc: "Reels & Post" },
              { name: "Twitter/X", color: "#1d9bf0", desc: "Video & GIF" },
              { name: "Vimeo",     color: "#1ab7ea", desc: "HD Video" },
              { name: "Reddit",    color: "#ff4500", desc: "Video & GIF" },
              { name: "Dailymotion", color: "#0066dc", desc: "Video" },
            ].map((p) => (
              <div
                key={p.name}
                className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl border transition-colors"
                style={{ borderColor: `${p.color}25`, backgroundColor: `${p.color}0d` }}
              >
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: p.color, boxShadow: `0 0 6px ${p.color}` }}
                />
                <div>
                  <p className="text-xs font-semibold text-gray-200 leading-none">{p.name}</p>
                  <p className="text-[10px] text-gray-600 mt-0.5">{p.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-center text-[11px] text-gray-700 mt-5">
            và hàng trăm trang khác được <span className="text-gray-500">yt-dlp</span> hỗ trợ
          </p>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-24 px-5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold mb-3">Tại sao chọn VidGet?</h2>
            <p className="text-gray-500 text-sm">Đơn giản, nhanh và đáng tin cậy.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="group p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06] hover:border-violet-500/25 hover:bg-white/[0.05] transition-all duration-300"
              >
                <div className="w-9 h-9 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mb-4 group-hover:bg-violet-500/20 transition-colors">
                  <f.icon className="text-violet-400" size={16} />
                </div>
                <h3 className="font-semibold text-white mb-1.5 text-sm">{f.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how" className="py-24 px-5 bg-white/[0.012]">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold mb-3">Chỉ 3 bước đơn giản</h2>
            <p className="text-gray-500 text-sm">Không cần cài đặt. Không cần tài khoản.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map((s, i) => (
              <div key={s.n} className="relative text-center">
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-6 left-[60%] w-full h-px bg-gradient-to-r from-violet-500/25 to-transparent" />
                )}
                <div className="w-11 h-11 rounded-full bg-violet-600/12 border border-violet-500/20 flex items-center justify-center text-violet-400 font-bold text-xs mx-auto mb-4">
                  {s.n}
                </div>
                <h3 className="font-semibold text-white mb-1.5 text-sm">{s.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="py-8 px-5 border-t border-white/[0.05] text-center">
        <p className="text-gray-700 text-sm">
          © 2026{" "}
          <span className="text-gray-500 font-medium">
            Vid<span className="text-violet-400">Get</span>
          </span>{" "}
          · Made with ♥
        </p>
      </footer>
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
      className="relative flex items-center gap-3 px-4 py-3.5 rounded-2xl border transition-all duration-300"
      style={{
        backgroundColor: isActive ? `${color}07` : "rgba(255,255,255,0.02)",
        borderColor: isActive ? `${color}28` : "rgba(255,255,255,0.06)",
      }}
    >
      {/* Accent stripe */}
      <div
        className="absolute left-0 top-3 bottom-3 w-[3px] rounded-r-full transition-opacity duration-300"
        style={{ backgroundColor: color, opacity: isActive ? 0.85 : 0.3 }}
      />

      {/* Platform badge */}
      <div
        className="ml-2 w-9 h-9 rounded-xl flex items-center justify-center text-[9px] font-bold tracking-wider shrink-0"
        style={{ backgroundColor: `${color}18`, color, border: `1px solid ${color}30` }}
      >
        {job.platform.slice(0, 2).toUpperCase()}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-100 truncate">{job.title}</p>

        {job.status === "pending" && (
          <div className="flex items-center gap-2 mt-1">
            <div className="flex items-end gap-[3px] h-3">
              {[0, 1, 2].map((i) => (
                <span key={i} className="w-[3px] rounded-full animate-bounce-dot"
                  style={{ height: "10px", backgroundColor: color, animationDelay: `${i * 0.18}s` }} />
              ))}
            </div>
            <span className="text-[11px] text-gray-600">Đang chuẩn bị...</span>
          </div>
        )}

        {job.status === "downloading" && (
          <div className="mt-1.5 space-y-1">
            <div className="relative h-1 bg-white/[0.05] rounded-full overflow-hidden">
              <div className="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${job.percent}%`, background: `linear-gradient(90deg,${color}88,${color})`, boxShadow: `0 0 8px ${color}44` }} />
              <div className="absolute inset-y-0 w-1/3 animate-shimmer"
                style={{ background: "linear-gradient(90deg,transparent,rgba(255,255,255,0.1),transparent)" }} />
            </div>
            <div className="flex items-center gap-1.5 text-[11px]">
              <span className="font-semibold text-gray-300">{job.percent.toFixed(0)}%</span>
              {job.speed && <><span className="text-gray-700">·</span><span className="text-gray-500">{job.speed}</span></>}
            </div>
          </div>
        )}

        {job.status === "done" && (
          <p className="text-[11px] text-emerald-500/80 mt-0.5">
            Hoàn thành · Nhấn <span className="text-emerald-400 font-medium">Lưu về</span> để lưu file
          </p>
        )}

        {job.status === "error" && (
          <p className="text-[11px] text-red-400/80 mt-0.5 break-words line-clamp-2">
            {job.errorMsg || "Tải thất bại"} · Nhấn <span className="font-medium">Thử lại</span>
          </p>
        )}
      </div>

      {/* Spinner */}
      <div className="shrink-0">
        {job.status === "downloading" && (
          <div className="w-4 h-4 rounded-full border-2 border-transparent animate-spin"
            style={{ borderTopColor: color, borderRightColor: `${color}40` }} />
        )}
        {job.status === "pending"  && <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: color }} />}
        {job.status === "done"     && <CheckCircle2 size={16} className="text-emerald-400" />}
        {job.status === "error"    && <XCircle size={16} className="text-red-400/70" />}
      </div>

      {/* Actions */}
      {isActive && (
        <button onClick={onStop}
          className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 border border-red-500/20 bg-red-500/[0.08] hover:bg-red-500/[0.16] text-red-400">
          <Square size={9} fill="currentColor" /> Stop
        </button>
      )}
      {job.status === "done" && job.downloadUrl && (
        <a href={job.downloadUrl} download
          className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 border border-emerald-500/20 bg-emerald-500/[0.08] hover:bg-emerald-500/[0.18] text-emerald-400">
          <Download size={11} /> Lưu về
        </a>
      )}
      {job.status === "error" && (
        <button onClick={onRetry}
          className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 border border-amber-500/20 bg-amber-500/[0.08] hover:bg-amber-500/[0.16] text-amber-400">
          <RefreshCw size={11} /> Thử lại
        </button>
      )}
    </div>
  )
}
