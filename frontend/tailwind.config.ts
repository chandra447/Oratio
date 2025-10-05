import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Oratio Brand Colors
        primary: {
          DEFAULT: "#1A244B",
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#FFB76B",
          foreground: "#1A244B",
        },
        accent: {
          DEFAULT: "#8A3FFC",
          foreground: "#FFFFFF",
        },
        // Background Colors
        "background-light": "#F7F7F9",
        "background-dark": "#101010",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // Surface Colors
        "surface-light": "#FFFFFF",
        "surface-dark": "#1C1C1E",
        // Text Colors
        "text-light": "#1A244B",
        "text-dark": "#FFFFFF",
        "subtle-light": "#646B87",
        "subtle-dark": "#A0AEC0",
        // Additional Oratio Colors
        "highlight-violet": "#8B5CF6",
        "border-light": "#E2E8F0",
        "border-dark": "#334155",
        // shadcn/ui compatibility
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "1rem",
        lg: "1.5rem",
        xl: "2rem",
        full: "9999px",
      },
      boxShadow: {
        glow: "0 0 20px 5px rgba(255, 183, 107, 0.3), 0 0 10px 2px rgba(138, 63, 252, 0.2)",
      },
      animation: {
        blob: "blob 7s infinite",
      },
      keyframes: {
        blob: {
          "0%": { transform: "translate(0px, 0px) scale(1)" },
          "33%": { transform: "translate(30px, -50px) scale(1.1)" },
          "66%": { transform: "translate(-20px, 20px) scale(0.9)" },
          "100%": { transform: "translate(0px, 0px) scale(1)" },
        },
      },
    },
  },
  plugins: [],
}

export default config
