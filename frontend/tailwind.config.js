/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Page layers
        base:     '#08080a',
        surface:  '#0f0f13',
        raised:   '#161620',
        card:     '#1a1a24',

        // Borders
        border:   '#22222e',
        borderHi: '#32323e',

        // Muted text scale
        muted3:  '#2e2e3c',
        muted4:  '#3a3a4e',
        muted5:  '#50505e',
        muted6:  '#606070',
        muted7:  '#78788a',
        muted9:  '#9898aa',
        muted11: '#c0c0d0',
        muted14: '#e0e0ee',
        white:   '#f4f4fc',

        // Accent
        accent:     '#7c6af7',
        accentLight:'#a78bfa',
        accentDim:  'rgba(124,106,247,0.14)',

        // Status
        success: '#34d399',
        warning: '#fbbf24',
        error:   '#f87171',
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
      },
      borderWidth: {
        '1.5': '1.5px',
      },
      animation: {
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4,0,0.6,1) infinite',
      },
    },
  },
  plugins: [],
}
