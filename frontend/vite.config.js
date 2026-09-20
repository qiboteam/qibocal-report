import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'

const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
const wsBackendUrl = backendUrl.replace(/^http/, 'ws')

const rawBase = process.env.BASE_PATH || process.env.VITE_BASE_PATH
const base = rawBase !== undefined && rawBase !== ''
  ? (rawBase.endsWith('/') ? rawBase : `${rawBase}/`)
  : './'

export default defineConfig({
  base,
  plugins: [
    vue(),
    UnoCSS()
  ],
  server: {
    port: 5173,
    fs: {
      allow: ['..']
    },
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true
      },
      '/ws': {
        target: wsBackendUrl,
        ws: true,
        changeOrigin: true
      }
    }
  }
})
