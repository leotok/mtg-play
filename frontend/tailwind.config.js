/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'mtg-black': '#1a1a1a',
        'mtg-gold': '#d4af37',
        'mtg-dark': '#2d2d2d',
        'mtg-light': '#f5f5f5',
      },
      fontFamily: {
        'card': ['Georgia', 'serif'],
      },
      boxShadow: {
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
        'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
      },
    },
  },
  plugins: [],
}
