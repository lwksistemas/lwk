'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
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

export type ClinicaBelezaThemeColorsInput = {
  corPrimaria?: string | null;
  corSecundaria?: string | null;
  /** String vazia = automático (tom claro da primária). */
  corFundoPagina?: string | null;
  agendaStatusColors?: Record<string, { bg?: string; border?: string }> | null;
};

type ClinicaBelezaThemeActions = {
  /** Atualiza cores do menu/fundo/agenda na hora (preview ou após salvar). */
  applyColors: (colors: ClinicaBelezaThemeColorsInput) => void;
};

const ClinicaBelezaThemeContext = createContext<ClinicaBelezaTheme | null>(null);
const ClinicaBelezaThemeActionsContext = createContext<ClinicaBelezaThemeActions | null>(null);

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

type LocalColors = {
  corPrimaria: string | null | undefined;
  corSecundaria: string | null | undefined;
  corFundoPagina: string | null | undefined;
  agendaStatusColors: Record<string, { bg?: string; border?: string }> | null | undefined;
};

function propsToLocal(input: {
  corPrimaria?: string | null;
  corSecundaria?: string | null;
  corFundoPagina?: string | null;
  agendaStatusColors?: Record<string, { bg?: string; border?: string }> | null;
}): LocalColors {
  return {
    corPrimaria: input.corPrimaria,
    corSecundaria: input.corSecundaria,
    corFundoPagina: input.corFundoPagina,
    agendaStatusColors: input.agendaStatusColors,
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
  const [local, setLocal] = useState<LocalColors>(() =>
    propsToLocal({ corPrimaria, corSecundaria, corFundoPagina, agendaStatusColors }),
  );

  const propsKey = `${corPrimaria ?? ''}|${corSecundaria ?? ''}|${corFundoPagina ?? ''}|${JSON.stringify(agendaStatusColors ?? null)}`;
  const prevPropsKey = useRef(propsKey);

  useEffect(() => {
    if (propsKey === prevPropsKey.current) return;
    prevPropsKey.current = propsKey;
    setLocal(propsToLocal({ corPrimaria, corSecundaria, corFundoPagina, agendaStatusColors }));
  }, [propsKey, corPrimaria, corSecundaria, corFundoPagina, agendaStatusColors]);

  const applyColors = useCallback((colors: ClinicaBelezaThemeColorsInput) => {
    setLocal((prev) => ({
      corPrimaria:
        colors.corPrimaria !== undefined ? colors.corPrimaria : prev.corPrimaria,
      corSecundaria:
        colors.corSecundaria !== undefined ? colors.corSecundaria : prev.corSecundaria,
      corFundoPagina:
        colors.corFundoPagina !== undefined ? colors.corFundoPagina : prev.corFundoPagina,
      agendaStatusColors:
        colors.agendaStatusColors !== undefined
          ? colors.agendaStatusColors
          : prev.agendaStatusColors,
    }));
  }, []);

  const theme = useMemo(
    () =>
      buildClinicaBelezaTheme({
        cor_primaria: local.corPrimaria,
        cor_secundaria: local.corSecundaria,
        cor_fundo_pagina: local.corFundoPagina,
        agenda_status_colors: local.agendaStatusColors,
      }),
    [local],
  );

  const actions = useMemo(() => ({ applyColors }), [applyColors]);

  return (
    <ClinicaBelezaThemeActionsContext.Provider value={actions}>
      <ClinicaBelezaThemeContext.Provider value={theme}>
        <div className="contents" style={theme.cssVars}>
          {children}
        </div>
      </ClinicaBelezaThemeContext.Provider>
    </ClinicaBelezaThemeActionsContext.Provider>
  );
}

export function useClinicaBelezaTheme(): ClinicaBelezaTheme {
  const ctx = useContext(ClinicaBelezaThemeContext);
  if (ctx) return ctx;
  return buildClinicaBelezaTheme();
}

export function useClinicaBelezaThemeActions(): ClinicaBelezaThemeActions {
  const ctx = useContext(ClinicaBelezaThemeActionsContext);
  if (ctx) return ctx;
  return {
    applyColors: () => {
      /* fora do provider (ex.: testes) — no-op */
    },
  };
}

export function useAgendaStatusColors(): AgendaStatusColorMap {
  return useClinicaBelezaTheme().agendaStatusColors;
}

/** Fallback estático (testes / fora do provider). */
export const DEFAULT_AGENDA_STATUS_COLORS = CLINICA_AGENDA_STATUS_COLORS;
