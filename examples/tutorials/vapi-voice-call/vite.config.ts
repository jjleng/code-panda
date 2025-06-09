import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    hmr: {
      overlay: false,
    },
    watch: {
      // Use polling instead of native file system events (more reliable for some environments)
      usePolling: false,
      // Wait 500ms before triggering a rebuild (gives time for all files to be flushed)
      interval: 500,
      // Additional delay between file change detection and reload
      binaryInterval: 500,
    },
  },
});
