import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import envPlugin from 'vite-plugin-environment'
import tsconfigPaths from 'vite-tsconfig-paths'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    envPlugin({
      FOXOPS_API_URL: "",
      FOXOPS_STATIC_TOKEN: "",
      FOXOPS_STATIC_USERNAME: "",
      FOXOPS_STATIC_GROUPS: "",
    }),
    tsconfigPaths(),
  ],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
      },
      "/auth/test": {
        target: "http://localhost:5001",
        changeOrigin: true,
      },
    },
  },
});
