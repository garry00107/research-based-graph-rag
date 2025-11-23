import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8002/:path*',
      },
    ];
  },
  experimental: {
    proxyTimeout: 300000, // 5 minutes
  },
};

export default nextConfig;
