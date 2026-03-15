/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base:    '#09090b',   // page background
        surface: '#111113',   // card background
        raised:  '#18181b',   // input, elevated card
        border:  '#27272a',   // all borders and dividers
        muted4:  '#3f3f46',   // placeholders, disabled, muted icons
        muted5:  '#52525b',   // secondary icons, metadata
        muted7:  '#71717a',   // secondary text
        muted10: '#a1a1aa',   // body text
        muted14: '#e4e4e7',   // primary text
        white:   '#fafafa',   // headings, active labels
      },
      fontFamily: {
        inter: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      spacing: {
        '8': '8px',
        '16': '16px',
        '24': '24px',
        '32': '32px',
        '40': '40px',
        '48': '48px',
      },
      borderRadius: {
        '4': '4px',
        '6': '6px',
        '8': '8px',
        '10': '10px',
      },
      borderWidth: {
        '1.5': '1.5px',
      }
    },
  },
  plugins: [],
}
