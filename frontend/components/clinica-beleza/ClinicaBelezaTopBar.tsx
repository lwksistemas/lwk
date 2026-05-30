'use client';

import { CalendarDays, Menu } from 'lucide-react';
import type { LojaInfo } from '@/types/dashboard';
import { CLINICA_BELEZA_PRIMARY } from './clinica-beleza-nav';

function formatDatePicker(): string {
  return new Date().toLocaleDateString('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function DashboardTopBarRight({ loja }: { loja: LojaInfo }) {
  const displayName = loja?.nome?.split(' ')[0] || 'Usuária';
  return (
    <div className="flex items-center gap-2 sm:gap-3">
      <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-sm text-gray-600 dark:text-gray-300">
        <CalendarDays className="w-4 h-4 shrink-0" style={{ color: CLINICA_BELEZA_PRIMARY }} />
        <span className="capitalize whitespace-nowrap">{formatDatePicker()}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="text-right hidden md:block">
          <p className="text-sm font-semibold text-gray-800 dark:text-gray-100 leading-tight">Administrador(a)</p>
          <p className="text-xs text-gray-400 truncate max-w-[140px]">{loja?.nome}</p>
        </div>
        <div
          className="w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-white font-bold text-sm shrink-0"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        >
          {displayName.charAt(0).toUpperCase()}
        </div>
      </div>
    </div>
  );
}

interface ClinicaBelezaTopBarProps {
  loja: LojaInfo;
  isDashboard?: boolean;
  onOpenMobileMenu?: () => void;
}

export function ClinicaBelezaTopBar({
  loja,
  isDashboard = false,
  onOpenMobileMenu,
}: ClinicaBelezaTopBarProps) {
  return (
    <header className="sticky top-0 z-30 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shrink-0">
      <div className="flex items-center justify-between gap-2 min-h-[3.5rem] px-3 sm:px-6 lg:px-8">
        <div className="flex items-center min-w-0">
          <button
            type="button"
            onClick={onOpenMobileMenu}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Abrir menu"
          >
            <Menu className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
        </div>

        <div className="flex items-center justify-end min-w-0">
          {isDashboard ? (
            <DashboardTopBarRight loja={loja} />
          ) : (
            <span className="lg:hidden text-xs font-medium text-gray-500 truncate max-w-[100px]">
              {loja?.nome}
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
