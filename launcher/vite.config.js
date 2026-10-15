import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'

const launcher = fileURLToPath(new URL('./src', import.meta.url))
// The deployed web application is bundled as a second page, so the launcher
// ships the very same dashboard without duplicating its source.
const dashboard = fileURLToPath(new URL('../frontend/src', import.meta.url))

export default defineConfig({
  base: './',
  plugins: [vue(), UnoCSS()],
  resolve: {
    alias: {
      '@': launcher,
      '@dashboard': dashboard
    },
    // The dashboard sources live outside this package, so their bare imports
    // must be resolved from the launcher's own dependencies.
    dedupe: ['vue', 'vue-router', 'lucide-vue-next', 'marked', 'plotly.js-dist-min']
  },
  build: {
    target: 'es2021',
    chunkSizeWarningLimit: 4096,
    rollupOptions: {
      input: {
        index: fileURLToPath(new URL('./index.html', import.meta.url)),
        dashboard: fileURLToPath(new URL('./dashboard.html', import.meta.url))
      }
    }
  },
  server: {
    port: 5174,
    strictPort: true,
    fs: { allow: ['..'] }
  },
  clearScreen: false,
  envPrefix: ['VITE_', 'TAURI_']
})
