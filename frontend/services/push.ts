/**
 * Registro de push notifications (VAPID).
 * Requer NEXT_PUBLIC_VAPID_PUBLIC_KEY no .env.
 * Usa token do sessionStorage (apiClient) se não passar token.
 */
import apiClient from '@/lib/api-client';

export async function registerPush(token?: string): Promise<boolean> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return false;
  const vapidKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;
  if (!vapidKey) {
    console.warn('NEXT_PUBLIC_VAPID_PUBLIC_KEY não configurada');
    return false;
  }

  try {
    const reg = await navigator.serviceWorker.ready;
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') return false;

    const subscription = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey),
    });

    const payload = subscription.toJSON ? subscription.toJSON() : {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
        auth: arrayBufferToBase64(subscription.getKey('auth')),
      },
    };

    await apiClient.post('push/subscribe/', {
      endpoint: payload.endpoint,
      keys: payload.keys,
    }, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined);
    return true;
  } catch (e) {
    console.error('Erro ao registrar push:', e);
    return false;
  }
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const output = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) output[i] = rawData.charCodeAt(i);
  return output;
}

function arrayBufferToBase64(buffer: ArrayBuffer | null): string {
  if (!buffer) return '';
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
