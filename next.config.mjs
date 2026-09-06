/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  transpilePackages: ['three', 'react-globe.gl', 'globe.gl'],
  experimental: {
    workerThreads: false,
  },
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.externals.push('@mongodb-js/zstd', 'kerberos', 'mongodb-client-encryption');
    }
    return config;
  },
  // Optimize for deployment
  // Increase timeout for API routes
  serverRuntimeConfig: {
    maxDuration: 300, // 5 minutes
  },
  // Configure for Render deployment
  env: {
    FASTAPI_BASE_URL: "https://varuna-sonar-backend.onrender.com",
    NEXT_PUBLIC_API_URL: "https://varuna-sonar-backend.onrender.com",
    NEXT_PUBLIC_BACKEND_URL: "https://varuna-sonar-backend.onrender.com",
    CUSTOM_KEY: process.env.CUSTOM_KEY,
    PORT: process.env.PORT,
  },
  async rewrites() {
    return [
      {
        source: "/static/uploads/:path*",
        destination: "https://varuna-sonar-backend.onrender.com/static/uploads/:path*",
      },
      {
        source: "/static/thumbnails/:path*",
        destination: "https://varuna-sonar-backend.onrender.com/static/thumbnails/:path*",
      },
      {
        source: "/backend-api/:path*",
        destination: "https://varuna-sonar-backend.onrender.com/api/:path*",
      },
    ];
  },
}

export default nextConfig
