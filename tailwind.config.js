/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./static/**/*.js"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Poppins", "system-ui", "sans-serif"],
      },
      colors: {
        primary: {
          50: "#f5f3ff",
          100: "#ede9fe",
          200: "#ddd6fe",
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
          800: "#5b21b6",
          900: "#4c1d95",
        },
        secondary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: "none",
            color: "#333",
            a: {
              color: "#8b5cf6", // matching primary.500
              "&:hover": {
                color: "#7c3aed", // matching primary.600
              },
            },
            h1: {
              fontFamily: "Poppins, sans-serif",
            },
            h2: {
              fontFamily: "Poppins, sans-serif",
            },
            h3: {
              fontFamily: "Poppins, sans-serif",
            },
          },
        },
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("@tailwindcss/forms"),
    require("@tailwindcss/aspect-ratio"),
  ],
};
