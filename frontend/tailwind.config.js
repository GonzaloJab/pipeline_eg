/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      "./pages/**/*.{js,ts,jsx,tsx}",
      "./components/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          primary: {
            600: '#2563eb',
            700: '#1d4ed8',
          },
          danger: {
            500: '#ef4444',
            600: '#dc2626',
          }
        },
        boxShadow: {
          form: '0 2px 10px rgba(0, 0, 0, 0.1)',
          card: '0 1px 3px rgba(0, 0, 0, 0.1)',
        }
      },
    },
    plugins: [],
  }