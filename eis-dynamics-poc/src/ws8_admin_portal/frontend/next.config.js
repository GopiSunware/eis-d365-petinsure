/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // Environment variables are loaded from .env.local (local) or environment (cloud)
  // No hardcoded fallbacks - configuration must be explicit
};

module.exports = nextConfig;
