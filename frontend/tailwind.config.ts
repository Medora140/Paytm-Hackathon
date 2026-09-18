import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#9fe870",
          active: "#cdffad",
          neutral: "#c5edab",
          pale: "#e2f6d5",
        },
        canvas: {
          DEFAULT: "#ffffff",
          soft: "#e8ebe6",
        },
        ink: {
          DEFAULT: "#0e0f0c",
          deep: "#163300",
        },
        body: "#454745",
        mute: "#868685",
        positive: {
          DEFAULT: "#2ead4b",
          deep: "#054d28",
        },
        warning: {
          DEFAULT: "#ffd11a",
          deep: "#b86700",
          content: "#4a3b1c",
        },
        negative: {
          DEFAULT: "#d03238",
          deep: "#a72027",
          darkest: "#a7000d",
          bg: "#320707",
        },
        accent: {
          orange: "#ffc091",
          cyan: "#38c8ff",
        },
      },
      borderRadius: {
        "xl-brand": "24px",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
