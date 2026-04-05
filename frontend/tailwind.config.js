/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          red: '#9B1C1C',
          teal: '#0D7377',
        },
      },
    },
  },
  plugins: [],
}
