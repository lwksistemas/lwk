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
export const LOGIN_BACKGROUND_PATHS = {
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

type LoginBackgroundKey = keyof typeof LOGIN_BACKGROUND_PATHS;

/** Cor sólida exibida instantaneamente enquanto o JPEG progresivo carrega */
const FALLBACK_COLORS: Record<LoginBackgroundKey, string> = {
  clinicaBeleza: '#3d1a24',
  clinicaEstetica: '#4a2035',
  cabeleireiro: '#2c1810',
  hotel: '#1a2744',
  restaurante: '#3d2218',
  crm: '#1e3a5f',
  servicos: '#2a3441',
  commerce: '#2d2d2d',
  default: '#1f2937',
};

/** Cor primária para UI da tela de login — baseada na imagem de fundo padrão */
export const LOGIN_THEME_COLORS: Record<LoginBackgroundKey, string> = {
  clinicaBeleza: '#c4737b',
  clinicaEstetica: '#9b5d7a',
  cabeleireiro: '#8b6b4a',
  hotel: '#4a7ab5',
  restaurante: '#b5704a',
  crm: '#3b7d5c',
  servicos: '#5a7a8a',
  commerce: '#6a6a6a',
  default: '#4a6a8a',
};

export function getLoginThemeColor(tipoLojaNome: string): string {
  const tipo = (tipoLojaNome || '').trim();
  if (isTipoClinicaBeleza(tipo)) return LOGIN_THEME_COLORS.clinicaBeleza;
  if (isTipoClinicaEstetica(tipo)) return LOGIN_THEME_COLORS.clinicaEstetica;
  if (isTipoCabeleireiro(tipo)) return LOGIN_THEME_COLORS.cabeleireiro;
  if (isTipoHotel(tipo)) return LOGIN_THEME_COLORS.hotel;
  if (isTipoRestaurante(tipo)) return LOGIN_THEME_COLORS.restaurante;
  if (isTipoCRMVendas(tipo)) return LOGIN_THEME_COLORS.crm;
  if (isTipoServicos(tipo)) return LOGIN_THEME_COLORS.servicos;
  if (isTipoCommerce(tipo)) return LOGIN_THEME_COLORS.commerce;
  return LOGIN_THEME_COLORS.default;
}

const LOCAL = LOGIN_BACKGROUND_PATHS;

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

function backgroundKeyFromPath(path: string): LoginBackgroundKey {
  const entry = Object.entries(LOCAL).find(([, url]) => url === path);
  return (entry?.[0] as LoginBackgroundKey) ?? 'default';
}

export function getLoginBackgroundFallbackColor(imageUrl: string): string {
  if (!imageUrl) return FALLBACK_COLORS.default;
  const localPath = Object.values(LOCAL).find((p) => imageUrl === p || imageUrl.endsWith(p));
  if (localPath) return FALLBACK_COLORS[backgroundKeyFromPath(localPath)];
  return FALLBACK_COLORS.default;
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
  if (s.includes('hotel') || s.includes('pousada')) return LOCAL.hotel;
  if (s.includes('restaurante') || s.includes('bar') || s.includes('food')) return LOCAL.restaurante;
  if (s.includes('crm') || s.includes('vendas')) return LOCAL.crm;
  if (s.includes('servico')) return LOCAL.servicos;
  if (s.includes('commerce') || s.includes('ecommerce') || s.includes('loja')) return LOCAL.commerce;

  return LOCAL.default;
}

export function getLoginBackgroundFallbackFromSlug(slug: string): string {
  return getLoginBackgroundFallbackColor(getLoginBackgroundHintFromSlug(slug));
}

/** Preload no navegador (fire-and-forget). */
export function preloadLoginBackground(url: string): void {
  if (typeof window === 'undefined' || !url) return;
  const img = new window.Image();
  img.decoding = 'async';
  img.fetchPriority = 'high';
  img.src = url;
}

/** Preload de todos os fundos locais (opcional — útil em build/preview). */
export function preloadAllDefaultLoginBackgrounds(): void {
  Object.values(LOCAL).forEach(preloadLoginBackground);
}
