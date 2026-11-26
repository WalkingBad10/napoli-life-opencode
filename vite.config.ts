import { defineConfig } from 'vite';

export default defineConfig({
  // Base relativa: la versione web funziona su GitHub Pages in una sottocartella.
  base: './',
  build: {
    target: 'es2020',
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 1600,
  },
  server: { host: '0.0.0.0', port: 5173 },
});
