'use client';

import { useCallback } from 'react';
import { Menu, Moon, Sun } from 'lucide-react';
import type { LojaInfo } from '@/types/dashboard';
import { useClinicaBelezaPageHeaderMount, useClinicaBelezaShellActions } from './ClinicaBelezaPageHeaderContext';

function ClinicaBelezaUserTopBarActions({ loja }: { loja: LojaInfo }) {
  const shellActions = useClinicaBelezaShellActions();
  const darkMode = shellActions?.darkMode ?? false;
  const setDarkMode = shellActions?.setDarkMode;

  return (
    <div className="flex items-center gap-2 sm:gap-3 shrink-0">
      <div className="text-right hidden md:block">
        <p className="text-sm font-semibold text-gray-800 dark:text-gray-100 leading-tight">Administrador(a)</p>
        <p className="text-xs text-gray-400 truncate max-w-[140px]">{loja?.nome}</p>
      </div>
      <button
        type="button"
        onClick={() => setDarkMode?.(!darkMode)}
        className="w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 shrink-0 transition-colors"
        title={darkMode ? 'Modo claro' : 'Modo escuro'}
        aria-label={darkMode ? 'Ativar modo claro' : 'Ativar modo escuro'}
      >
        {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </button>
    </div>
  );
}

interface ClinicaBelezaTopBarProps {
  loja: LojaInfo;
  onOpenMobileMenu?: () => void;
}

export function ClinicaBelezaTopBar({ loja, onOpenMobileMenu }: ClinicaBelezaTopBarProps) {
  const { setMainTarget, setSecondaryTarget } = useClinicaBelezaPageHeaderMount();

  const mainRef = useCallback(
    (node: HTMLDivElement | null) => {
      setMainTarget(node);
    },
    [setMainTarget],
  );

  const secondaryRef = useCallback(
    (node: HTMLDivElement | null) => {
      setSecondaryTarget(node);
    },
    [setSecondaryTarget],
  );

  return (
    <header className="sticky top-0 z-30 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shrink-0">
      <div className="flex items-center gap-2 sm:gap-3 min-h-[3.5rem] px-3 sm:px-6 lg:px-8">
        <div className="flex items-center shrink-0 lg:hidden">
          <button
            type="button"
            onClick={onOpenMobileMenu}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Abrir menu"
          >
            <Menu className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
        </div>

        <div ref={mainRef} className="flex-1 min-w-0 flex items-center" />

        <ClinicaBelezaUserTopBarActions loja={loja} />
      </div>

      <div
        ref={secondaryRef}
        className="empty:hidden px-3 sm:px-6 lg:px-8 py-2 border-t border-gray-100 dark:border-gray-700/80"
      />
    </header>
  );
}
