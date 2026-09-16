import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'

const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
const wsBackendUrl = backendUrl.replace(/^http/, 'ws')

export default defineConfig({
  plugins: [
    vue(),
    UnoCSS()
  ],
  server: {
    port: 5173,
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
