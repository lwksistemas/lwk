function buildConnectSrc() {
  const origins = new Set(["'self'"]);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
  if (apiUrl) {
    try {
      const u = new URL(apiUrl.replace(/\/api\/?$/, ''));
      origins.add(u.origin);
    } catch {
      /* ignore */
    }
  }
  [
    'https://api.lwksistemas.com.br',
    'https://lwks-backend-production.up.railway.app',
    'https://lwks-backend-staging-staging.up.railway.app',
    'https://viacep.com.br',
    'https://brasilapi.com.br',
    'https://memed.com.br',
    'https://*.memed.com.br',
    'wss://*.memed.com.br',
    'https://api.cloudinary.com',
    'https://*.cloudinary.com',
  ].forEach((o) => origins.add(o));
  return Array.from(origins).join(' ');
}

const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "base-uri 'self'",
      "object-src 'none'",
      "frame-ancestors 'none'",
      "form-action 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://memed.com.br https://*.memed.com.br https://upload-widget.cloudinary.com https://widget.cloudinary.com",
      "style-src 'self' 'unsafe-inline' https://*.memed.com.br https://upload-widget.cloudinary.com",
      "img-src 'self' data: blob: https://res.cloudinary.com https://*.cloudinary.com https://i.pravatar.cc https://*.memed.com.br",
      "font-src 'self' data: https://*.memed.com.br https://*.cloudinary.com",
      `connect-src ${buildConnectSrc()}`,
      "frame-src 'self' https://memed.com.br https://*.memed.com.br https://upload-widget.cloudinary.com https://widget.cloudinary.com https://*.cloudinary.com",
      "child-src 'self' blob: https://memed.com.br https://*.memed.com.br https://upload-widget.cloudinary.com https://widget.cloudinary.com",
      "worker-src 'self' blob: https://*.memed.com.br",
      "upgrade-insecure-requests",
    ].join('; '),
  },
  {
    key: 'Cross-Origin-Opener-Policy',
    value: 'same-origin',
  },
  {
    key: 'Cross-Origin-Resource-Policy',
    value: 'same-site',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(self), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  
  // Ignorar erros de ESLint durante o build (necessário para Vercel)
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Ignorar erros de TypeScript durante o build
  typescript: {
    ignoreBuildErrors: true,
  },
  
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
            value: '0'
          },
          ...securityHeaders,
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
      {
        source: '/loja/:slug/clinica-estetica/agenda',
        destination: '/loja/:slug/agenda',
        permanent: true,
      },
      {
        source: '/loja/:slug/clinica-estetica/configuracoes/:path*',
        destination: '/loja/:slug/clinica-beleza/configuracoes/:path*',
        permanent: true,
      },
      {
        source: '/loja/:slug/clinica-estetica',
        destination: '/loja/:slug/clinica-beleza/consultas',
        permanent: true,
      },
    ]
  },
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_BUILD_ID: process.env.NEXT_PUBLIC_BUILD_ID || process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 8) || 'dev',
    NEXT_PUBLIC_VERSION: process.env.NEXT_PUBLIC_VERSION || '1390',
    NEXT_PUBLIC_SW_VERSION: process.env.NEXT_PUBLIC_SW_VERSION || 'v1390',
    NEXT_PUBLIC_PWA_ENABLED: process.env.NEXT_PUBLIC_PWA_ENABLED || 'false',
  },
  
  // Build ID: usa commit SHA (Vercel injeta VERCEL_GIT_COMMIT_SHA) ou env explícito.
  generateBuildId: async () => {
    return process.env.NEXT_PUBLIC_BUILD_ID || process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 8) || 'dev';
  },
}

module.exports = nextConfig;
