/**
 * Adiciona listeners de push e notificationclick ao sw.js gerado pelo next-pwa.
 * ✅ v1375: Também adiciona regras de no-cache para APIs de dados
 * Rodar após o build: "postbuild": "node scripts/patch-sw-push.js"
 */
const fs = require('fs');
const path = require('path');

const swPath = path.join(__dirname, '..', 'public', 'sw.js');
if (!fs.existsSync(swPath)) {
  console.warn('patch-sw-push: public/sw.js não encontrado (build ainda não rodou?)');
  process.exit(0);
}

let content = fs.readFileSync(swPath, 'utf8');

// Patch 1: Push notifications
let needsPushPatch = !content.includes('notificationclick');
if (needsPushPatch) {
  const pushPatch = `
self.addEventListener('push',function(e){if(!e.data)return;try{var d=e.data.json();}catch(err){return;}self.registration.showNotification(d.title||'Notificação',{body:d.body||'',icon:'/icons/icon-192.png',data:{url:d.url||'/'}});});
self.addEventListener('notificationclick',function(e){e.notification.close();var u=e.notification.data&&e.notification.data.url;e.waitUntil(self.clients.openWindow(u||'/').catch(function(){}));});
`;
  content = content.trimEnd() + pushPatch;
  console.log('✅ patch-sw-push: handlers de push adicionados ao sw.js');
}

// Patch 2: No-cache para APIs (v1375)
let needsNoCachePatch = !content.includes('NO_CACHE_API_PATTERNS');
if (needsNoCachePatch) {
  const noCachePatch = `

// ✅ v1375: NUNCA cachear endpoints de API de dados
const NO_CACHE_API_PATTERNS = [
  /\\/api\\/crm-vendas\\//,
  /\\/api\\/clinica-estetica\\//,
  /\\/api\\/clinica-beleza\\//,
  /\\/api\\/restaurante\\//,
  /\\/api\\/ecommerce\\//,
  /\\/api\\/servicos\\//,
  /\\/api\\/cabeleireiro\\//,
];

// Interceptar fetch ANTES de qualquer cache
const originalFetch = self.fetch;
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Verificar se é endpoint de API que não deve ser cacheado
  const shouldNotCache = NO_CACHE_API_PATTERNS.some(pattern => pattern.test(url.pathname));
  
  if (shouldNotCache) {
    // NetworkOnly - NUNCA cachear, sempre buscar do servidor
    event.respondWith(
      fetch(event.request.clone(), {
        cache: 'no-store'
      }).catch((error) => {
        console.error('[SW v1375] Erro ao buscar API:', url.pathname, error);
        // Se falhar, retornar erro (não usar cache)
        return new Response(
          JSON.stringify({ error: 'Sem conexão com o servidor', offline: true }),
          {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
          }
        );
      })
    );
  }
  // Para outras requisições, deixar o workbox lidar
}, true); // true = capturar na fase de captura (antes do workbox)

console.log('[SW v1375] Service Worker com no-cache para APIs carregado');
`;
  content = content.trimEnd() + noCachePatch;
  console.log('✅ patch-sw-push: regras de no-cache para APIs adicionadas (v1375)');
}

// Salvar arquivo modificado
fs.writeFileSync(swPath, content, 'utf8');

if (!needsPushPatch && !needsNoCachePatch) {
  console.log('ℹ️  patch-sw-push: sw.js já contém todos os patches necessários');
} else {
  console.log('✅ patch-sw-push: sw.js patcheado com sucesso!');
}
