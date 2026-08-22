'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { evolucaoPdfUrl, getProntuario, openPdf, receitaPdfUrl } from '@/lib/clinica-geral-api';
import type { Evolucao, Paciente, Prescricao } from '@/lib/clinica-geral-types';

export function ProntuarioPage() {
  const params = useParams();
  const id = Number(params.id);
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [evolucoes, setEvolucoes] = useState<Evolucao[]>([]);
  const [prescricoes, setPrescricoes] = useState<Prescricao[]>([]);

  useEffect(() => {
    if (!id) return;
    void getProntuario(id).then((d) => {
      setPaciente(d.paciente);
      setEvolucoes(d.evolucoes);
      setPrescricoes(d.prescricoes);
    });
  }, [id]);

  if (!paciente) return <p className="p-6 text-sm text-slate-500">Carregando prontuário...</p>;

  return (
    <div className="mx-auto max-w-3xl space-y-5 p-6">
      <h1 className="text-xl font-semibold text-slate-800">Prontuário · {paciente.nome}</h1>
      {paciente.alergias ? (
        <p className="rounded-md bg-red-50 px-4 py-2 text-sm font-medium text-red-700">Alergias: {paciente.alergias}</p>
      ) : null}
      <section>
        <h2 className="mb-2 font-semibold text-slate-800">Evoluções</h2>
        {evolucoes.length === 0 ? <p className="text-sm text-slate-500">Nenhuma evolução.</p> : null}
        {evolucoes.map((ev) => (
          <article key={ev.id} className="mb-3 rounded-xl border border-slate-200 bg-white p-4 text-sm">
            <p className="text-xs text-slate-400">{ev.especialidade} · consulta #{ev.consulta}</p>
            <p className="mt-1"><b>S</b> {ev.subjetivo || '—'}</p>
            <p><b>O</b> {ev.objetivo || '—'}</p>
            <p><b>A</b> {ev.avaliacao || '—'}</p>
            <p><b>P</b> {ev.plano || '—'}</p>
            <button type="button" className="mt-2 text-teal-700" onClick={() => void openPdf(evolucaoPdfUrl(ev.id))}>
              PDF
            </button>
          </article>
        ))}
      </section>
      <section>
        <h2 className="mb-2 font-semibold text-slate-800">Receitas</h2>
        {prescricoes.map((p) => (
          <button key={p.id} type="button" className="mb-2 block text-sm text-teal-700" onClick={() => void openPdf(receitaPdfUrl(p.id))}>
            Receita #{p.id} · {p.itens.map((i) => i.medicamento).join(', ')}
          </button>
        ))}
      </section>
    </div>
  );
}
