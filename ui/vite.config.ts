import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import envPlugin from 'vite-plugin-environment'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    envPlugin({
      FOXOPS_API_URL: ''
    })
  ]
})
