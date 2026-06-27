"use client";

import { X } from "lucide-react";
import type { ReactNode } from "react";

interface ClinicaBelezaPortraitModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  closeDisabled?: boolean;
}

/** Modal estreito (retrato) — padrão da Clínica da Beleza para configurações. */
export function ClinicaBelezaPortraitModal({
  open,
  onClose,
  title,
  subtitle,
  icon,
  children,
  footer,
  closeDisabled = false,
}: ClinicaBelezaPortraitModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl w-full max-w-[22rem] max-h-[min(90vh,640px)] flex flex-col overflow-hidden">
        <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div className="min-w-0 flex items-start gap-2">
            {icon}
            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 leading-tight">{title}</h2>
              {subtitle ? (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-snug">{subtitle}</p>
              ) : null}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={closeDisabled}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500 shrink-0 disabled:opacity-40"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain px-4 py-4">{children}</div>

        {footer ? (
          <div className="px-4 py-3 border-t border-gray-200 dark:border-neutral-700 shrink-0">{footer}</div>
        ) : null}
      </div>
    </div>
  );
}
