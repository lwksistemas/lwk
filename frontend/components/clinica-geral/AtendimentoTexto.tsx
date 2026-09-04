'use client';

import { SecaoTeal } from '@/components/clinica-geral/AtendimentoWidgets';

type Props = {
  titulo: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  onVerAnteriores?: () => void;
  onConfigurar?: () => void;
};

export function AtendimentoTexto({ titulo, value, onChange, rows = 10, onVerAnteriores, onConfigurar }: Props) {
  return (
    <SecaoTeal titulo={titulo} onVerAnteriores={onVerAnteriores} onConfigurar={onConfigurar}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500"
      />
    </SecaoTeal>
  );
}
