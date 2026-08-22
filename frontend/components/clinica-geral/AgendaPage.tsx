'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ChevronLeft, ChevronRight, Clock, Printer, User } from 'lucide-react';
import { getPaciente, listConsultas, listHorariosLivres } from '@/lib/clinica-geral-api';
import type { Consulta, DiaHorariosLivres, PacienteLista } from '@/lib/clinica-geral-types';
import { STATUS_LABEL, TIPO_CONSULTA_LABEL } from '@/lib/clinica-geral-types';
import {
  addDays,
  cardTone,
  formatHora,
  formatLivreHeading,
  formatLongDate,
  slotTimes,
  toISODate,
} from '@/lib/clinica-geral-utils';
import { AgendamentoRapido } from '@/components/clinica-geral/AgendamentoRapido';
import { RecepcionarModal } from '@/components/clinica-geral/RecepcionarModal';
import { ResumoAgendamento } from '@/components/clinica-geral/ResumoAgendamento';

const TEAL = '#0D9B9B';
const SLOTS = slotTimes();

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
    if (!abrirNova) return;
    const hora = nextLivre(livres, data) || SLOTS[0];
    setSlotAberto(hora);
  }, [abrirNova, livres, data]);

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
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 bg-white px-4 py-3">
          <button
            type="button"
            onClick={() => setSlotAberto(nextLivre(livres, data) || SLOTS[0])}
            className="rounded-md px-4 py-2 text-sm font-medium text-white"
            style={{ backgroundColor: TEAL }}
          >
            nova consulta
          </button>
          <button
            type="button"
            onClick={() => setData(hoje)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
          >
            Ir para hoje
          </button>
          <button type="button" onClick={() => setData(addDays(data, -1))} className="rounded p-1.5 hover:bg-slate-100" aria-label="Dia anterior">
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button type="button" onClick={() => setData(addDays(data, 1))} className="rounded p-1.5 hover:bg-slate-100" aria-label="Próximo dia">
            <ChevronRight className="h-4 w-4" />
          </button>
          <h1 className="text-lg font-semibold capitalize text-slate-800">{formatLongDate(data)}</h1>
          <button type="button" className="ml-auto rounded p-2 text-slate-500 hover:bg-slate-100" title="Imprimir" onClick={() => window.print()}>
            <Printer className="h-4 w-4" />
          </button>
        </div>

        {erro && <p className="px-4 py-2 text-sm text-red-600">{erro}</p>}

        <div className="flex-1 overflow-auto">
          {loading ? (
            <p className="p-6 text-sm text-slate-500">Carregando agenda...</p>
          ) : (
            <div>
              {SLOTS.map((slot, i) => {
                const consulta = porHora.get(slot);
                const tom = consulta ? cardTone(consulta.status) : null;
                return (
                  <button
                    key={slot}
                    type="button"
                    title={consulta ? STATUS_LABEL[consulta.status] : `Agendar às ${slot}`}
                    onClick={() => (consulta ? setResumo(consulta) : setSlotAberto(slot))}
                    className={`flex w-full items-stretch border-b border-slate-100 text-left ${
                      i % 2 === 0 ? 'bg-[#F4F6FB]' : 'bg-white'
                    }`}
                  >
                    <span className="w-16 shrink-0 px-3 py-2.5 text-xs text-slate-400">{slot}</span>
                    <span className="min-h-[44px] flex-1 px-2 py-1">
                      {consulta && tom && (
                        <span
                          className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm text-slate-800"
                          style={{ backgroundColor: tom.bg, borderColor: tom.border }}
                        >
                          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white/70">
                            <User className="h-3.5 w-3.5 text-slate-500" />
                          </span>
                          <span className="font-medium">{consulta.paciente_nome}</span>
                          {consulta.paciente_idade != null && (
                            <span className="text-xs text-slate-600">{consulta.paciente_idade}a</span>
                          )}
                          <span className="text-slate-600">
                            {TIPO_CONSULTA_LABEL[consulta.tipo]} | {consulta.convenio || 'PARTICULAR'}
                          </span>
                          <span className="ml-auto flex items-center gap-1 text-xs text-slate-600">
                            <Clock className="h-3.5 w-3.5" />
                            {consulta.minutos_espera ?? 0} min
                          </span>
                        </span>
                      )}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
        <p className="border-t border-slate-200 bg-white px-4 py-2 text-xs text-slate-500">
          Total de agendamentos no dia: {consultas.length}
        </p>
      </div>

      <aside className="hidden w-72 shrink-0 border-l border-slate-200 bg-white p-4 xl:block">
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
                  className="rounded border border-slate-200 bg-white px-1 py-1 text-xs text-slate-600 hover:border-teal-500"
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
