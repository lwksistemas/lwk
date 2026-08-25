import { NextRequest } from 'next/server';
import { logger } from '@/lib/logger';
import { buildLojaManifest } from '@/lib/pwa-loja';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE = API_URL.endsWith('/api') ? API_URL : `${API_URL}/api`;

export async function GET(request: NextRequest) {
  const slug = request.nextUrl.searchParams.get('slug');
  if (!slug?.trim()) {
    return new Response(JSON.stringify({ error: 'slug obrigatório' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    const res = await fetch(
      `${API_BASE}/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug.trim())}`,
      { next: { revalidate: 300 } },
    );
    if (!res.ok) {
      return new Response(JSON.stringify({ error: 'Loja não encontrada' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    const loja = await res.json();
    return new Response(JSON.stringify(buildLojaManifest(slug, loja)), {
      headers: {
        'Content-Type': 'application/manifest+json',
        'Cache-Control': 'public, max-age=300',
      },
    });
  } catch (e) {
    logger.warn('Erro ao gerar manifest da loja:', e);
    return new Response(JSON.stringify({ error: 'Erro ao gerar manifest' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
