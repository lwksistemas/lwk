'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ChevronLeft, ChevronRight, Printer, User } from 'lucide-react';
import { AgendamentoRapido } from '@/components/clinica-geral/AgendamentoRapido';
import { RecepcionarModal } from '@/components/clinica-geral/RecepcionarModal';
import { ResumoAgendamento } from '@/components/clinica-geral/ResumoAgendamento';
import { getConfiguracao, getPaciente, listConsultas, listHorariosLivres } from '@/lib/clinica-geral-api';
import { NAVY, TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta, DiaHorariosLivres, PacienteLista } from '@/lib/clinica-geral-types';
import { STATUS_LABEL, TIPO_CONSULTA_LABEL } from '@/lib/clinica-geral-types';
import {
  addDays,
  formatHora,
  formatLivreHeading,
  formatLongDate,
  slotTimes,
  slotTimesFromConfig,
  toISODate,
} from '@/lib/clinica-geral-utils';

export function AgendaPage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const search = useSearchParams();
  const data = search.get('data') || toISODate(new Date());
  const abrirNova = search.get('nova') === '1';
  const pacienteId = Number(search.get('paciente') || 0);

  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [livres, setLivres] = useState<DiaHorariosLivres[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [slotAberto, setSlotAberto] = useState<string | null>(abrirNova ? nextLivre(livres, data) : null);
  const [pacienteInicial, setPacienteInicial] = useState<PacienteLista | null>(null);
  const [resumo, setResumo] = useState<Consulta | null>(null);
  const [recepcionar, setRecepcionar] = useState<Consulta | null>(null);
  const [slots, setSlots] = useState<string[]>(() => slotTimes());

  const setData = (iso: string) => router.replace(`/loja/${slug}/clinica-geral/agenda?data=${iso}`);

  const carregar = useCallback(async () => {
    setLoading(true);
    setErro('');
    try {
      const [lista, horarios] = await Promise.all([listConsultas(data), listHorariosLivres(data)]);
      setConsultas(lista.filter((c) => c.status !== 'desmarcado'));
      setLivres(horarios);
    } catch {
      setErro('Não foi possível carregar a agenda.');
    } finally {
      setLoading(false);
    }
  }, [data]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  useEffect(() => {
    void getConfiguracao()
      .then((c) => setSlots(slotTimesFromConfig(c.hora_inicio, c.hora_fim, c.duracao_minutos)))
      .catch(() => setSlots(slotTimes()));
  }, []);

  useEffect(() => {
    if (!abrirNova) return;
    const hora = nextLivre(livres, data) || slots[0];
    setSlotAberto(hora);
  }, [abrirNova, livres, data, slots]);

  useEffect(() => {
    if (!pacienteId) return;
    void getPaciente(pacienteId)
      .then((p) => setPacienteInicial(p))
      .catch(() => setPacienteInicial(null));
  }, [pacienteId]);

  const porHora = useMemo(() => {
    const map = new Map<string, Consulta>();
    for (const c of consultas) map.set(formatHora(c.hora), c);
    return map;
  }, [consultas]);

  const hoje = toISODate(new Date());

  return (
    <div className="flex min-h-full">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#1E1D3A]">
          <button
            type="button"
            onClick={() => setSlotAberto(nextLivre(livres, data) || slots[0])}
            className="rounded-md px-4 py-2 text-sm font-medium text-white"
            style={{ backgroundColor: TEAL }}
          >
            nova consulta
          </button>
          <button
            type="button"
            onClick={() => setData(hoje)}
            disabled={data === hoje}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 disabled:cursor-default disabled:opacity-40 dark:border-white/25 dark:text-slate-200 dark:hover:bg-white/10"
          >
            Ir para hoje
          </button>
          <button type="button" onClick={() => setData(addDays(data, -1))} className="rounded p-1.5 hover:bg-slate-100 dark:hover:bg-white/10" aria-label="Dia anterior">
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button type="button" onClick={() => setData(addDays(data, 1))} className="rounded p-1.5 hover:bg-slate-100 dark:hover:bg-white/10" aria-label="Próximo dia">
            <ChevronRight className="h-4 w-4" />
          </button>
          <h1 className="text-lg font-semibold capitalize text-slate-800 dark:text-slate-100">{formatLongDate(data)}</h1>
          <button type="button" className="ml-auto rounded p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/10" title="Imprimir" onClick={() => window.print()}>
            <Printer className="h-4 w-4" />
          </button>
        </div>

        {erro && <p className="px-4 py-2 text-sm text-red-600">{erro}</p>}

        <div className="flex-1 overflow-auto">
          {loading ? (
            <p className="p-6 text-sm text-slate-500">Carregando agenda...</p>
          ) : (
            <div>
              {slots.map((slot, i) => {
                const consulta = porHora.get(slot);
                return (
                  <div
                    key={slot}
                    className={`flex w-full items-stretch border-b border-slate-100 dark:border-white/5 ${
                      i % 2 === 0 ? 'bg-[#F4F6FB] dark:bg-[#252448]' : 'bg-white dark:bg-[#1E1D3A]'
                    }`}
                  >
                    <span className="w-16 shrink-0 px-3 py-2.5 text-xs font-medium text-slate-600 dark:text-slate-300">{slot}</span>
                    <div className="min-h-[52px] flex-1 px-2 py-1">
                      {consulta ? (
                        <div
                          role="button"
                          tabIndex={0}
                          title={STATUS_LABEL[consulta.status]}
                          onClick={() => setResumo(consulta)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') setResumo(consulta);
                          }}
                          className="flex items-center gap-2 overflow-hidden rounded-md border border-slate-200 bg-white text-left text-sm text-slate-800 dark:border-white/15 dark:bg-[#2F2E5B] dark:text-white"
                        >
                          <span className="h-full w-1.5 self-stretch" style={{ backgroundColor: NAVY }} />
                          <span className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-200">
                            {consulta.paciente_foto_url ? (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img src={consulta.paciente_foto_url} alt="" className="h-full w-full object-cover" />
                            ) : (
                              <User className="h-4 w-4 text-slate-400" />
                            )}
                          </span>
                          <span className="min-w-0 flex-1 py-2">
                            <span className="font-semibold">{consulta.paciente_nome}</span>
                            {consulta.paciente_idade != null ? (
                              <span className="ml-2 text-xs text-slate-500 dark:text-slate-300">{consulta.paciente_idade}a</span>
                            ) : null}
                            {consulta.paciente_alergias ? (
                              <span className="ml-2 rounded bg-red-600 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                                alergia
                              </span>
                            ) : null}
                            <span className="ml-2 text-slate-500 dark:text-slate-300">
                              {TIPO_CONSULTA_LABEL[consulta.tipo]} | {consulta.convenio || 'PARTICULAR'}
                            </span>
                          </span>
                          <button
                            type="button"
                            className="mr-2 shrink-0 rounded-md border border-[#2F2E5B] bg-white px-3 py-1.5 text-xs font-medium text-[#2F2E5B] dark:border-teal-300 dark:bg-transparent dark:text-teal-200"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/loja/${slug}/clinica-geral/pacientes/${consulta.paciente}/prontuario`);
                            }}
                          >
                            Ver Prontuário
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          title={`Agendar às ${slot}`}
                          onClick={() => setSlotAberto(slot)}
                          className="h-full min-h-[44px] w-full"
                        />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
        <p className="border-t border-slate-200 bg-white px-4 py-2 text-xs text-slate-500 dark:border-white/10 dark:bg-[#1E1D3A] dark:text-slate-400">
          Total de agendamentos no dia: {consultas.length}
        </p>
      </div>

      <aside className="hidden w-72 shrink-0 border-l border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#1E1D3A] xl:block">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Próximos horários livres</h2>
        {livres.map((dia) => (
          <div key={dia.data} className="mb-4">
            <p className="mb-2 text-xs capitalize text-slate-500">{formatLivreHeading(dia.data, hoje)}</p>
            <div className="grid grid-cols-4 gap-1.5">
              {dia.horarios.map((h) => (
                <button
                  key={`${dia.data}-${h}`}
                  type="button"
                  onClick={() => {
                    if (dia.data !== data) setData(dia.data);
                    setSlotAberto(h);
                  }}
                  className="rounded border border-slate-200 bg-white px-1 py-1 text-xs text-slate-600 hover:border-teal-500 dark:border-white/15 dark:bg-[#2F2E5B] dark:text-slate-200"
                >
                  {h}
                </button>
              ))}
            </div>
          </div>
        ))}
      </aside>

      {slotAberto && (
        <AgendamentoRapido
          data={data}
          hora={slotAberto}
          pacienteInicial={pacienteInicial}
          onClose={() => {
            setSlotAberto(null);
            if (abrirNova) router.replace(`/loja/${slug}/clinica-geral/agenda?data=${data}`);
          }}
          onSaved={async () => {
            setSlotAberto(null);
            setPacienteInicial(null);
            if (abrirNova) router.replace(`/loja/${slug}/clinica-geral/agenda?data=${data}`);
            await carregar();
          }}
        />
      )}

      {resumo && (
        <ResumoAgendamento
          consulta={resumo}
          slug={slug}
          onClose={() => setResumo(null)}
          onChanged={async () => {
            setResumo(null);
            await carregar();
          }}
          onRecepcionar={() => {
            setRecepcionar(resumo);
          }}
        />
      )}

      {recepcionar && (
        <RecepcionarModal
          consulta={recepcionar}
          onClose={() => setRecepcionar(null)}
          onDone={async () => {
            setRecepcionar(null);
            setResumo(null);
            await carregar();
          }}
        />
      )}
    </div>
  );
}

function nextLivre(livres: DiaHorariosLivres[], data: string): string | null {
  const dia = livres.find((d) => d.data === data);
  return dia?.horarios[0] || null;
}
