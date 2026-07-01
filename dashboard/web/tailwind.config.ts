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
          black:      "#121212",
          dark:       "#181818",
          card:       "#232323",
          gray:       "#282828",
          "mid-gray": "#535353",
          "light-gray":"#B3B3B3",
          white:      "#FFFFFF",
          green:      "#1DB954",
          "green-h":  "#1ed760",
          negative:   "#E9143D",
          positive:   "#1DB954",
          neutral:    "#B3B3B3",
        },
      },
      fontFamily: {
        spotify: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "sp": "8px",
      },
    },
  },
  plugins: [],
};

export default config;
