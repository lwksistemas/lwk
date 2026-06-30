'use client';

import Link from 'next/link';
import { AlertTriangle, X } from 'lucide-react';
import type { AssinaturaAviso } from '@/lib/assinatura-aviso';

type Props = {
  slug: string;
  aviso: AssinaturaAviso | null;
  visivel: boolean;
  onDismiss: () => void;
};

const NIVEL_STYLES: Record<AssinaturaAviso['nivel'], string> = {
  aviso: 'bg-amber-50 border-amber-300 text-amber-950 dark:bg-amber-950/40 dark:border-amber-700 dark:text-amber-100',
  urgente: 'bg-orange-50 border-orange-400 text-orange-950 dark:bg-orange-950/40 dark:border-orange-600 dark:text-orange-100',
  critico: 'bg-red-50 border-red-400 text-red-950 dark:bg-red-950/40 dark:border-red-700 dark:text-red-100',
};

export function LojaAssinaturaAvisoBanner({ slug, aviso, visivel, onDismiss }: Props) {
  if (!visivel || !aviso?.mensagem) return null;

  const assinaturaHref = `/loja/${slug}/assinatura`;

  return (
    <div
      role="alert"
      className={`sticky top-0 z-[100] border-b px-3 py-2.5 sm:px-4 ${NIVEL_STYLES[aviso.nivel]}`}
    >
      <div className="mx-auto flex max-w-7xl items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
        <div className="min-w-0 flex-1 text-sm leading-snug">
          <p className="font-medium">{aviso.mensagem}</p>
          <Link
            href={assinaturaHref}
            className="mt-1 inline-block font-semibold underline underline-offset-2 hover:opacity-80"
          >
            Ir para assinatura e pagar
          </Link>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded p-1 hover:bg-black/5 dark:hover:bg-white/10"
          aria-label="Fechar aviso de hoje"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
