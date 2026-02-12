import { NextRequest } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE = API_URL.endsWith('/api') ? API_URL : `${API_URL}/api`;

interface LojaInfoPublica {
  nome: string;
  tipo_loja_nome?: string;
  cor_primaria?: string;
  cor_secundaria?: string;
  logo?: string;
}

export async function GET(request: NextRequest) {
  const slug = request.nextUrl.searchParams.get('slug');
  if (!slug?.trim()) {
    return new Response(
      JSON.stringify({ error: 'slug obrigatório' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  try {
    const res = await fetch(
      `${API_BASE}/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug.trim())}`,
      { cache: 'no-store' }
    );
    if (!res.ok) {
      return new Response(
        JSON.stringify({ error: 'Loja não encontrada' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }
    const loja: LojaInfoPublica = await res.json();
    const nome = loja.nome?.trim() || 'Loja';
    const shortName = nome.length > 20 ? nome.slice(0, 17) + '…' : nome;
    const themeColor = loja.cor_primaria?.trim() || '#ec4899';

    const manifest = {
      name: `${nome} - LWK Sistemas`,
      short_name: shortName,
      description: `Gestão ${loja.tipo_loja_nome || 'da loja'} - ${nome}`,
      start_url: '/',
      display: 'standalone',
      background_color: '#ffffff',
      theme_color: themeColor,
      orientation: 'portrait-primary',
      scope: '/',
      icons: [
        { src: '/icons/icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' },
        { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
        { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
      ],
    };

    return new Response(JSON.stringify(manifest), {
      headers: {
        'Content-Type': 'application/manifest+json',
        'Cache-Control': 'public, max-age=300',
      },
    });
  } catch (e) {
    console.error('Erro ao gerar manifest da loja:', e);
    return new Response(
      JSON.stringify({ error: 'Erro ao gerar manifest' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
