/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        cream: '#FFF8F0',
        terracotta: '#E07A5F',
        sage: '#81B29A',
        charcoal: '#3D405B',
        gold: '#F2CC8F',
      },
      fontFamily: {
        heading: ['"Patrick Hand"', 'cursive'],
        body: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
