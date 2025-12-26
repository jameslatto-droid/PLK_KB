import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f5f7fb",
          100: "#e7ecf5",
          200: "#c7d3e6",
          300: "#9fb4d4",
          400: "#6f89bb",
          500: "#4f6aa4",
          600: "#3f5486",
          700: "#334368",
          800: "#2a3650",
          900: "#20283c",
        },
        ember: {
          50: "#fff4ed",
          100: "#ffe4d5",
          200: "#ffc5aa",
          300: "#ff9b73",
          400: "#ff6b3a",
          500: "#f34c13",
          600: "#cc370b",
          700: "#a52c0d",
          800: "#842510",
          900: "#6b1f0f",
        },
      },
      boxShadow: {
        panel: "0 20px 60px -40px rgba(15, 23, 42, 0.6)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        serif: ["var(--font-serif)", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
