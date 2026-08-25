import { NAVY } from '@/lib/clinica-geral-theme';
import { isTipoClinicaGeral } from '@/lib/loja-tipo';

/** Fora de /api — no beta/prod o nginx manda /api para o Django. */
export const LOJA_MANIFEST_PATH = '/pwa/manifest/loja';

export const PWA_SW_PATH = '/pwa-sw.js';

const ESTETICA_GREEN = '#10B981';

export type PwaContextType = 'loja' | 'superadmin' | 'suporte';

export type PwaContext = {
  allow: boolean;
  type: PwaContextType | null;
};

export function lojaManifestUrl(slug: string): string {
  return `${LOJA_MANIFEST_PATH}?slug=${encodeURIComponent(slug.trim())}`;
}

export function pwaIcons(kind: 'lwk' | 'clinica' = 'lwk') {
  const base = kind === 'clinica' ? '/icons/clinica' : '/icons/icon';
  return [
    { src: `${base}-192.png`, sizes: '192x192', type: 'image/png', purpose: 'any' },
    { src: `${base}-512.png`, sizes: '512x512', type: 'image/png', purpose: 'any' },
    { src: `${base}-192.png`, sizes: '192x192', type: 'image/png', purpose: 'maskable' },
    { src: `${base}-512.png`, sizes: '512x512', type: 'image/png', purpose: 'maskable' },
  ];
}

export function getPWAContext(pathname: string | null): PwaContext {
  if (!pathname) return { allow: false, type: null };
  if (pathname === '/superadmin/login') return { allow: true, type: 'superadmin' };
  if (pathname === '/suporte/login') return { allow: true, type: 'suporte' };

  const parts = pathname.split('/').filter(Boolean);
  if (parts[0] === 'loja' && parts.length >= 2) {
    const seg = parts[1];
    if (seg === 'dashboard' || seg === 'trocar-senha') return { allow: false, type: null };
    return { allow: true, type: 'loja' };
  }

  return { allow: false, type: null };
}

export function isInstallPWALojaPath(pathname: string | null): boolean {
  return getPWAContext(pathname).allow;
}

export type LojaManifestInput = {
  nome?: string;
  tipo_loja_nome?: string;
  cor_primaria?: string;
};

export function themeColorForLojaManifest(loja: LojaManifestInput): string {
  const tipo = loja.tipo_loja_nome || '';
  const cor = (loja.cor_primaria || '').trim();
  if (isTipoClinicaGeral(tipo)) {
    if (!cor || cor.toUpperCase() === ESTETICA_GREEN.toUpperCase()) return NAVY;
    return cor;
  }
  return cor || '#ec4899';
}

export function buildLojaManifest(slug: string, loja: LojaManifestInput) {
  const nome = loja.nome?.trim() || 'Loja';
  const shortName = nome.length > 20 ? `${nome.slice(0, 17)}…` : nome;
  const slugTrim = slug.trim();
  const clinica = isTipoClinicaGeral(loja.tipo_loja_nome || '');
  const tipoLabel = clinica ? 'Clínica' : loja.tipo_loja_nome || 'da loja';

  return {
    id: `/loja/${slugTrim}/`,
    name: nome,
    short_name: shortName,
    description: `Gestão ${tipoLabel} - ${nome}`,
    start_url: `/loja/${slugTrim}/login`,
    display: 'standalone' as const,
    lang: 'pt-BR',
    background_color: '#ffffff',
    theme_color: themeColorForLojaManifest(loja),
    orientation: 'portrait-primary' as const,
    scope: `/loja/${slugTrim}/`,
    icons: pwaIcons(clinica ? 'clinica' : 'lwk'),
  };
}
