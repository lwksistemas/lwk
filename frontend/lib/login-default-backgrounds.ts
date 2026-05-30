/**
 * Imagens de fundo padrão da tela de login por tipo de loja.
 * Usadas quando a loja não definiu login_background nas configurações.
 */
import {
  isTipoCabeleireiro,
  isTipoClinicaBeleza,
  isTipoClinicaEstetica,
  isTipoCommerce,
  isTipoCRMVendas,
  isTipoHotel,
  isTipoRestaurante,
  isTipoServicos,
} from '@/lib/loja-tipo';

/** Arquivos em /public/login-backgrounds/ — um por tipo de app */
const LOCAL = {
  clinicaBeleza: '/login-backgrounds/clinica-beleza.jpg',
  clinicaEstetica: '/login-backgrounds/clinica-estetica.jpg',
  cabeleireiro: '/login-backgrounds/cabeleireiro.jpg',
  hotel: '/login-backgrounds/hotel.jpg',
  restaurante: '/login-backgrounds/restaurante.jpg',
  crm: '/login-backgrounds/crm-vendas.jpg',
  servicos: '/login-backgrounds/servicos.jpg',
  commerce: '/login-backgrounds/commerce.jpg',
  default: '/login-backgrounds/default.jpg',
} as const;

/**
 * Retorna URL do fundo padrão conforme o tipo da loja (nome vindo da API).
 */
export function getDefaultLoginBackground(tipoLojaNome: string): string {
  const tipo = (tipoLojaNome || '').trim();
  if (isTipoClinicaBeleza(tipo)) return LOCAL.clinicaBeleza;
  if (isTipoClinicaEstetica(tipo)) return LOCAL.clinicaEstetica;
  if (isTipoCabeleireiro(tipo)) return LOCAL.cabeleireiro;
  if (isTipoHotel(tipo)) return LOCAL.hotel;
  if (isTipoRestaurante(tipo)) return LOCAL.restaurante;
  if (isTipoCRMVendas(tipo)) return LOCAL.crm;
  if (isTipoServicos(tipo)) return LOCAL.servicos;
  if (isTipoCommerce(tipo)) return LOCAL.commerce;
  return LOCAL.default;
}

export function resolveLoginBackground(
  tipoLojaNome: string,
  loginBackground?: string | null,
): string {
  const custom = (loginBackground ?? '').trim();
  if (custom) return custom;
  return getDefaultLoginBackground(tipoLojaNome);
}

/**
 * Chute imediato pelo slug da URL — exibe fundo antes da API responder.
 * Slugs conhecidos + heurísticas pelo nome.
 */
export function getLoginBackgroundHintFromSlug(slug: string): string {
  const s = (slug || '').toLowerCase().trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

  const exact: Record<string, string> = {
    beleza: LOCAL.clinicaBeleza,
  };
  if (exact[s]) return exact[s];

  if (s.includes('beleza')) return LOCAL.clinicaBeleza;
  if (s.includes('estetica')) return LOCAL.clinicaEstetica;
  if (s.includes('cabeleireiro') || s.includes('salao') || s.includes('barbearia')) return LOCAL.cabeleireiro;
  if (s.includes('hotel')) return LOCAL.hotel;
  if (s.includes('restaurante')) return LOCAL.restaurante;
  if (s.includes('crm') || s.includes('vendas')) return LOCAL.crm;
  if (s.includes('servico')) return LOCAL.servicos;
  if (s.includes('commerce') || s.includes('loja')) return LOCAL.commerce;

  return LOCAL.default;
}

/** Preload no navegador (fire-and-forget). */
export function preloadLoginBackground(url: string): void {
  if (typeof window === 'undefined' || !url) return;
  const img = new window.Image();
  img.decoding = 'async';
  img.fetchPriority = 'high';
  img.src = url;
}
