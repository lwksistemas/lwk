'use client';

import type { Prescricao, PrescricaoItem } from '@/lib/clinica-geral-types';
import { TEAL } from '@/lib/clinica-geral-theme';
import { alertaAlergia } from '@/lib/clinica-geral-utils';

export const EMPTY_ITEM: PrescricaoItem = { medicamento: '', dosagem: '', posologia: '', quantidade: '' };

type ReceitaFormProps = {
  alergias: string;
  itens: PrescricaoItem[];
  prescricoes: Prescricao[];
  onItensChange: (itens: PrescricaoItem[]) => void;
  onEmitir: () => void;
  onAbrirPdf: (id: number) => void;
};

export function ReceitaForm({ alergias, itens, prescricoes, onItensChange, onEmitir, onAbrirPdf }: ReceitaFormProps) {
  const patchItem = (index: number, patch: Partial<PrescricaoItem>) => {
    onItensChange(itens.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  };

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="mb-3 font-semibold text-slate-800">Receituário ANVISA</h2>
      {itens.map((item, i) => {
        const alerta = alertaAlergia(alergias, item.medicamento);
        return (
          <div key={i} className="mb-2 grid gap-2 sm:grid-cols-4">
            <input
              placeholder="Medicamento"
              value={item.medicamento}
              onChange={(e) => patchItem(i, { medicamento: e.target.value })}
              className={`rounded-md border px-3 py-2 text-sm ${alerta ? 'border-red-500 bg-red-50' : 'border-slate-300'}`}
            />
            <input placeholder="Dosagem" value={item.dosagem} onChange={(e) => patchItem(i, { dosagem: e.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" />
            <input placeholder="Posologia" value={item.posologia} onChange={(e) => patchItem(i, { posologia: e.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" />
            <input placeholder="Qtde" value={item.quantidade} onChange={(e) => patchItem(i, { quantidade: e.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" />
            {alerta ? <p className="sm:col-span-4 text-xs text-red-600">Conflito com alergia cadastrada.</p> : null}
          </div>
        );
      })}
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => onItensChange([...itens, { ...EMPTY_ITEM }])} className="text-sm text-teal-700">
          + medicamento
        </button>
        <button type="button" onClick={onEmitir} className="rounded-md px-4 py-2 text-sm text-white" style={{ backgroundColor: TEAL }}>
          Emitir receita
        </button>
      </div>
      {prescricoes.map((p) => (
        <button key={p.id} type="button" onClick={() => onAbrirPdf(p.id)} className="mt-2 block text-sm text-teal-700">
          Abrir receita #{p.id}
          {p.itens.some((i) => i.alerta_alergia) ? ' (alerta de alergia)' : ''}
        </button>
      ))}
    </section>
  );
}
