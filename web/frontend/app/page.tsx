import Link from "next/link"
import { ArrowRight, Download, Zap, Shield, Globe, Sparkles } from "lucide-react"

const PLATFORMS = [
  { name: "YouTube",    color: "#FF0000", short: "YT" },
  { name: "TikTok",     color: "#010101", short: "TT" },
  { name: "Facebook",   color: "#1877F2", short: "FB" },
  { name: "Instagram",  color: "#C13584", short: "IG" },
  { name: "Twitter / X", color: "#1DA1F2", short: "X"  },
  { name: "1000+ sites", color: "#6B7280", short: "…"  },
]

const FEATURES = [
  {
    icon: Zap,
    title: "Tải siêu nhanh",
    desc: "Tốc độ tải xuống tối đa, không giới hạn băng thông hay hàng chờ.",
  },
  {
    icon: Globe,
    title: "Đa nền tảng",
    desc: "YouTube, TikTok, Facebook, Instagram và hơn 1000 trang web khác.",
  },
  {
    icon: Download,
    title: "Chất lượng cao",
    desc: "Tải video 4K, 1080p với âm thanh lossless. Không nén, không mất chất lượng.",
  },
  {
    icon: Shield,
    title: "Bảo mật & Riêng tư",
    desc: "Link video được xử lý ngay và không lưu lại. Dữ liệu của bạn là của bạn.",
  },
]

const STEPS = [
  {
    n: "01",
    title: "Sao chép link",
    desc: "Copy link video từ bất kỳ trang web nào — YouTube, TikTok, Facebook...",
  },
  {
    n: "02",
    title: "Dán & Tải xuống",
    desc: "Dán link vào VidGet, chọn nền tảng rồi nhấn nút Tải xuống.",
  },
  {
    n: "03",
    title: "Lưu về thiết bị",
    desc: "Video được xử lý trên server và trả về ngay để bạn lưu về máy.",
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#07070f] text-white antialiased">

      {/* ── Navbar ── */}
      <nav className="fixed top-0 inset-x-0 z-50 h-16 flex items-center px-6 border-b border-white/[0.06] bg-[#07070f]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto w-full flex items-center justify-between">
          <span className="text-xl font-bold tracking-tight">
            Vid<span className="text-violet-400">Get</span>
          </span>
          <Link
            href="/download"
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-sm font-semibold transition-colors"
          >
            Thử ngay <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative pt-40 pb-28 px-6 text-center overflow-hidden">
        {/* Glow orbs */}
        <div className="absolute top-24 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-violet-600/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-40 left-1/3 w-[300px] h-[300px] bg-blue-600/10 rounded-full blur-[80px] pointer-events-none" />

        <div className="relative max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-medium mb-8">
            <Sparkles size={12} />
            Miễn phí · Không đăng ký · Không quảng cáo
          </div>

          <h1 className="text-5xl md:text-[64px] font-extrabold leading-[1.08] tracking-tight mb-6">
            Tải video từ{" "}
            <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-blue-400 bg-clip-text text-transparent">
              mọi nền tảng
            </span>
          </h1>

          <p className="text-lg text-gray-400 max-w-xl mx-auto mb-10 leading-relaxed">
            Dán link — nhấn tải — xong. Nhanh, sạch, không rác.
            Hỗ trợ YouTube, TikTok, Facebook và hơn 1000 trang web.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/download"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-violet-600 hover:bg-violet-500 text-base font-semibold transition-all hover:scale-[1.03] shadow-xl shadow-violet-500/20"
            >
              Bắt đầu tải xuống <ArrowRight size={18} />
            </Link>
            <Link
              href="#how"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-base font-medium transition-colors"
            >
              Xem cách dùng
            </Link>
          </div>
        </div>
      </section>

      {/* ── Platforms ── */}
      <section className="py-14 px-6 border-y border-white/[0.05]">
        <div className="max-w-4xl mx-auto">
          <p className="text-center text-gray-600 text-xs font-semibold uppercase tracking-widest mb-6">
            Hỗ trợ
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {PLATFORMS.map((p) => (
              <div
                key={p.name}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.04] border border-white/[0.08] text-sm text-gray-300 hover:border-white/20 transition-colors"
              >
                <span
                  className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0"
                  style={{ backgroundColor: p.color }}
                >
                  {p.short}
                </span>
                {p.name}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Tại sao chọn VidGet?</h2>
            <p className="text-gray-500 max-w-md mx-auto">
              Được xây dựng để đơn giản, nhanh và đáng tin cậy.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="group p-6 rounded-2xl bg-white/[0.03] border border-white/[0.07] hover:border-violet-500/30 hover:bg-white/[0.05] transition-all duration-300"
              >
                <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mb-4 group-hover:bg-violet-500/20 transition-colors">
                  <f.icon className="text-violet-400" size={18} />
                </div>
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how" className="py-24 px-6 bg-white/[0.015]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Chỉ 3 bước đơn giản</h2>
            <p className="text-gray-500">Không cần cài đặt. Không cần tài khoản.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map((s, i) => (
              <div key={s.n} className="relative text-center">
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-6 left-[60%] w-full h-px bg-gradient-to-r from-violet-500/30 to-transparent" />
                )}
                <div className="w-12 h-12 rounded-full bg-violet-600/15 border border-violet-500/25 flex items-center justify-center text-violet-400 font-bold text-sm mx-auto mb-5">
                  {s.n}
                </div>
                <h3 className="font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-28 px-6 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Sẵn sàng chưa?
          </h2>
          <p className="text-gray-500 mb-10">
            Hoàn toàn miễn phí. Không cần tạo tài khoản. Bắt đầu ngay bây giờ.
          </p>
          <Link
            href="/download"
            className="inline-flex items-center gap-2 px-10 py-4 rounded-xl bg-violet-600 hover:bg-violet-500 text-base font-semibold transition-all hover:scale-[1.03] shadow-xl shadow-violet-500/20"
          >
            Tải video ngay <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="py-8 px-6 border-t border-white/[0.06] text-center">
        <p className="text-gray-600 text-sm">
          © 2026{" "}
          <span className="text-gray-400 font-medium">
            Vid<span className="text-violet-400">Get</span>
          </span>{" "}
          · Made with ♥
        </p>
      </footer>
    </div>
  )
}
