import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The admin UI only ever talks to the FastAPI service through its own
  // /api/proxy route handler, so no rewrites or CORS setup are needed here.
  reactStrictMode: true,
};

export default nextConfig;
