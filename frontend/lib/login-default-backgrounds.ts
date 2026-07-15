/**
 * Imagens de fundo padrão da tela de login por tipo de loja.
 * Usadas quando a loja não definiu login_background nas configurações.
 */
import {
  isTipoCabeleireiro,
  isTipoClinicaBeleza,
  isTipoCRMVendas,
  isTipoHotel,
} from '@/lib/loja-tipo';

/** Arquivos em /public/login-backgrounds/ — um por tipo de app ativo */
export const LOGIN_BACKGROUND_PATHS = {
  clinicaBeleza: '/login-backgrounds/clinica-beleza.jpg',
  hotel: '/login-backgrounds/hotel.jpg',
  crm: '/login-backgrounds/crm-vendas.jpg',
  /** Reusa visual clínica até haver asset dedicado do salão */
  salao: '/login-backgrounds/clinica-beleza.jpg',
  default: '/login-backgrounds/default.jpg',
} as const;

type LoginBackgroundKey = keyof typeof LOGIN_BACKGROUND_PATHS;

/** Cor sólida exibida instantaneamente enquanto o JPEG progressivo carrega */
const FALLBACK_COLORS: Record<LoginBackgroundKey, string> = {
  clinicaBeleza: '#3d1a24',
  hotel: '#1a2744',
  crm: '#1e3a5f',
  salao: '#4A3042',
  default: '#1f2937',
};

/** Cor primária para UI da tela de login — baseada na imagem de fundo padrão */
export const LOGIN_THEME_COLORS: Record<LoginBackgroundKey, string> = {
  clinicaBeleza: '#c4737b',
  hotel: '#4a7ab5',
  crm: '#3b7d5c',
  salao: '#4A3042',
  default: '#4a6a8a',
};

export function getLoginThemeColor(tipoLojaNome: string): string {
  const tipo = (tipoLojaNome || '').trim();
  if (isTipoClinicaBeleza(tipo)) return LOGIN_THEME_COLORS.clinicaBeleza;
  if (isTipoCabeleireiro(tipo)) return LOGIN_THEME_COLORS.salao;
  if (isTipoHotel(tipo)) return LOGIN_THEME_COLORS.hotel;
  if (isTipoCRMVendas(tipo)) return LOGIN_THEME_COLORS.crm;
  return LOGIN_THEME_COLORS.default;
}

const LOCAL = LOGIN_BACKGROUND_PATHS;

/**
 * Retorna URL do fundo padrão conforme o tipo da loja (nome vindo da API).
 */
export function getDefaultLoginBackground(tipoLojaNome: string): string {
  const tipo = (tipoLojaNome || '').trim();
  if (isTipoClinicaBeleza(tipo)) return LOCAL.clinicaBeleza;
  if (isTipoCabeleireiro(tipo)) return LOCAL.salao;
  if (isTipoHotel(tipo)) return LOCAL.hotel;
  if (isTipoCRMVendas(tipo)) return LOCAL.crm;
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

  if (s.includes('beleza') || s.includes('estetica')) return LOCAL.clinicaBeleza;
  if (s.includes('salao') || s.includes('cabeleireiro') || s.includes('lumina')) return LOCAL.salao;
  if (s.includes('hotel') || s.includes('pousada')) return LOCAL.hotel;
  if (s.includes('crm') || s.includes('vendas')) return LOCAL.crm;

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

/** Preload aguardável — evita piscada ao trocar a URL do fundo. */
export function preloadImageUrl(url: string): Promise<void> {
  if (typeof window === 'undefined' || !url) return Promise.resolve();
  return new Promise((resolve) => {
    const img = new window.Image();
    img.decoding = 'async';
    img.fetchPriority = 'high';
    img.onload = () => resolve();
    img.onerror = () => resolve();
    img.src = url;
  });
}

const lojaTipoCacheKey = (slug: string) => `loja_tipo_${slug}`;
const lojaLoginBgCacheKey = (slug: string) => `loja_login_bg_${slug}`;

/** Persiste tipo/fundo customizado para abrir login sem piscada na 2ª visita. */
export function cacheLojaLoginContext(
  slug: string,
  tipoLojaNome: string,
  loginBackground?: string | null,
): void {
  if (typeof window === 'undefined' || !slug) return;
  sessionStorage.setItem(lojaTipoCacheKey(slug), (tipoLojaNome || '').trim());
  const custom = (loginBackground ?? '').trim();
  if (custom) sessionStorage.setItem(lojaLoginBgCacheKey(slug), custom);
  else sessionStorage.removeItem(lojaLoginBgCacheKey(slug));
}

/**
 * Fundo imediato: cache da visita anterior ou heurística pelo slug.
 */
export function getInitialLoginBackgroundForSlug(slug: string): string {
  if (typeof window !== 'undefined') {
    const tipo = sessionStorage.getItem(lojaTipoCacheKey(slug));
    if (tipo) {
      const custom = sessionStorage.getItem(lojaLoginBgCacheKey(slug));
      return resolveLoginBackground(tipo, custom);
    }
  }
  return getLoginBackgroundHintFromSlug(slug);
}

export function getInitialLoginBackgroundFallbackForSlug(slug: string): string {
  return getLoginBackgroundFallbackColor(getInitialLoginBackgroundForSlug(slug));
}

/** Preload de todos os fundos locais (opcional — útil em build/preview). */
export function preloadAllDefaultLoginBackgrounds(): void {
  Object.values(LOCAL).forEach(preloadLoginBackground);
}
