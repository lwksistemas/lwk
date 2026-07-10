'use client';

import {
  createContext,
  useContext,
  useMemo,
  type CSSProperties,
  type ReactNode,
} from 'react';
import {
  CLINICA_BELEZA_PRIMARY,
  CLINICA_BELEZA_PRIMARY_LIGHT,
} from '@/components/clinica-beleza/clinica-beleza-nav';
import {
  CLINICA_AGENDA_STATUS_COLORS,
  type AgendaStatusColorMap,
  mergeAgendaStatusColors,
} from '@/lib/clinica-beleza-constants';
import { lightenHex, normalizeHexColor } from '@/lib/clinica-beleza-theme-utils';

export type ClinicaBelezaTheme = {
  primary: string;
  primaryLight: string;
  secondary: string;
  sidebarBg: string;
  pageBg: string;
  agendaStatusColors: AgendaStatusColorMap;
  cssVars: CSSProperties;
};

const ClinicaBelezaThemeContext = createContext<ClinicaBelezaTheme | null>(null);

export function buildClinicaBelezaTheme(input?: {
  cor_primaria?: string | null;
  cor_secundaria?: string | null;
  cor_fundo_pagina?: string | null;
  agenda_status_colors?: Record<string, { bg?: string; border?: string }> | null;
}): ClinicaBelezaTheme {
  const primary =
    normalizeHexColor(input?.cor_primaria) || CLINICA_BELEZA_PRIMARY;
  const secondary =
    normalizeHexColor(input?.cor_secundaria) || primary;
  const primaryLight = lightenHex(primary, 0.88) || CLINICA_BELEZA_PRIMARY_LIGHT;
  const sidebarBg = lightenHex(primary, 0.92) || '#f0eaec';
  const pageBg =
    normalizeHexColor(input?.cor_fundo_pagina) ||
    lightenHex(primary, 0.96) ||
    '#f7f2f4';
  const agendaStatusColors = mergeAgendaStatusColors(input?.agenda_status_colors);

  return {
    primary,
    primaryLight,
    secondary,
    sidebarBg,
    pageBg,
    agendaStatusColors,
    cssVars: {
      ['--cb-primary' as string]: primary,
      ['--cb-primary-light' as string]: primaryLight,
      ['--cb-secondary' as string]: secondary,
      ['--cb-sidebar-bg' as string]: sidebarBg,
      ['--cb-page-bg' as string]: pageBg,
    },
  };
}

export function ClinicaBelezaThemeProvider({
  corPrimaria,
  corSecundaria,
  corFundoPagina,
  agendaStatusColors,
  children,
}: {
  corPrimaria?: string | null;
  corSecundaria?: string | null;
  corFundoPagina?: string | null;
  agendaStatusColors?: Record<string, { bg?: string; border?: string }> | null;
  children: ReactNode;
}) {
  const theme = useMemo(
    () =>
      buildClinicaBelezaTheme({
        cor_primaria: corPrimaria,
        cor_secundaria: corSecundaria,
        cor_fundo_pagina: corFundoPagina,
        agenda_status_colors: agendaStatusColors,
      }),
    [corPrimaria, corSecundaria, corFundoPagina, agendaStatusColors],
  );

  return (
    <ClinicaBelezaThemeContext.Provider value={theme}>
      <div className="contents" style={theme.cssVars}>
        {children}
      </div>
    </ClinicaBelezaThemeContext.Provider>
  );
}

export function useClinicaBelezaTheme(): ClinicaBelezaTheme {
  const ctx = useContext(ClinicaBelezaThemeContext);
  if (ctx) return ctx;
  return buildClinicaBelezaTheme();
}

export function useAgendaStatusColors(): AgendaStatusColorMap {
  return useClinicaBelezaTheme().agendaStatusColors;
}

/** Fallback estático (testes / fora do provider). */
export const DEFAULT_AGENDA_STATUS_COLORS = CLINICA_AGENDA_STATUS_COLORS;
