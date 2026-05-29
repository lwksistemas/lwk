'use client';

import Link from 'next/link';
import { MessageCircle } from 'lucide-react';
import { CLINICA_BELEZA_PRIMARY, CLINICA_BELEZA_PRIMARY_LIGHT } from './clinica-beleza-nav';

interface ClinicaBelezaSuporteButtonProps {
  slug: string;
  compact?: boolean;
}

export function ClinicaBelezaSuporteButton({ slug, compact = false }: ClinicaBelezaSuporteButtonProps) {
  if (compact) {
    return (
      <Link
        href={`/loja/${slug}/suporte`}
        className="inline-flex items-center justify-center w-10 h-10 rounded-full text-white shadow-sm transition-opacity hover:opacity-90"
        style={{ backgroundColor: '#25D366' }}
        title="Suporte — Precisa de ajuda?"
        aria-label="Abrir suporte"
      >
        <MessageCircle className="w-5 h-5" />
      </Link>
    );
  }

  return (
    <Link
      href={`/loja/${slug}/suporte`}
      className="inline-flex items-center gap-3 px-4 py-2 rounded-xl transition-opacity hover:opacity-95 shadow-sm"
      style={{ backgroundColor: CLINICA_BELEZA_PRIMARY_LIGHT }}
      title="Abrir suporte"
    >
      <div className="text-left leading-tight">
        <p className="text-[10px] font-bold uppercase tracking-wide" style={{ color: CLINICA_BELEZA_PRIMARY }}>
          Suporte
        </p>
        <p className="text-xs text-gray-600 dark:text-gray-400 hidden sm:block">Precisa de ajuda?</p>
      </div>
      <span
        className="inline-flex items-center justify-center w-10 h-10 rounded-full text-white shrink-0"
        style={{ backgroundColor: '#25D366' }}
      >
        <MessageCircle className="w-5 h-5" />
      </span>
    </Link>
  );
}
