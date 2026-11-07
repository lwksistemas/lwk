'use client';

import Link from 'next/link';
import { AlertTriangle } from 'lucide-react';
import type { AssinaturaAviso } from '@/lib/assinatura-aviso';

type Props = {
  slug: string;
  aviso: AssinaturaAviso | null;
  visivel: boolean;
};

const NIVEL_STYLES: Record<AssinaturaAviso['nivel'], string> = {
  aviso: 'bg-amber-50 border-amber-300 text-amber-950 dark:bg-amber-950/40 dark:border-amber-700 dark:text-amber-100',
  urgente: 'bg-orange-50 border-orange-400 text-orange-950 dark:bg-orange-950/40 dark:border-orange-600 dark:text-orange-100',
  critico: 'bg-red-50 border-red-400 text-red-950 dark:bg-red-950/40 dark:border-red-700 dark:text-red-100',
};

export function LojaAssinaturaAvisoBanner({ slug, aviso, visivel }: Props) {
  if (!visivel || !aviso?.mensagem) return null;

  const assinaturaHref = `/loja/${slug}/assinatura`;

  return (
    <div
      role="alert"
      className={`fixed top-0 left-0 right-0 z-[200] border-b px-3 py-2 sm:px-4 shadow-md ${NIVEL_STYLES[aviso.nivel]}`}
    >
      <div className="mx-auto flex max-w-7xl items-center gap-2">
        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
        <p className="min-w-0 flex-1 truncate text-sm font-medium" title={aviso.mensagem}>
          {aviso.mensagem}
        </p>
        <Link
          href={assinaturaHref}
          className="shrink-0 text-sm font-semibold underline underline-offset-2 hover:opacity-80"
        >
          Ir para assinatura e pagar
        </Link>
      </div>
    </div>
  );
}

/** Espaço para o banner fixo não cobrir o menu. */
export function LojaAssinaturaAvisoSpacer({ visivel }: { visivel: boolean }) {
  if (!visivel) return null;
  return <div className="h-10 shrink-0" aria-hidden />;
}
