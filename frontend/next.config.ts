import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 移除 output: "export" 以支持动态路由和API交互
  // output: "export",
  images: {
    unoptimized: true,
  },
  typescript: {
    // ignoreBuildErrors: true,
  },
  // 添加对API路由的支持
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5001/api/:path*',
      },
    ];
  },
};

export default nextConfig;
