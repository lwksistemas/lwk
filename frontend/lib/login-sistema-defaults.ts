/**
 * Imagens e textos padrão das telas de login do sistema (Superadmin e Suporte).
 * Usados quando a API não retorna logo/fundo personalizados.
 *
 * No beta, fundo/cores distintos para não confundir com produção.
 */

import { isBetaEnvironment } from '@/lib/api-base';

export type LoginSistemaTipo = 'superadmin' | 'suporte';

export interface LoginSistemaDefaults {
  logo: string;
  login_background: string;
  cor_primaria: string;
  cor_secundaria: string;
  titulo: string;
  subtitulo: string;
}

const SUPERADMIN_PRODUCTION: LoginSistemaDefaults = {
  logo: '/login-logos/superadmin.svg',
  login_background: '/login-backgrounds/superadmin.jpg',
  cor_primaria: '#9333ea',
  cor_secundaria: '#7e22ce',
  titulo: 'Super Admin',
  subtitulo: 'Gestão global da plataforma LWK',
};

const SUPERADMIN_BETA: LoginSistemaDefaults = {
  logo: '/login-logos/superadmin.svg',
  login_background: '/login-backgrounds/superadmin-beta.jpg',
  cor_primaria: '#ea580c',
  cor_secundaria: '#c2410c',
  titulo: 'Super Admin — Beta',
  subtitulo: 'Homologação (beta.lwksistemas.com.br)',
};

const SUPORTE_PRODUCTION: LoginSistemaDefaults = {
  logo: '/login-logos/suporte.svg',
  login_background: '/login-backgrounds/suporte.jpg',
  cor_primaria: '#2563eb',
  cor_secundaria: '#1d4ed8',
  titulo: 'Portal de Suporte',
  subtitulo: 'Chamados, tickets e atendimento às lojas',
};

const SUPORTE_BETA: LoginSistemaDefaults = {
  logo: '/login-logos/suporte.svg',
  login_background: '/login-backgrounds/suporte-beta.jpg',
  cor_primaria: '#ea580c',
  cor_secundaria: '#c2410c',
  titulo: 'Portal de Suporte — Beta',
  subtitulo: 'Homologação (beta.lwksistemas.com.br)',
};

const PRODUCTION_DEFAULTS: Record<LoginSistemaTipo, LoginSistemaDefaults> = {
  superadmin: SUPERADMIN_PRODUCTION,
  suporte: SUPORTE_PRODUCTION,
};

const BETA_DEFAULTS: Record<LoginSistemaTipo, LoginSistemaDefaults> = {
  superadmin: SUPERADMIN_BETA,
  suporte: SUPORTE_BETA,
};

export function getLoginSistemaDefaults(tipo: LoginSistemaTipo): LoginSistemaDefaults {
  if (isBetaEnvironment()) {
    return BETA_DEFAULTS[tipo];
  }
  return PRODUCTION_DEFAULTS[tipo];
}

export function isSistemaBetaLogin(): boolean {
  return isBetaEnvironment();
}

/** @deprecated Use isSistemaBetaLogin */
export function isSuperadminBetaLogin(): boolean {
  return isBetaEnvironment();
}

/** Mescla resposta da API com padrões locais (logo/fundo vazios → padrão). */
export function resolveLoginSistemaConfig(
  tipo: LoginSistemaTipo,
  api?: Partial<LoginSistemaDefaults> | null,
): LoginSistemaDefaults {
  const base = getLoginSistemaDefaults(tipo);
  if (!api) return base;

  const productionBg = PRODUCTION_DEFAULTS[tipo].login_background;
  const betaBg = BETA_DEFAULTS[tipo].login_background;

  let login_background = (api.login_background ?? '').trim() || base.login_background;
  if (isBetaEnvironment() && login_background === productionBg) {
    login_background = betaBg;
  }

  return {
    logo: (api.logo ?? '').trim() || base.logo,
    login_background,
    cor_primaria: (api.cor_primaria ?? '').trim() || base.cor_primaria,
    cor_secundaria: (api.cor_secundaria ?? '').trim() || base.cor_secundaria,
    titulo: (api.titulo ?? '').trim() || base.titulo,
    subtitulo: (api.subtitulo ?? '').trim() || base.subtitulo,
  };
}
