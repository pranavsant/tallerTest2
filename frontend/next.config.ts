import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
