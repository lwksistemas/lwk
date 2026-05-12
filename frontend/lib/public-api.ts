import axios from 'axios';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

/**
 * GET público à API (sem interceptors de sessão/refresh).
 * Timeout curto para ecrãs de login não ficarem presos em «Carregando...».
 */
export async function getPublicApiJson<T>(path: string, timeoutMs = 8000): Promise<T> {
  const base = getPrimaryApiBaseUrl();
  const p = path.startsWith('/') ? path : `/${path}`;
  const { data } = await axios.get<T>(`${base}${p}`, {
    timeout: timeoutMs,
    headers: { 'Content-Type': 'application/json' },
    params: { _t: Date.now() },
  });
  return data;
}
