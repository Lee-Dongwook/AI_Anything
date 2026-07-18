import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The demo app lives under `demo-app/`. Both the dev server (`npm run dev`) and the
// static preview server (`npm run preview`, used by Playwright's webServer) bind to
// port 4173 so specs can target a single stable baseURL.
export default defineConfig({
  root: "demo-app",
  plugins: [react()],
  server: { port: 4173, strictPort: true },
  preview: { port: 4173, strictPort: true },
});
