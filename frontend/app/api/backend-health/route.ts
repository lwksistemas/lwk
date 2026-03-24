import { NextRequest } from 'next/server';

/** Mesma regra que SeletorServidorBackend: evita /api/api/ quando o env já termina em /api */
function healthBaseUrl(url: string): string {
  return url.replace(/\/api\/?$/, '');
}

const HEALTH_TIMEOUT_MS = 45000;

/**
 * Health check via servidor Next (sem CORS).
 * Só aceita `server=heroku|render` e usa apenas URLs dos envs — evita SSRF.
 */
export async function GET(request: NextRequest) {
  const server = request.nextUrl.searchParams.get('server');
  if (server !== 'heroku' && server !== 'render') {
    return new Response(JSON.stringify({ error: 'Parâmetro server inválido' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const primary = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').trim();
  const backup = (process.env.NEXT_PUBLIC_API_BACKUP_URL || '').trim();

  if (server === 'render' && !backup) {
    return new Response(JSON.stringify({ ok: false, configured: false }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const root = server === 'render' ? backup : primary;
  const healthUrl = `${healthBaseUrl(root)}/api/superadmin/health/`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);

  try {
    const res = await fetch(healthUrl, {
      method: 'GET',
      signal: controller.signal,
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });
    clearTimeout(timeoutId);
    return new Response(
      JSON.stringify({ ok: res.ok, status: res.status, configured: true }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch {
    clearTimeout(timeoutId);
    return new Response(
      JSON.stringify({ ok: false, error: 'network', configured: true }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
