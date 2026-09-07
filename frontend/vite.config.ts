import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // react-helmet-async breaks Vite's dependency pre-bundling because it
  // pokes at internal scheduler state at import time.  Including it in
  // `optimizeDeps.include` forces Vite to bundle it ahead of time so the
  // import side-effect runs in a worker, not in the main thread.
  optimizeDeps: {
    include: ["react-helmet-async"],
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/static": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});