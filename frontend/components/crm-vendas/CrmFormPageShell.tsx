'use client';

import type { ReactNode } from 'react';
import { Loader2, Save } from 'lucide-react';
import { CrmPagePanel, CRM_ACCENT } from '@/components/crm-vendas/CrmPagePanel';

interface CrmFormPageShellProps {
  children: ReactNode;
  error?: string | null;
  saving?: boolean;
  saveLabel?: string;
  savingLabel?: string;
  onSave: () => void;
  onCancel: () => void;
  saveDisabled?: boolean;
  accentColor?: string;
  /** Formulário ocupa 100% da área (sem margem cinza nem card centralizado). */
  fullPage?: boolean;
}

/** Layout full-page CRM: rodapé fixo (sem cabeçalho). */
export function CrmFormPageShell({
  children,
  error,
  saving = false,
  saveLabel = 'Salvar',
  savingLabel = 'Salvando...',
  onSave,
  onCancel,
  saveDisabled = false,
  accentColor = CRM_ACCENT,
  fullPage = false,
}: CrmFormPageShellProps) {
  return (
    <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-col min-h-[calc(100dvh-3.5rem)]">
      <div className="flex flex-col flex-1 min-h-0 w-full">
        <div
          className={
            fullPage
              ? 'flex-1 min-h-0 overflow-y-auto bg-white dark:bg-[#16325c]'
              : 'flex-1 min-h-0 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#f3f2f2] dark:bg-[#0d1f3c]'
          }
        >
          {error && (
            <div
              className={`p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm ${
                fullPage ? 'mx-4 md:mx-6 lg:mx-8 mt-4 mb-0' : 'mb-5'
              }`}
            >
              {error}
            </div>
          )}
          {fullPage ? (
            <div className="p-5 md:p-6 lg:p-8 min-h-full">{children}</div>
          ) : (
            <CrmPagePanel className="p-5 md:p-6 lg:p-8">{children}</CrmPagePanel>
          )}
        </div>

        <div
          className={`shrink-0 border-t border-gray-200 dark:border-[#0d1f3c] px-4 md:px-6 lg:px-8 py-4 ${
            fullPage ? 'bg-white dark:bg-[#16325c]' : 'bg-white/80 dark:bg-[#16325c]/80'
          }`}
        >
          <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 w-full">
            <button
              type="button"
              onClick={onCancel}
              className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-[#1e3a5f]"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={onSave}
              disabled={saving || saveDisabled}
              className="sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
              style={{ backgroundColor: accentColor }}
            >
              {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
              {saving ? savingLabel : saveLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
