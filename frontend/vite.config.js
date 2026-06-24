import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/echarts')) return 'vendor-echarts'
          if (id.includes('node_modules/@antv') || id.includes('node_modules/@ant-design')) return 'vendor-g6'
          if (id.includes('node_modules/three') || id.includes('node_modules/@tresjs')) return 'vendor-3d'
          if (id.includes('node_modules/@vue-flow')) return 'vendor-vue-flow'
          if (id.includes('node_modules/@tsparticles')) return 'vendor-particles'
          if (id.includes('node_modules/vue')) return 'vendor-vue'
          if (id.includes('node_modules')) return 'vendor'
        }
      }
    }
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
