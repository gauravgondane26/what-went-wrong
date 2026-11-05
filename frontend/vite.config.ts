import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // docker-compose points this at the backend service (http://backend:8081).
        target: process.env.VITE_PROXY_TARGET ?? 'http://localhost:8081',
        changeOrigin: true,
      },
    },
  },
})
