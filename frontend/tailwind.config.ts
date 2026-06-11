import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#f4f1ea",
        panel: "#fffdf8",
        ink: "#132022",
        accent: "#195d4d",
        muted: "#667375",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(19, 32, 34, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
