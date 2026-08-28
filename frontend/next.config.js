const { extraConnectSrcOrigins, MEMED_HTTPS } = require('./lib/csp-policy');

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
  extraConnectSrcOrigins().forEach((o) => origins.add(o));
  return Array.from(origins).join(' ');
}

const memedHttps = MEMED_HTTPS.join(' ');

const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "base-uri 'self'",
      "object-src 'none'",
      "frame-ancestors 'none'",
      "form-action 'self'",
      `script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: ${memedHttps} https://meet.jit.si https://8x8.vc`,
      `style-src 'self' 'unsafe-inline' ${memedHttps} https://meet.jit.si`,
      `img-src 'self' data: blob: https://media.lwksistemas.com.br https://i.pravatar.cc ${memedHttps} https://meet.jit.si https://*.jitsi.net`,
      `font-src 'self' data: ${memedHttps} https://meet.jit.si`,
      `connect-src ${buildConnectSrc()}`,
      "media-src 'self' blob: mediastream:",
      `frame-src 'self' ${memedHttps} https://meet.jit.si https://8x8.vc https://*.jitsi.net`,
      `child-src 'self' blob: ${memedHttps} https://meet.jit.si https://8x8.vc`,
      `worker-src 'self' blob: ${memedHttps} https://meet.jit.si`,
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
    value: 'camera=(self "https://meet.jit.si" "https://8x8.vc"), microphone=(self "https://meet.jit.si" "https://8x8.vc"), geolocation=(), payment=(), usb=(), browsing-topics=()',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
];

/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  output: "standalone",
  // Garante alias @/ no webpack (Next 16)
  webpack: (config) => {
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@': path.resolve(__dirname),
    };
    return config;
  },
  reactStrictMode: true,
  experimental: {
    cpus: 1,
  },
  poweredByHeader: false,

  // Next 16: lint não roda no build; use `npm run lint`. TS: ignorar erros no CI/Vercel.
  typescript: {
    ignoreBuildErrors: true,
  },
  

  // Otimizações de performance
  compress: true,
  
  // Otimizar imagens (remotePatterns para Next 14+)
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'i.pravatar.cc', pathname: '/**' },
      { protocol: 'https', hostname: 'api.lwksistemas.com.br', pathname: '/**' },
      { protocol: 'https', hostname: 'media.lwksistemas.com.br', pathname: '/**' },
      { protocol: 'http', hostname: 'localhost', pathname: '/**' },
    ],
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60,
  },
  
  // Otimizar compilação
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
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
        destination: '/loja/:slug/clinica-beleza/prontuario',
        permanent: true,
      },
      {
        source: '/loja/:slug/clinica-geral',
        destination: '/loja/:slug/clinica',
        permanent: false,
      },
      {
        source: '/loja/:slug/clinica-geral/:path*',
        destination: '/loja/:slug/clinica/:path*',
        permanent: false,
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
