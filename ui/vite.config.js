import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const serverUrl = (env.VITE_SERVER_URL || 'http://localhost:8000').replace(/\/$/, '')
  const apiPath = env.VITE_API_PATH || '/v1'
  const proxyKey = apiPath.startsWith('/') ? apiPath : `/${apiPath}`

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        [proxyKey]: {
          target: serverUrl,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    preview: {
      port: 5173,
    },
  }
})
