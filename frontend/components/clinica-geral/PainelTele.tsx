'use client';

import type { Consulta } from '@/lib/clinica-geral-types';
import { TEAL } from '@/lib/clinica-geral-theme';

type PainelTeleProps = {
  consulta: Consulta;
  info: string;
  onAbrir: () => void;
  onRegistrar: () => void;
};

export function PainelTele({ consulta, info, onAbrir, onRegistrar }: PainelTeleProps) {
  if (consulta.modalidade !== 'tele') return null;
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="mb-3 font-semibold text-slate-800">Telemedicina (cota 10h/mês)</h2>
      {info ? <p className="mb-2 text-sm text-slate-600">{info}</p> : null}
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={onAbrir} className="rounded-md px-4 py-2 text-sm text-white" style={{ backgroundColor: TEAL }}>
          Abrir sala
        </button>
        <button type="button" onClick={onRegistrar} className="rounded-md border px-4 py-2 text-sm">
          Registrar duração
        </button>
      </div>
    </section>
  );
}
