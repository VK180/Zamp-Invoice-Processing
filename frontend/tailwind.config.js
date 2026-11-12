/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        zamp: {
          50: '#eef6ff',
          100: '#d9ebff',
          200: '#bcdbff',
          300: '#8ec3ff',
          400: '#58a0fd',
          500: '#257bf4',
          600: '#155ed9',
          700: '#124ab0',
          800: '#143f8e',
          900: '#153673',
          950: '#0f2249',
        }
      }
    },
  },
  plugins: [],
}
