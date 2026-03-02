const withPWA = require("@ducanh2912/next-pwa").default({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Otimizações de performance
  compress: true,
  
  // Otimizar imagens (remotePatterns para Next 14+)
  images: {
    domains: ['localhost', 'i.pravatar.cc'],
    remotePatterns: [
      { protocol: 'https', hostname: 'i.pravatar.cc', pathname: '/**' },
    ],
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60,
  },
  
  // Otimizar compilação
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // ✅ OTIMIZAÇÃO: Webpack optimization
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          commons: {
            name: 'commons',
            chunks: 'all',
            minChunks: 2,
          },
        },
      };
    }
    return config;
  },
  
  // Headers de cache
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
        ],
      },
    ]
  },
  
  // Redirects para nomenclatura atualizada
  async redirects() {
    return [
      {
        source: '/superadmin/tipos-loja',
        destination: '/superadmin/tipos-app',
        permanent: true,
      },
    ]
  },
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_BUILD_ID: 'v258-restaurante-dashboard',
    NEXT_PUBLIC_VERSION: '258',
  },
  
  // Gerar build ID único para invalidar cache COMPLETAMENTE
  generateBuildId: async () => {
    // Usar timestamp + versão para garantir unicidade (dashboard Restaurante v258)
    return 'v258-restaurante-' + Date.now();
  },
}

module.exports = withPWA(nextConfig);
