/* Service worker só para o app ficar instalável. Sem cache. */
self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', () => {
  /* handler vazio: Chrome considera o app instalável; a rede segue normal */
});
