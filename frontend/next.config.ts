import type { NextConfig } from "next";

// The browser only talks to this app's own origin. Requests to /api/* are forwarded to
// the FastAPI backend, so the session cookie is first-party and no CORS is needed.
const API_ORIGIN = (process.env.API_ORIGIN || "http://localhost:8050").replace(/\/$/, "");

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_ORIGIN}/api/:path*` }];
  },
};

export default nextConfig;
