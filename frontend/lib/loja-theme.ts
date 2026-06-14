import type { CSSProperties } from 'react';
import type { LojaInfo } from '@/types/dashboard';
import {
  homePathForTipo,
  isTipoCRMVendas,
  isTipoClinicaBeleza,
  isTipoClinicaEstetica,
} from '@/lib/loja-tipo';

export interface LojaThemeColors {
  corPrimaria: string;
  corSecundaria: string;
  pageBg: string;
  cardBorder: string;
  cssVars: CSSProperties;
}

const DEFAULT_PRIMARY = '#10B981';
const DEFAULT_SECONDARY = '#059669';

export function normalizeHex(color: string | undefined | null, fallback: string): string {
  const raw = (color || '').trim();
  if (!raw) return fallback;
  return raw.startsWith('#') ? raw : `#${raw}`;
}

export function hexToRgba(hex: string, alpha: number): string {
  const h = normalizeHex(hex, DEFAULT_PRIMARY).replace('#', '');
  const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
  if (full.length !== 6) return `rgba(16, 185, 129, ${alpha})`;
  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function isGenericGreen(primary: string, secondary: string): boolean {
  const p = normalizeHex(primary, '').toUpperCase();
  const s = normalizeHex(secondary, '').toUpperCase();
  return (!p || p === '#10B981') && (!s || s === '#059669');
}

function defaultColorsForTipo(tipoLojaNome: string): { primary: string; secondary: string } {
  if (isTipoCRMVendas(tipoLojaNome)) return { primary: '#3B82F6', secondary: '#2563EB' };
  if (isTipoClinicaBeleza(tipoLojaNome)) return { primary: '#EC4899', secondary: '#DB2777' };
  if (isTipoClinicaEstetica(tipoLojaNome)) return { primary: '#10B981', secondary: '#059669' };
  return { primary: DEFAULT_PRIMARY, secondary: DEFAULT_SECONDARY };
}

export function lojaThemeFromInfo(info: Partial<LojaInfo> | null | undefined): LojaThemeColors {
  const tipoNome = info?.tipo_loja_nome || '';
  const tipoDefaults = defaultColorsForTipo(tipoNome);
  let corPrimaria = normalizeHex(info?.cor_primaria, '');
  let corSecundaria = normalizeHex(info?.cor_secundaria, '');
  if (!corPrimaria || (isGenericGreen(corPrimaria, corSecundaria) && tipoNome)) {
    corPrimaria = tipoDefaults.primary;
  }
  if (!corSecundaria || (isGenericGreen(corPrimaria, corSecundaria) && tipoNome)) {
    corSecundaria = tipoDefaults.secondary;
  }
  return {
    corPrimaria,
    corSecundaria,
    pageBg: hexToRgba(corPrimaria, 0.06),
    cardBorder: hexToRgba(corPrimaria, 0.18),
    cssVars: {
      '--loja-primary': corPrimaria,
      '--loja-secondary': corSecundaria,
      '--loja-primary-soft': hexToRgba(corPrimaria, 0.1),
      '--loja-primary-muted': hexToRgba(corPrimaria, 0.06),
    } as CSSProperties,
  };
}

export { homePathForTipo };

export function assinaturaBackPath(slug: string, tipoLojaNome: string): string {
  return homePathForTipo(slug, tipoLojaNome);
}

export function themeLabelForTipo(tipoLojaNome: string): string {
  if (isTipoCRMVendas(tipoLojaNome)) return 'CRM Vendas';
  if (isTipoClinicaBeleza(tipoLojaNome)) return 'Clínica da Beleza';
  if (isTipoClinicaEstetica(tipoLojaNome)) return 'Clínica Estética';
  return 'Dashboard';
}
