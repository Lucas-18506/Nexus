/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        green: { 500: '#10B981' },
        yellow: { 500: '#F59E0B' },
        red: { 500: '#EF4444' },
      },
    },
  },
  plugins: [],
}
