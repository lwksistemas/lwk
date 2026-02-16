/**
 * Adiciona listeners de push e notificationclick ao sw.js gerado pelo next-pwa.
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
if (content.includes('notificationclick')) {
  console.log('patch-sw-push: sw.js já contém push handlers.');
  process.exit(0);
}

const patch = `
self.addEventListener('push',function(e){if(!e.data)return;try{var d=e.data.json();}catch(err){return;}self.registration.showNotification(d.title||'Notificação',{body:d.body||'',icon:'/icons/icon-192.png',data:{url:d.url||'/'}});});
self.addEventListener('notificationclick',function(e){e.notification.close();var u=e.notification.data&&e.notification.data.url;e.waitUntil(self.clients.openWindow(u||'/').catch(function(){}));});
`;

fs.writeFileSync(swPath, content.trimEnd() + patch, 'utf8');
console.log('patch-sw-push: handlers de push adicionados ao sw.js');
