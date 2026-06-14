/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        nicto: {
          bg: '#030712',
          surface: '#111827',
          green: '#22c55e',
          accent: '#06b6d4',
          text: '#f3f4f6',
          muted: '#9ca3af',
        },
      },
    },
  },
  plugins: [],
}
