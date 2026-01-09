/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Only use static export for production builds (set STATIC_EXPORT=true)
  ...(process.env.STATIC_EXPORT === 'true' ? { output: 'export' } : {}),
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Environment variables are loaded from .env.local (local) or .env.production (cloud)
};

module.exports = nextConfig;
