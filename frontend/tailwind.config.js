/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // High-End Monochrome Scale
        base:     '#000000',
        surface:  '#0a0a0a',
        raised:   '#121212',
        card:     '#181818',

        // Monochrome Borders
        border:   'rgba(255, 255, 255, 0.08)',
        borderHi: 'rgba(255, 255, 255, 0.15)',

        // Pure Grayscale Text Scale
        muted3:  '#262626',
        muted4:  '#404040',
        muted5:  '#525252',
        muted6:  '#737373',
        muted7:  '#a3a3a3',
        muted9:  '#d4d4d4',
        muted11: '#e5e5e5',
        muted14: '#fafafa',
        white:   '#ffffff',

        // Grayscale "Accent" (White/Silver focus)
        accent:     '#ffffff',
        accentLight:'#e5e5e5',
        accentDim:  'rgba(255, 255, 255, 0.1)',

        // Minimal Status (keeping semantic meaning but desaturated)
        success: '#e5e5e5', // Done is now bold white
        warning: '#a3a3a3', // Warning is silver
        error:   '#ffffff', // Error is white on dark
      },
      fontFamily: {
        inter: ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        '4':  '4px',
        '6':  '6px',
        '8':  '8px',
        '10': '10px',
        '12': '12px',
        '16': '16px',
        '24': '24px',
      },
      borderWidth: {
        '1.5': '1.5px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.8)',
        'glow': '0 0 20px rgba(255, 255, 255, 0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'fade-up': 'fadeUp 0.6s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}
