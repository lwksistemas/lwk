'use client';

import { useMemo } from 'react';
import { Info } from 'lucide-react';
import { SecaoTeal } from '@/components/clinica-geral/AtendimentoWidgets';
import { ESCALAS_MEDICAS, lerEscalasOcultas } from '@/lib/clinica-geral-atendimento';
import { TEAL } from '@/lib/clinica-geral-theme';

type Props = {
  versao?: number;
  onVerAnteriores?: () => void;
  onConfigurar?: () => void;
};

export function AtendimentoEscalas({ versao = 0, onVerAnteriores, onConfigurar }: Props) {
  const visiveis = useMemo(() => {
    const ocultas = new Set(lerEscalasOcultas());
    return ESCALAS_MEDICAS.filter((nome) => !ocultas.has(nome));
  }, [versao]);

  return (
    <SecaoTeal titulo="Escalas médicas" onVerAnteriores={onVerAnteriores} onConfigurar={onConfigurar}>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {visiveis.map((nome) => (
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
