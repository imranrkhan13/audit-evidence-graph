/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        stone: {
          50: "#faf8f5",
          100: "#f2ede4",
        },
        navy: {
          900: "#1c2333",
          700: "#2d3548",
        },
        slate: {
          panel: "#eceae4",
        },
        pass: "#1f7a4d",
        review: "#a8710a",
        fail: "#a83232",
        accent: "#2b6f77",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
