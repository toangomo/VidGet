"use client"

import { useState } from "react"
import { Download, Zap, Shield, Globe, Sparkles, CheckCircle2, XCircle, RefreshCw, Square, Monitor, ChevronRight, ChevronDown, MousePointerClick, Info, Apple } from "lucide-react"

const WIN_URL = "https://github.com/toangomo/VidGet/releases/latest/download/VidGet.exe"
const MAC_URL = "https://github.com/toangomo/VidGet/releases/latest/download/VidGet-mac.dmg"

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
        <div className="max-w-5xl mx-auto w-full flex items-center justify-between">
          <span className="text-[1.625rem] font-bold tracking-tight">
            Vid<span className="text-violet-400">Get</span>
          </span>
          <div className="flex items-center gap-1.5">
            <a
              href={WIN_URL}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-violet-500/25 bg-violet-500/10 text-violet-300 hover:bg-violet-500/20 hover:border-violet-500/40 transition-all duration-200"
            >
              <Monitor size={11} />
              Windows
            </a>
            <a
              href={MAC_URL}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-violet-500/25 bg-violet-500/10 text-violet-300 hover:bg-violet-500/20 hover:border-violet-500/40 transition-all duration-200"
            >
              <Apple size={11} />
              macOS
            </a>
          </div>
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
          <h1 className="text-center text-4xl sm:text-5xl md:text-[58px] font-extrabold leading-[2.15] tracking-tight mb-4">
            Tải video từ{" "}
            <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
              mọi nền tảng phổ biến
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

      {/* ── Desktop App CTA ── */}
      <section className="py-12 px-5">
        <div className="max-w-2xl mx-auto">
          <div
            className="relative rounded-3xl border border-violet-500/20 overflow-hidden p-8 sm:p-10 text-center"
            style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(124,58,237,0.12) 0%, rgba(7,7,15,0) 70%), #07070f" }}
          >
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[400px] h-[200px] bg-violet-600/[0.1] rounded-full blur-[80px] pointer-events-none" />
            <div className="relative">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-medium mb-5">
                <Monitor size={11} />
                Ứng dụng Desktop
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold mb-3 tracking-tight">
                Tải VidGet về{" "}
                <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                  máy tính
                </span>
              </h2>
              <p className="text-gray-500 text-sm leading-relaxed mb-7 max-w-md mx-auto">
                Chạy offline, tải thẳng vào máy, không cần trình duyệt hay kết nối server. Giao diện tối đẹp, hỗ trợ hàng trăm trang web.
              </p>
              <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs text-gray-600 mb-8">
                {["Windows 10 / 11", "macOS 12+", "Không cần cài đặt", "Miễn phí hoàn toàn"].map((f) => (
                  <span key={f} className="flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-violet-500/60" />
                    {f}
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap justify-center gap-3 mb-2">
                <a
                  href={WIN_URL}
                  className="inline-flex items-center gap-3 px-7 py-4 rounded-2xl font-bold text-base text-white transition-all duration-200 hover:scale-[1.03] active:scale-[0.98]"
                  style={{
                    background: "linear-gradient(135deg, #7c3aed, #6d28d9)",
                    boxShadow: "0 0 40px rgba(124,58,237,0.35), 0 2px 8px rgba(0,0,0,0.4)",
                  }}
                >
                  <Monitor size={18} />
                  <span>
                    <span className="block">Tải cho Windows</span>
                    <span className="block text-xs font-normal opacity-60">VidGet.exe · ~31 MB</span>
                  </span>
                </a>
                <a
                  href={MAC_URL}
                  className="inline-flex items-center gap-3 px-7 py-4 rounded-2xl font-bold text-base text-white transition-all duration-200 hover:scale-[1.03] active:scale-[0.98]"
                  style={{
                    background: "linear-gradient(135deg, #3a3a4a, #252532)",
                    boxShadow: "0 0 24px rgba(255,255,255,0.06), 0 2px 8px rgba(0,0,0,0.4)",
                    border: "1px solid rgba(255,255,255,0.08)",
                  }}
                >
                  <Apple size={18} />
                  <span>
                    <span className="block">Tải cho macOS</span>
                    <span className="block text-xs font-normal opacity-60">VidGet.dmg · ~60 MB</span>
                  </span>
                </a>
              </div>
              <div className="mt-6">
                <SmartScreenGuide />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats strip ── */}
      <div className="border-y border-white/[0.05] bg-white/[0.01] py-10 px-5">
        <div className="max-w-2xl mx-auto grid grid-cols-3 gap-6 text-center">
          {[
            { icon: "⚡", text: "Tốc độ siêu nhanh" },
            { icon: "✨", text: "Chất lượng tối đa" },
            { icon: "💰", text: "Miễn phí hoàn toàn" },
          ].map((s) => (
            <div key={s.text}>
              <p className="text-3xl mb-2">{s.icon}</p>
              <p className="text-xs font-bold text-white leading-snug">{s.text}</p>
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

// ── SmartScreenGuide ─────────────────────────────────────────────────────────

function SmartScreenGuide() {
  const [open, setOpen] = useState(false)

  const steps = [
    {
      icon: <Download size={14} />,
      label: "Tải file về",
      desc: 'Nhấn nút "Tải VidGet.exe" ở trên. File khoảng 31 MB.',
    },
    {
      icon: <Info size={14} />,
      label: 'Windows hiện cảnh báo "Windows protected your PC"',
      desc: 'Đây là bình thường — Windows cảnh báo tất cả phần mềm mới chưa có chữ ký số. VidGet hoàn toàn an toàn và mã nguồn mở.',
    },
    {
      icon: <MousePointerClick size={14} />,
      label: 'Nhấn "More info"',
      desc: 'Ở cửa sổ cảnh báo màu xanh, nhấn chữ "More info" nhỏ phía dưới.',
    },
    {
      icon: <ChevronRight size={14} />,
      label: 'Nhấn "Run anyway"',
      desc: 'Nút "Run anyway" hiện ra — nhấn vào để chạy VidGet bình thường.',
    },
  ]

  return (
    <div className="text-left">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 mx-auto text-xs text-gray-600 hover:text-gray-400 transition-colors"
      >
        <Info size={12} className="text-amber-500/70" />
        Windows hiện cảnh báo SmartScreen? Xem hướng dẫn
        <ChevronDown size={12} className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="mt-4 rounded-2xl border border-amber-500/15 bg-amber-500/[0.04] p-5">
          <p className="text-xs font-semibold text-amber-400/80 mb-4 flex items-center gap-2">
            <Info size={12} />
            Tại sao có cảnh báo?
          </p>
          <p className="text-xs text-gray-600 leading-relaxed mb-5">
            Windows SmartScreen cảnh báo tất cả phần mềm chưa được ký bằng chứng chỉ số thương mại (code signing certificate). VidGet là phần mềm mã nguồn mở, miễn phí — hoàn toàn an toàn. Chỉ cần làm theo 4 bước dưới đây:
          </p>
          <div className="space-y-3">
            {steps.map((s, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-violet-500/15 border border-violet-500/20 flex items-center justify-center text-violet-400 font-bold text-[10px]">
                  {i + 1}
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                    <span className="text-violet-400">{s.icon}</span>
                    {s.label}
                  </p>
                  <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-gray-700 mt-4 pt-3 border-t border-white/[0.05]">
            Mã nguồn VidGet công khai tại{" "}
            <a href="https://github.com/toangomo/VidGet" target="_blank" rel="noopener noreferrer"
              className="text-violet-400/70 hover:text-violet-400 underline underline-offset-2">
              github.com/toangomo/VidGet
            </a>
          </p>
        </div>
      )}
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
          <>
            <p className="text-[11px] text-red-400/80 mt-0.5 break-words line-clamp-2">
              {job.errorMsg || "Tải thất bại"} · Nhấn <span className="font-medium">Thử lại</span>
            </p>
            {job.errorMsg?.includes("chặn") && (
              <div className="mt-2 p-2.5 rounded-xl bg-amber-500/[0.06] border border-amber-500/15">
                <p className="text-[11px] text-amber-300/70 leading-relaxed">
                  YouTube chặn tải xuống từ server đám mây. Hãy dùng{" "}
                  <a href={WIN_URL} className="text-violet-400 font-semibold hover:text-violet-300 transition-colors">
                    ứng dụng desktop
                  </a>
                  {" "}để tải YouTube nhanh hơn, không bị giới hạn.
                </p>
              </div>
            )}
          </>
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
