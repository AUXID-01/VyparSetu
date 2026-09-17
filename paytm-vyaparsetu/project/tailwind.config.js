/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sage: {
          50: '#F0F7F4',
          100: '#DCEEE7',
          200: '#B9DDD0',
          300: '#8FC6B2',
          400: '#6BAB97',
          500: '#4F9B82',
          600: '#3D7E69',
          700: '#336656',
          800: '#2B5347',
          900: '#244539',
        },
        teal: {
          50: '#EEF8F6',
          100: '#D3EFE9',
          200: '#A8DFD4',
          300: '#72B7A3',
          400: '#5AA188',
          500: '#4A8A73',
          600: '#3B705D',
          700: '#315A4D',
          800: '#284940',
          900: '#1F3A33',
        },
        mint: {
          50: '#F1F9F5',
          100: '#DFF1E7',
          200: '#BCE3CD',
          300: '#8FD0AC',
          400: '#67BD90',
          500: '#4FA879',
        },
        cream: {
          50: '#FBFCFB',
          100: '#F8FAF9',
          200: '#F0F4F2',
          300: '#E6ECE9',
        },
        ink: {
          50: '#F5F7F6',
          100: '#E8EDEB',
          200: '#CDD6D2',
          300: '#A7B2AE',
          400: '#66736E',
          500: '#4A5651',
          600: '#33403B',
          700: '#17201D',
          800: '#0F1715',
          900: '#0A100E',
        },
        positive: '#5C9B78',
        warning: '#D7A85D',
        danger: '#D98276',
      },
      fontFamily: {
        sans: ['Inter', 'Manrope', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'wave': 'wave 1s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        wave: {
          '0%, 100%': { transform: 'scaleY(0.3)' },
          '50%': { transform: 'scaleY(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
};
