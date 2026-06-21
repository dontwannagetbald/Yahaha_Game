import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "..", "");
  const apiProxyTarget = (
    env.VITE_API_PROXY_TARGET ||
    env.VITE_API_BASE_URL ||
    "http://localhost:8000"
  ).replace(/\/$/, "");

  return {
    envDir: "..",
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: apiProxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
