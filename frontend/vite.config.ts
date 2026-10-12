import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    // The FastAPI back end runs on port 8000 during development.
    proxy: { '/api': 'http://localhost:8000' },
  },
})
