import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for the Docker multi-stage build: produces .next/standalone/server.js
  output: "standalone",

  // Proxy /api/backend/* to the FastAPI server during development
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination:
          (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000") +
          "/:path*",
      },
    ];
  },
};

export default nextConfig;
