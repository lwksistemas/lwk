// Service Worker Customizado - v1375
// Correção: NUNCA cachear endpoints de API de dados

// Importar workbox
importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js');

const CACHE_VERSION = 'v1375';
const API_CACHE_NAME = `api-cache-${CACHE_VERSION}`;
const STATIC_CACHE_NAME = `static-cache-${CACHE_VERSION}`;

// Configurar workbox
workbox.setConfig({
  debug: false,
});

// Ativar imediatamente
self.skipWaiting();
workbox.core.clientsClaim();

// ✅ CRÍTICO: NUNCA cachear endpoints de API de dados
// Lista de endpoints que NUNCA devem ser cacheados
const NO_CACHE_API_PATTERNS = [
  /\/api\/crm-vendas\/vendedores/,
  /\/api\/crm-vendas\/oportunidades/,
  /\/api\/crm-vendas\/propostas/,
  /\/api\/crm-vendas\/contatos/,
  /\/api\/crm-vendas\/contas/,
  /\/api\/crm-vendas\/customers/,
  /\/api\/crm-vendas\/leads/,
  /\/api\/crm-vendas\/atividades/,
  /\/api\/crm-vendas\/produtos-servicos/,
  /\/api\/crm-vendas\/contratos/,
  /\/api\/crm-vendas\/relatorios/,
  /\/api\/crm-vendas\/dashboard/,
  /\/api\/clinica-estetica\//,
  /\/api\/restaurante\//,
  /\/api\/ecommerce\//,
  /\/api\/servicos\//,
];

// Função para verificar se URL não deve ser cacheada
function shouldNotCache(url) {
  return NO_CACHE_API_PATTERNS.some(pattern => pattern.test(url.pathname));
}

// ✅ Estratégia NetworkOnly para APIs de dados (NUNCA cachear)
workbox.routing.registerRoute(
  ({ url, request }) => {
    return shouldNotCache(url);
  },
  new workbox.strategies.NetworkOnly({
    plugins: [
      {
        // Adicionar headers no-cache na requisição
        requestWillFetch: async ({ request }) => {
          const headers = new Headers(request.headers);
          headers.set('Cache-Control', 'no-cache, no-store, must-revalidate');
          headers.set('Pragma', 'no-cache');
          headers.set('Expires', '0');
          
          return new Request(request, { headers });
        },
      },
    ],
  })
);

// ✅ Estratégia NetworkFirst para outras APIs (com timeout curto)
workbox.routing.registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new workbox.strategies.NetworkFirst({
    cacheName: API_CACHE_NAME,
    networkTimeoutSeconds: 5,
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 10,
        maxAgeSeconds: 60, // Cache por apenas 1 minuto
      }),
      {
        // Não cachear respostas vazias ou com erro
        cacheWillUpdate: async ({ response }) => {
          if (!response) return null;
          if (response.status !== 200) return null;
          
          // Verificar se resposta é JSON vazio
          try {
            const clone = response.clone();
            const data = await clone.json();
            
            // Não cachear se count=0 ou results vazio
            if (data.count === 0 || (Array.isArray(data.results) && data.results.length === 0)) {
              console.log('[SW] Não cacheando resposta vazia:', response.url);
              return null;
            }
          } catch (e) {
            // Não é JSON, permitir cache
          }
          
          return response;
        },
      },
    ],
  })
);

// Cache de assets estáticos (imagens, fontes, etc.)
workbox.routing.registerRoute(
  ({ request }) => request.destination === 'image',
  new workbox.strategies.CacheFirst({
    cacheName: 'images',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 60,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 dias
      }),
    ],
  })
);

workbox.routing.registerRoute(
  ({ request }) => request.destination === 'font',
  new workbox.strategies.CacheFirst({
    cacheName: 'fonts',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 30,
        maxAgeSeconds: 365 * 24 * 60 * 60, // 1 ano
      }),
    ],
  })
);

// Cache de arquivos estáticos do Next.js
workbox.routing.registerRoute(
  ({ url }) => url.pathname.startsWith('/_next/static/'),
  new workbox.strategies.CacheFirst({
    cacheName: STATIC_CACHE_NAME,
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 365 * 24 * 60 * 60, // 1 ano
      }),
    ],
  })
);

// Limpar caches antigos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => {
            // Remover caches antigos (versões diferentes)
            return cacheName.includes('api-cache-') && cacheName !== API_CACHE_NAME ||
                   cacheName.includes('static-cache-') && cacheName !== STATIC_CACHE_NAME;
          })
          .map((cacheName) => {
            console.log('[SW] Removendo cache antigo:', cacheName);
            return caches.delete(cacheName);
          })
      );
    })
  );
});

// Push notifications
self.addEventListener('push', function(e) {
  if (!e.data) return;
  
  try {
    var d = e.data.json();
  } catch (err) {
    return;
  }
  
  self.registration.showNotification(d.title || 'Notificação', {
    body: d.body || '',
    icon: '/icons/icon-192.png',
    data: { url: d.url || '/' }
  });
});

self.addEventListener('notificationclick', function(e) {
  e.notification.close();
  var u = e.notification.data && e.notification.data.url;
  e.waitUntil(
    self.clients.openWindow(u || '/').catch(function() {})
  );
});

console.log('[SW] Service Worker v1375 carregado - APIs de dados NUNCA são cacheadas');
