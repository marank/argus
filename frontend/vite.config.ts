import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

const backend = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000'
// Keep the browser's Host header so Django's CSRF origin check sees a same-origin request.
const proxy = { target: backend, changeOrigin: false }

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // Same-origin requests in development: session cookie and CSRF just work.
    proxy: {
      '/api': proxy,
      '/admin': proxy,
      '/static': proxy,
    },
  },
})
