'use client';

import { useMemo, useState } from 'react';
import { AlertTriangle, Calendar, FileText, Printer, Stethoscope, ZoomIn, ZoomOut } from 'lucide-react';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta, Evolucao, FichaAtendimento } from '@/lib/clinica-geral-types';
import { mergeFicha } from '@/lib/clinica-geral-atendimento';
import { formatDataExtenso, formatDateBR, toISODate } from '@/lib/clinica-geral-utils';

const MESES = ['Jan.', 'Fev.', 'Mar.', 'Abr.', 'Mai.', 'Jun.', 'Jul.', 'Ago.', 'Set.', 'Out.', 'Nov.', 'Dez.'];

type Props = {
  consultas: Consulta[];
  evolucoes: Evolucao[];
  medicoNome: string;
  onReabrir: (consulta: Consulta) => void;
  onImprimir: (evolucao?: Evolucao) => void;
};

export function ProntuarioResumoAtendimento({ consultas, evolucoes, medicoNome, onReabrir, onImprimir }: Props) {
  const ordenadas = useMemo(
    () =>
      [...consultas]
        .filter((c) => c.status !== 'desmarcado')
        .sort((a, b) => `${b.data}${b.hora}`.localeCompare(`${a.data}${a.hora}`)),
    [consultas],
  );
  const [selecionadaId, setSelecionadaId] = useState(ordenadas[0]?.id || 0);
  const consulta = ordenadas.find((c) => c.id === selecionadaId) || ordenadas[0];
  const evolucao = consulta ? evolucoes.find((e) => e.consulta === consulta.id) : undefined;
  const ficha = mergeFicha(evolucao?.ficha);
  const aberto = Boolean(consulta && consulta.status !== 'atendido' && consulta.status !== 'faltou');

  if (!consulta) {
    return <p className="pt-16 text-center text-slate-400">Este paciente não possui atendimentos</p>;
  }

  return (
    <div className="space-y-5">
      <LinhaDoTempo consultas={ordenadas} selecionada={consulta} onSelect={setSelecionadaId} />

      <section className="rounded-lg border border-slate-200 bg-white">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-4 py-3">
          <h2 className="text-base font-semibold text-slate-800">Resumo do atendimento</h2>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onReabrir(consulta)}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-white"
              style={{ backgroundColor: TEAL }}
            >
              Reabrir atendimento
            </button>
            <button type="button" className="rounded-md border border-slate-200 p-1.5 text-slate-500" title="Imprimir" onClick={() => onImprimir(evolucao)}>
              <Printer className="h-4 w-4" />
            </button>
          </div>
        </div>

        {aberto ? (
          <p className="flex items-center gap-2 bg-amber-50 px-4 py-2 text-sm text-amber-800">
            <AlertTriangle className="h-4 w-4" />
            Atendimento aberto
          </p>
        ) : null}

        <div className="space-y-2 px-4 py-3 text-sm text-slate-600">
          <p className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400" />
            {formatDataExtenso(consulta.data)}
          </p>
          <p className="flex items-center gap-2">
            <Stethoscope className="h-4 w-4 text-slate-400" />
            Atendimento: {medicoNome || consulta.agendado_por || 'Médico do consultório'}
          </p>
          <p className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-slate-400" />
            Prontuário utilizado: Clínica
          </p>
        </div>

        <div className="grid gap-3 px-4 pb-4 md:grid-cols-2">
          <Cartao titulo="História e motivo do atendimento" linhas={linhasHma(ficha)} />
          <Cartao titulo="Antecedentes pessoais" linhas={linhasAntecedentes(ficha)} />
        </div>
      </section>
    </div>
  );
}

function linhasHma(ficha: FichaAtendimento): string[] {
  const queixas = ficha.queixas.map((q) => [q.nome, q.duracao].filter(Boolean).join(' — '));
  return [...queixas, ficha.historia_doenca].filter(Boolean);
}

function linhasAntecedentes(ficha: FichaAtendimento): string[] {
  return [
    ...ficha.antecedentes_clinicos.map((i) => `${i.nome}${i.status ? ` (${i.status})` : ''}`),
    ...ficha.antecedentes_cirurgicos.map((i) => `${i.nome}${i.status ? ` (${i.status})` : ''}`),
  ];
}

function Cartao({ titulo, linhas }: { titulo: string; linhas: string[] }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50/60 p-3">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">{titulo}</h3>
      {linhas.length === 0 ? (
        <p className="text-sm text-slate-400">Ainda não há informações</p>
      ) : (
        <ul className="space-y-1 text-sm text-slate-700">
          {linhas.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function LinhaDoTempo({
  consultas,
  selecionada,
  onSelect,
}: {
  consultas: Consulta[];
  selecionada: Consulta;
  onSelect: (id: number) => void;
}) {
  const hoje = toISODate(new Date());
  const centro = parseInt(hoje.slice(5, 7), 10) - 1;
  const meses = Array.from({ length: 6 }, (_, i) => (centro - 2 + i + 12) % 12);
  const porMes = new Set(consultas.map((c) => parseInt(c.data.slice(5, 7), 10) - 1));

  return (
    <div className="rounded-md border border-slate-100 bg-slate-50 px-3 py-3">
      <div className="mb-2 flex items-center gap-2 text-slate-400">
        <ZoomOut className="h-3.5 w-3.5" />
        <ZoomIn className="h-3.5 w-3.5" />
      </div>
      <div className="flex items-end justify-between gap-2">
        {meses.map((mes) => {
          const marca = porMes.has(mes);
          const ativo = parseInt(selecionada.data.slice(5, 7), 10) - 1 === mes;
          const consultaMes = consultas.find((c) => parseInt(c.data.slice(5, 7), 10) - 1 === mes);
          return (
            <button
              key={mes}
              type="button"
              disabled={!consultaMes}
              onClick={() => consultaMes && onSelect(consultaMes.id)}
              className="flex flex-1 flex-col items-center gap-1 text-xs disabled:opacity-40"
            >
              <span className={ativo ? 'font-semibold text-slate-800' : 'text-slate-500'}>{MESES[mes]}</span>
              <span className="relative h-2 w-full rounded-full bg-slate-200">
                {marca ? (
                  <span className="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full" style={{ backgroundColor: TEAL }} />
                ) : null}
              </span>
              {ativo ? (
                <span className="text-center text-[10px] leading-tight" style={{ color: TEAL }}>
                  Clínica
                  <br />
                  {formatDateBR(selecionada.data)}
                </span>
              ) : (
                <span className="h-6" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
