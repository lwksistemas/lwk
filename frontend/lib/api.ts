import { headers } from 'next/headers';
import { getPrimaryApiBaseUrlFromHost } from './api-base';

const FETCH_TIMEOUT = 10000; // 10s para produção

async function resolveHomepageApiBase(): Promise<string> {
  try {
    const host = (await headers()).get('host') ?? '';
    if (host) return getPrimaryApiBaseUrlFromHost(host);
  } catch {
    // fora do contexto de request (build estático, etc.)
  }
  const envRoot =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/?$/, '') || 'http://localhost:8000';
  return `${envRoot}/api`;
}

export async function getHomepage() {
  const API_BASE = await resolveHomepageApiBase();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);

  try {
    const res = await fetch(`${API_BASE}/homepage/`, {
      next: { revalidate: 300 }, // Cache por 5 minutos — reduz Function Invocations
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`Erro ao carregar homepage: ${res.status}`);
    }

    return res.json();
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}
