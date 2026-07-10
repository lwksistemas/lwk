import type { ReactNode } from 'react';

/** Área principal em tela cheia — padrão Consultas / Clientes */
export function ClinicaBelezaPageContent({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`min-h-full bg-[var(--cb-page-bg,#f7f2f4)] dark:bg-gray-950 p-4 md:p-6 lg:p-8 w-full ${className}`}
    >
      {children}
    </div>
  );
}

/** Painel branco em largura total */
export function ClinicaBelezaPanel({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm w-full overflow-hidden ${className}`}
    >
      {children}
    </div>
  );
}
