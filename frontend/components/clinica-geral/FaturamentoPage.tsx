'use client';

import { useEffect, useState } from 'react';
import { fecharCaixa, getCaixaDia } from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { CaixaDia } from '@/lib/clinica-geral-types';
import { formatBRL, toISODate } from '@/lib/clinica-geral-utils';

export function FaturamentoPage() {
  const [data, setData] = useState(toISODate(new Date()));
  const [caixa, setCaixa] = useState<CaixaDia | null>(null);
  const [obs, setObs] = useState('');
  const [msg, setMsg] = useState('');

  useEffect(() => {
    void getCaixaDia(data).then(setCaixa);
  }, [data]);

  const particular = Number(caixa?.total_particular || 0);
  const convenio = Number(caixa?.total_convenio || 0);

  return (
    <div className="mx-auto max-w-xl space-y-5 p-6">
      <h1 className="text-xl font-semibold text-slate-800">Faturamento do dia</h1>
      <label className="text-sm text-slate-600">
        Data
        <input type="date" value={data} onChange={(e) => setData(e.target.value)} className="ml-2 rounded border border-slate-300 px-2 py-1" />
      </label>
      {caixa && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm">
          <p>Consultas: {caixa.consultas ?? 0}</p>
          <p>Particular: {formatBRL(particular)}</p>
          <p>Convênio: {formatBRL(convenio)}</p>
          <p className="mt-2 font-semibold">Total: {formatBRL(particular + convenio)}</p>
        </div>
      )}
      <textarea value={obs} onChange={(e) => setObs(e.target.value)} placeholder="Observações do fechamento" className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" rows={3} />
      <button
        type="button"
        onClick={async () => {
          await fecharCaixa(data, obs);
          setMsg('Caixa fechado.');
        }}
        className="rounded-md px-4 py-2 text-sm font-medium text-white"
        style={{ backgroundColor: TEAL }}
      >
        Fechar caixa
      </button>
      {msg ? <p className="text-sm text-teal-700">{msg}</p> : null}
    </div>
  );
}
