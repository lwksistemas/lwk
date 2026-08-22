'use client';

import type { Evolucao } from '@/lib/clinica-geral-types';
import { TEAL } from '@/lib/clinica-geral-theme';

const CAMPOS = ['subjetivo', 'objetivo', 'avaliacao', 'plano'] as const;

type EvolucaoFormProps = {
  evolucao: Partial<Evolucao>;
  onChange: (patch: Partial<Evolucao>) => void;
  onSave: () => void;
  onPdf?: () => void;
};

export function EvolucaoForm({ evolucao, onChange, onSave, onPdf }: EvolucaoFormProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="mb-3 font-semibold text-slate-800">Evolução SOAP</h2>
      {CAMPOS.map((campo) => (
        <label key={campo} className="mb-3 block text-sm">
          <span className="mb-1 block capitalize text-slate-600">{campo}</span>
          <textarea
            value={evolucao[campo] || ''}
            onChange={(e) => onChange({ [campo]: e.target.value })}
            rows={3}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
      ))}
      <div className="flex gap-2">
        <button type="button" onClick={onSave} className="rounded-md px-4 py-2 text-sm text-white" style={{ backgroundColor: TEAL }}>
          Salvar evolução
        </button>
        {evolucao.id && onPdf ? (
          <button type="button" onClick={onPdf} className="rounded-md border px-4 py-2 text-sm">
            PDF do prontuário
          </button>
        ) : null}
      </div>
    </section>
  );
}
