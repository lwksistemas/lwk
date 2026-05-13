// Service Worker mínimo para habilitar instalação PWA
// Não faz cache offline — apenas permite que o navegador ofereça "Instalar App"

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Não intercepta requests — deixa passar direto para a rede
  return;
});
