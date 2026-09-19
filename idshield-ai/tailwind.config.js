/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#070b14',
          900: '#0c1322',
          850: '#111a2e',
          800: '#18243e',
          700: '#263554'
        },
        shield: {
          cyan: '#00e5ff',
          blue: '#1e88e5',
          dark: '#050811'
        }
      }
    },
  },
  plugins: [],
}