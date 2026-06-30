'use client';

import Link from 'next/link';
import { AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { AssinaturaAviso } from '@/lib/assinatura-aviso';

type Props = {
  slug: string;
  aviso: AssinaturaAviso | null | undefined;
  className?: string;
};

const NIVEL_CLASS: Record<AssinaturaAviso['nivel'], string> = {
  aviso: 'border-amber-400 bg-amber-50 text-amber-950 dark:bg-amber-950/30 dark:border-amber-700 dark:text-amber-100',
  urgente: 'border-orange-400 bg-orange-50 text-orange-950 dark:bg-orange-950/30 dark:border-orange-600 dark:text-orange-100',
  critico: 'border-red-400 bg-red-50 text-red-950 dark:bg-red-950/30 dark:border-red-700 dark:text-red-100',
};

export function AssinaturaAvisoAlert({ slug, aviso, className = '' }: Props) {
  if (!aviso?.mensagem) return null;

  return (
    <Alert className={`${NIVEL_CLASS[aviso.nivel]} ${className}`.trim()}>
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription className="text-sm leading-relaxed">
        <span className="font-medium">{aviso.mensagem}</span>
        <span className="mt-1 block">
          <Link href={`/loja/${slug}/assinatura`} className="font-semibold underline underline-offset-2">
            Ir para assinatura e pagar
          </Link>
        </span>
      </AlertDescription>
    </Alert>
  );
}
