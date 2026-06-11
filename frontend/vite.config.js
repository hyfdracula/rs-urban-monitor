import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(__dirname, '..')

function manualChunks(id) {
  if (!id.includes('node_modules')) return undefined
  if (id.includes('mapbox-gl') || id.includes('@mapbox')) return 'mapbox'
  if (id.includes('zrender')) return 'zrender'
  if (id.includes('echarts')) return 'echarts'
  if (id.includes('element-plus') || id.includes('@element-plus')) return 'element-plus'
  if (id.includes('vue') || id.includes('@vue')) return 'vue'
  if (id.includes('jspdf')) return 'jspdf'
  if (id.includes('html2canvas')) return 'html2canvas'
  if (id.includes('canvg')) return 'canvg'
  return 'vendor'
}

export default defineConfig({
  root: projectRoot,
  envDir: projectRoot,
  publicDir: resolve(__dirname, 'public'),
  base: process.env.VITE_BASE || '/',
  plugins: [vue()],
  build: {
    outDir: resolve(projectRoot, 'dist'),
    emptyOutDir: true,
    chunkSizeWarningLimit: 1800,
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: ['.ngrok-free.dev'],
    proxy: {
      '/geoserver': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
