'use client';

import { useEffect, useState } from 'react';
import { createLoteTiss, guiaPdfUrl, listGuiasTiss, listLotesTiss, openPdf } from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { GuiaTiss, LoteTiss } from '@/lib/clinica-geral-types';
import { formatBRL } from '@/lib/clinica-geral-utils';

export function TissPage() {
  const [lotes, setLotes] = useState<LoteTiss[]>([]);
  const [guias, setGuias] = useState<GuiaTiss[]>([]);
  const [loteId, setLoteId] = useState<number | null>(null);
  const [competencia, setCompetencia] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  });

  const carregar = async (lote?: number | null) => {
    setLotes(await listLotesTiss());
    setGuias(await listGuiasTiss(lote || undefined));
  };

  useEffect(() => {
    void carregar(loteId);
  }, [loteId]);

  return (
    <div className="mx-auto max-w-3xl space-y-5 p-6">
      <h1 className="text-xl font-semibold text-slate-800">Lotes TISS</h1>
      <div className="flex flex-wrap items-end gap-2">
        <label className="text-sm">
          Competência
          <input value={competencia} onChange={(e) => setCompetencia(e.target.value)} className="ml-2 rounded border border-slate-300 px-2 py-1" />
        </label>
        <button
          type="button"
          onClick={async () => {
            const lote = await createLoteTiss(competencia);
            setLoteId(lote.id);
            await carregar(lote.id);
          }}
          className="rounded-md px-3 py-2 text-sm text-white"
          style={{ backgroundColor: TEAL }}
        >
          Novo lote
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => setLoteId(null)} className="rounded border px-2 py-1 text-xs">
          Todas as guias
        </button>
        {lotes.map((l) => (
          <button
            key={l.id}
            type="button"
            onClick={() => setLoteId(l.id)}
            className={`rounded border px-2 py-1 text-xs ${loteId === l.id ? 'border-teal-600 text-teal-700' : ''}`}
          >
            {l.numero || l.id} · {l.competencia} ({l.guias_count ?? 0})
          </button>
        ))}
      </div>
      <table className="min-w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500">
            <th className="py-2">Guia</th>
            <th>Paciente</th>
            <th>Data</th>
            <th>Valor</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {guias.map((g) => (
            <tr key={g.id} className="border-t border-slate-100">
              <td className="py-2">{g.numero_guia}</td>
              <td>{g.paciente_nome}</td>
              <td>{g.consulta_data}</td>
              <td>{formatBRL(g.valor)}</td>
              <td>
                <button type="button" className="text-teal-700" onClick={() => void openPdf(guiaPdfUrl(g.id))}>
                  Imprimir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
