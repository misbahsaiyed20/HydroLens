/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ocean: {
          50: "#eef6f6",
          100: "#d7e9ea",
          200: "#b0d3d5",
          300: "#7fb6ba",
          400: "#4c969c",
          500: "#2f7a81",
          600: "#215e66",
          700: "#1a4a51",
          800: "#123239", // primary deep teal
          900: "#0b2126",
        },
        aqua: {
          50: "#eafbfb",
          100: "#cdf4f4",
          200: "#9fe8e9",
          300: "#67d6d9",
          400: "#34bfc4", // secondary fresh aqua
          500: "#1fa3a9",
          600: "#1a828a",
          700: "#19676d",
        },
        moss: {
          50: "#f1f8ee",
          100: "#dfeed6",
          200: "#bcdcac",
          300: "#93c67c",
          400: "#6fac57", // natural green accent
          500: "#54903f",
          600: "#417332",
          700: "#355c2a",
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Inter", "Roboto", "sans-serif"],
      },
      borderRadius: {
        card: "0.875rem",
        pill: "999px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(11,33,38,0.04), 0 4px 16px -4px rgba(11,33,38,0.08)",
        "card-hover": "0 2px 4px rgba(11,33,38,0.06), 0 12px 28px -8px rgba(11,33,38,0.14)",
        pop: "0 8px 24px -6px rgba(11,33,38,0.18)",
      },
      backgroundImage: {
        "hero-wash": "radial-gradient(circle at 15% 0%, rgba(52,191,196,0.14), transparent 55%), radial-gradient(circle at 85% 10%, rgba(111,172,87,0.10), transparent 45%)",
      },
      keyframes: {
        "fade-in": { "0%": { opacity: 0, transform: "translateY(4px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
      },
      animation: {
        "fade-in": "fade-in 0.35s ease-out",
      },
    },
  },
  plugins: [],
};
