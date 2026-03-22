/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#27dae0',
          hover: '#1cb0b5',
          dark: '#168f93'
        }
      },
      fontFamily: {
        'serif': ['"Playfair Display"', 'serif'],
        'sans-ui': ['system-ui', '-apple-system', '"Segoe UI"', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}