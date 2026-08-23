'use client';

import { Info } from 'lucide-react';
import { SecaoTeal } from '@/components/clinica-geral/AtendimentoWidgets';
import { ESCALAS_MEDICAS } from '@/lib/clinica-geral-atendimento';
import { TEAL } from '@/lib/clinica-geral-theme';

export function AtendimentoEscalas() {
  return (
    <SecaoTeal titulo="Escalas médicas">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ESCALAS_MEDICAS.map((nome) => (
          <button
            key={nome}
            type="button"
            className="flex items-start justify-between rounded-md border border-slate-200 bg-white px-3 py-4 text-left text-sm font-medium hover:border-teal-400"
            style={{ color: TEAL }}
          >
            {nome}
            <Info className="h-3.5 w-3.5 text-slate-300" />
          </button>
        ))}
      </div>
    </SecaoTeal>
  );
}
