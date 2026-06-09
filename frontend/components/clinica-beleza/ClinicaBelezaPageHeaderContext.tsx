'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, LogOut, Plus, type LucideIcon } from 'lucide-react';
import type { LojaInfo } from '@/types/dashboard';
import { CLINICA_BELEZA_PRIMARY } from './clinica-beleza-nav';
import { OfflineIndicator } from './OfflineIndicator';

type PortalTarget = HTMLElement | null;

export interface ClinicaBelezaShellActions {
  loja: LojaInfo;
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
  onLogout?: () => void;
}

interface ClinicaBelezaPageHeaderContextValue {
  setMainTarget: (el: PortalTarget) => void;
  setSecondaryTarget: (el: PortalTarget) => void;
  shellActions: ClinicaBelezaShellActions | null;
}

const ClinicaBelezaPageHeaderContext = createContext<ClinicaBelezaPageHeaderContextValue | null>(
  null,
);

export function useClinicaBelezaShellActions() {
  return useContext(ClinicaBelezaPageHeaderContext)?.shellActions ?? null;
}

export function ClinicaBelezaPageHeaderProvider({
  children,
  shellActions = null,
}: {
  children: ReactNode;
  shellActions?: ClinicaBelezaShellActions | null;
}) {
  const [mainTarget, setMainTargetState] = useState<PortalTarget>(null);
  const [secondaryTarget, setSecondaryTargetState] = useState<PortalTarget>(null);

  const setMainTarget = useCallback((el: PortalTarget) => {
    setMainTargetState(el);
  }, []);

  const setSecondaryTarget = useCallback((el: PortalTarget) => {
    setSecondaryTargetState(el);
  }, []);

  return (
    <ClinicaBelezaPageHeaderContext.Provider value={{ setMainTarget, setSecondaryTarget, shellActions }}>
      <ClinicaBelezaPageHeaderPortalContext.Provider value={mainTarget}>
        <ClinicaBelezaPageHeaderFooterPortalContext.Provider value={secondaryTarget}>
          {children}
        </ClinicaBelezaPageHeaderFooterPortalContext.Provider>
      </ClinicaBelezaPageHeaderPortalContext.Provider>
    </ClinicaBelezaPageHeaderContext.Provider>
  );
}

export function useClinicaBelezaPageHeaderMount() {
  const ctx = useContext(ClinicaBelezaPageHeaderContext);
  if (!ctx) {
    throw new Error('useClinicaBelezaPageHeaderMount must be used within ClinicaBelezaPageHeaderProvider');
  }
  return ctx;
}

const ClinicaBelezaPageHeaderPortalContext = createContext<PortalTarget>(null);
const ClinicaBelezaPageHeaderFooterPortalContext = createContext<PortalTarget>(null);

/** Renderiza controles da página na faixa branca superior. */
export function ClinicaBelezaPageHeader({ children }: { children: ReactNode }) {
  const target = useContext(ClinicaBelezaPageHeaderPortalContext);
  if (!target) return null;
  return createPortal(children, target);
}

/** Segunda linha opcional na faixa branca (ex.: legenda da agenda). */
export function ClinicaBelezaPageHeaderFooter({ children }: { children: ReactNode }) {
  const target = useContext(ClinicaBelezaPageHeaderFooterPortalContext);
  if (!target) return null;
  return createPortal(children, target);
}

export interface ClinicaBelezaStandardPageHeaderProps {
  title: string;
  subtitle?: string;
  backHref?: string;
  /** Se definido, substitui a navegação padrão do botão voltar (ex.: limpar query params). */
  onBack?: () => void;
  icon?: LucideIcon;
  newLabel?: string;
  onNew?: () => void;
  showOffline?: boolean;
  /** Ações à esquerda do indicador Online (ex.: toolbar da aba ativa). */
  toolbarActions?: ReactNode;
  extraActions?: ReactNode;
  /** Oculta voltar, ícone e título — só exibe Online, Sair e ações extras (ex.: dashboard). */
  actionsOnly?: boolean;
  showBack?: boolean;
}

/** Cabeçalho padrão: voltar, título, offline e botão de ação. */
export function ClinicaBelezaStandardPageHeader({
  title,
  subtitle,
  backHref,
  onBack,
  icon: Icon,
  newLabel = 'Novo',
  onNew,
  showOffline = true,
  toolbarActions,
  extraActions,
  actionsOnly = false,
  showBack = true,
}: ClinicaBelezaStandardPageHeaderProps) {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;
  const shellActions = useClinicaBelezaShellActions();

  const handleBack = () => {
    if (onBack) {
      onBack();
      return;
    }
    router.push(backHref || `/loja/${slug}/dashboard`);
  };

  const actions = (
    <>
      {toolbarActions}
      {showOffline && <OfflineIndicator />}
      {shellActions?.onLogout && (
        <button
          type="button"
          onClick={shellActions.onLogout}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-sm font-medium text-red-600 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          title="Sair"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          <span className="hidden sm:inline">Sair</span>
        </button>
      )}
      {extraActions}
      {onNew && (
        <button
          type="button"
          onClick={onNew}
          className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-white rounded-lg hover:opacity-90 text-xs sm:text-sm font-medium"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        >
          <Plus className="w-4 h-4 shrink-0" />
          <span className="hidden sm:inline">{newLabel}</span>
          <span className="sm:hidden">Novo</span>
        </button>
      )}
    </>
  );

  if (actionsOnly) {
    return (
      <ClinicaBelezaPageHeader>
        <div className="flex items-center gap-1.5 sm:gap-2 w-full min-w-0 flex-wrap justify-end">
          {actions}
        </div>
      </ClinicaBelezaPageHeader>
    );
  }

  return (
    <ClinicaBelezaPageHeader>
      <div className="flex flex-wrap items-center gap-2 sm:gap-3 w-full min-w-0">
        {showBack && (
          <button
            type="button"
            onClick={handleBack}
            className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 shrink-0"
            aria-label="Voltar"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
        )}
        {Icon && (
          <div
            className="hidden sm:flex w-9 h-9 rounded-lg items-center justify-center shrink-0"
            style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}18` }}
          >
            <Icon className="w-4 h-4" style={{ color: CLINICA_BELEZA_PRIMARY }} />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <h1 className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate leading-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate hidden sm:block leading-snug">
              {subtitle}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1.5 sm:gap-2 ml-auto shrink-0 flex-wrap justify-end">
          {actions}
        </div>
      </div>
    </ClinicaBelezaPageHeader>
  );
}

/** Limpa o cabeçalho ao desmontar (útil em páginas sem header explícito). */
export function ClinicaBelezaClearPageHeader() {
  const main = useContext(ClinicaBelezaPageHeaderPortalContext);
  const secondary = useContext(ClinicaBelezaPageHeaderFooterPortalContext);

  useEffect(() => {
    return () => {
      if (main) main.innerHTML = '';
      if (secondary) secondary.innerHTML = '';
    };
  }, [main, secondary]);

  return null;
}
