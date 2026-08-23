'use client';

import { X } from 'lucide-react';
import { mergeFicha, resumoAbaFicha, type AbaAtendimento } from '@/lib/clinica-geral-atendimento';
import { NAVY, TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta, Evolucao } from '@/lib/clinica-geral-types';
import { formatDateBR, formatHora } from '@/lib/clinica-geral-utils';

type Props = {
  aba: AbaAtendimento;
  titulo: string;
  consultaId: number;
  evolucoes: Evolucao[];
  consultas: Consulta[];
  onClose: () => void;
};

export function AtendimentoAnteriores({ aba, titulo, consultaId, evolucoes, consultas, onClose }: Props) {
  const itens = evolucoes
    .filter((e) => e.consulta !== consultaId)
    .map((e) => {
      const consulta = consultas.find((c) => c.id === e.consulta);
      const linhas = resumoAbaFicha(aba, mergeFicha(e.ficha));
      return {
        id: e.id,
        data: consulta?.data || e.updated_at?.slice(0, 10) || '',
        hora: consulta?.hora || '',
        linhas,
      };
    })
    .filter((i) => i.linhas.length)
    .sort((a, b) => `${b.data}${b.hora}`.localeCompare(`${a.data}${a.hora}`));

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="max-h-[85vh] w-full max-w-lg overflow-auto rounded-xl bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium" style={{ color: TEAL }}>
              Ver anteriores
            </p>
            <h3 className="text-base font-semibold text-slate-800">{titulo}</h3>
          </div>
          <button type="button" onClick={onClose} aria-label="Fechar" className="text-slate-400 hover:text-slate-600">
            <X className="h-4 w-4" />
          </button>
        </div>
        {itens.length === 0 ? (
          <p className="text-sm text-slate-400">Não há registros anteriores nesta seção.</p>
        ) : (
          <ul className="space-y-3">
            {itens.map((item) => (
              <li key={item.id} className="rounded-md border border-slate-200 p-3">
                <p className="mb-2 text-xs font-medium" style={{ color: NAVY }}>
                  {item.data ? formatDateBR(item.data) : 'Sem data'}
                  {item.hora ? ` · ${formatHora(item.hora)}` : ''}
                </p>
                <ul className="space-y-1 text-sm text-slate-700">
                  {item.linhas.map((linha) => (
                    <li key={linha}>{linha}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
