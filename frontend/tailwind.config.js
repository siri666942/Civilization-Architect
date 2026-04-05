/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 赛博朋克配色
        'cyber-primary': '#0a0e17',
        'cyber-secondary': '#1a1f2e',
        'cyber-accent': '#00f0ff',
        'cyber-accent-alt': '#ff00ff',
        'cyber-success': '#39ff14',
        'cyber-danger': '#ff3131',
        'cyber-text': '#e8eaed',
        'cyber-text-muted': '#9ca3af',
        'cyber-border': 'rgba(0, 240, 255, 0.2)',
      },
      fontFamily: {
        'display': ['Orbitron', 'sans-serif'],
        'heading': ['Rajdhani', 'sans-serif'],
        'body': ['Inter', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'scanline': 'scanline 3s linear infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 240, 255, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 240, 255, 0.6)' },
        },
        'scanline': {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '100% 100%' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      backgroundImage: {
        'cyber-gradient': 'linear-gradient(135deg, #0a0e17 0%, #111827 100%)',
        'cyber-glow': 'radial-gradient(circle at center, rgba(0, 240, 255, 0.1) 0%, transparent 70%)',
      },
    },
  },
  plugins: [],
}