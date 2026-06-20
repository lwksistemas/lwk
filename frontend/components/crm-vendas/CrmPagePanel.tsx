import type { ReactNode } from 'react';

/** Painel branco em largura total — padrão CRM (equivalente ao ClinicaBelezaPanel). */
export function CrmPagePanel({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl bg-white dark:bg-[#16325c] border border-gray-200 dark:border-[#0d1f3c] shadow-sm w-full overflow-hidden ${className}`}
    >
      {children}
    </div>
  );
}

export const CRM_ACCENT = '#0176d3';
