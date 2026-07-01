import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        sp: {
          black:       "#0d0d0d",   // page canvas
          sidebar:     "#111111",   // sidebar bg
          dark:        "#161616",   // card bg
          card:        "#1c1c1c",   // inner card / table row
          gray:        "#222222",   // secondary card / hover
          border:      "#2a2a2a",   // subtle borders
          "mid-gray":  "#555555",   // muted text
          "light-gray":"#999999",   // secondary text
          white:       "#FFFFFF",
          green:       "#1DB954",
          "green-h":   "#1ed760",
          "green-dim": "#1DB95420", // green at 12% opacity
          negative:    "#E84040",
          "neg-dim":   "#E8404020",
          positive:    "#1DB954",
          neutral:     "#999999",
          warning:     "#F59E0B",
        },
      },
      fontFamily: {
        spotify: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        sp: "10px",
        "sp-sm": "6px",
        "sp-lg": "14px",
      },
    },
  },
  plugins: [],
};

export default config;
