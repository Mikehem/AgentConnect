import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@mui/material', '@emotion/react'],
          query: ['@tanstack/react-query'],
        },
      },
    },
  },
  server: {
    port: 7000,
    proxy: {
      '/api': {
        target: 'http://localhost:7001',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:7001',
        ws: true,
      },
    },
  },
  define: {
    global: 'globalThis',
  },
})
