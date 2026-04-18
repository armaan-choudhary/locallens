/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Main Content Area (Beige Palette) ──────────
        base:     '#D4BFB0',   // Primary beige background
        surface:  '#C9B2A1',   // Slightly darker for inputs/cards
        raised:   '#BFA898',   // Even darker for hover states
        card:     '#E0CFC2',   // Lighter cards on beige
        cardHi:   '#EAE0D7',   // Lightest card variant

        // ── Sidebar (Greyish Purple Palette) ───────────
        sidebar:     '#8B7089',  // Primary sidebar background
        sidebarDark: '#7A6178',  // Darker sidebar accents
        sidebarHi:   '#9A8098',  // Lighter sidebar hover

        // ── Borders ────────────────────────────────────
        border:   'rgba(0, 0, 0, 0.10)',
        borderHi: 'rgba(0, 0, 0, 0.18)',
        sidebarBorder: 'rgba(255, 255, 255, 0.12)',

        // ── Text on Beige (Warm Dark Scale) ────────────
        textPrimary:   '#2C2825',
        textSecondary: '#4A4542',
        textMuted:     '#7A7370',
        textLight:     '#9E9894',

        // ── Text on Sidebar (Light Scale) ──────────────
        sidebarText:     '#F0E8EF',
        sidebarTextDim:  'rgba(255, 255, 255, 0.60)',
        sidebarTextMute: 'rgba(255, 255, 255, 0.40)',

        // ── Accent (Purple Tint) ───────────────────────
        accent:      '#6B5568',
        accentLight: '#8B7089',
        accentDim:   'rgba(107, 85, 104, 0.15)',

        // ── Semantic Status ────────────────────────────
        success: '#4A7C59',
        warning: '#A67C3D',
        error:   '#9E4444',

        // ── Legacy compat aliases (used sparingly) ─────
        muted3:  '#BFA898',
        muted4:  '#9E9894',
        muted5:  '#8A8480',
        muted6:  '#7A7370',
        muted7:  '#6A6360',
        muted9:  '#4A4542',
        muted11: '#3A3532',
        muted14: '#2C2825',
        white:   '#2C2825',  // "white" now maps to dark text on light bg
      },
      fontFamily: {
        inter: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono:  ['JetBrains Mono', 'ui-monospace', 'monospace'],
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
        'glass': '0 4px 24px 0 rgba(0, 0, 0, 0.08)',
        'glow':  '0 2px 12px rgba(107, 85, 104, 0.20)',
        'card':  '0 1px 3px rgba(0, 0, 0, 0.06)',
        'input': '0 2px 8px rgba(0, 0, 0, 0.05)',
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
