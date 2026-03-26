const withPWA = require("@ducanh2912/next-pwa").default({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
  // ✅ v1375: Desabilitar service worker gerado automaticamente
  // Vamos usar apenas o sw.js padrão sem customização por enquanto
  // para evitar conflitos com precaching
  cacheOnFrontEndNav: true,
  aggressiveFrontEndNavCaching: false,
  reloadOnOnline: true,
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Otimizações de performance
  compress: true,
  
  // Otimizar imagens (remotePatterns para Next 14+)
  images: {
    domains: ['localhost', 'i.pravatar.cc', 'res.cloudinary.com'],
    remotePatterns: [
      { protocol: 'https', hostname: 'i.pravatar.cc', pathname: '/**' },
      { protocol: 'https', hostname: 'res.cloudinary.com', pathname: '/**' },
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
    NEXT_PUBLIC_BUILD_ID: 'v1375-no-cache-fix',
    NEXT_PUBLIC_VERSION: '1375',
    NEXT_PUBLIC_SW_VERSION: 'v1375', // ✅ Versão do SW para forçar atualização
  },
  
  // Gerar build ID único para invalidar cache COMPLETAMENTE
  generateBuildId: async () => {
    // ✅ v1375: Forçar atualização do service worker e limpar cache antigo
    return 'v1375-no-cache-fix-' + Date.now();
  },
}

module.exports = withPWA(nextConfig);
