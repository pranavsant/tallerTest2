import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      // ── Brand / primary ──────────────────────────────────────────────────
      colors: {
        brand: {
          50: "#f0f4ff",
          100: "#dbe4ff",
          200: "#bac8ff",
          300: "#91a7ff",
          400: "#748ffc",
          500: "#5c7cfa",
          600: "#4c6ef5",
          700: "#4263eb",
          800: "#3b5bdb",
          900: "#364fc7",
          950: "#1e3a8a",
        },

        // ── Dashboard surfaces ─────────────────────────────────────────────
        // Use as bg-surface, bg-sidebar, bg-sidebar-item-active, etc.
        surface: {
          DEFAULT: "#ffffff",
          muted: "#f8fafc",
          dark: "#0f172a",
          "dark-muted": "#1e293b",
        },
        sidebar: {
          DEFAULT: "#0f172a",   // dark slate — sidebar background
          border: "#1e293b",    // subtle divider inside sidebar
          item: "#1e293b",      // hover / selected item bg
          text: "#94a3b8",      // muted nav label
          "text-active": "#f1f5f9", // active nav label
        },
        topbar: {
          DEFAULT: "#ffffff",
          dark: "#0f172a",
          border: "#e2e8f0",
          "border-dark": "#1e293b",
        },

        // ── Agent / session status palette ────────────────────────────────
        status: {
          idle: "#6b7280",
          active: "#16a34a",
          busy: "#d97706",
          offline: "#dc2626",
          suspended: "#9333ea",
          ended: "#64748b",
          error: "#dc2626",
        },
      },

      // ── Typography ───────────────────────────────────────────────────────
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "SFMono-Regular"],
      },

      // ── Spacing ──────────────────────────────────────────────────────────
      spacing: {
        // Sidebar width — use w-sidebar / ml-sidebar in layout
        sidebar: "16rem",   // 256 px
        "sidebar-collapsed": "4rem", // 64 px icon-only mode
        // Dashboard content max-width
        "content-max": "80rem",
        // Topbar height
        topbar: "4rem",     // 64 px
      },

      // ── Border radius ────────────────────────────────────────────────────
      borderRadius: {
        card: "0.75rem",  // rounded-card  — dashboard cards
        pill: "9999px",   // rounded-pill  — badges, tags
        input: "0.5rem",  // rounded-input — form inputs
      },

      // ── Box shadows ──────────────────────────────────────────────────────
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)",
        "card-md": "0 4px 12px 0 rgb(0 0 0 / 0.08)",
        "card-hover": "0 8px 24px 0 rgb(0 0 0 / 0.10)",
        sidebar: "2px 0 8px 0 rgb(0 0 0 / 0.12)",
      },

      // ── Animations ───────────────────────────────────────────────────────
      keyframes: {
        "slide-in-left": {
          from: { transform: "translateX(-100%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      animation: {
        "slide-in-left": "slide-in-left 0.2s ease-out",
        "fade-in": "fade-in 0.15s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
