import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      keyframes: {
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        "bounce-dot": {
          "0%, 80%, 100%": { transform: "scaleY(0.4)", opacity: "0.4" },
          "40%": { transform: "scaleY(1)", opacity: "1" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s infinite",
        "bounce-dot": "bounce-dot 1.2s infinite ease-in-out",
      },
    },
  },
  plugins: [],
}

export default config
