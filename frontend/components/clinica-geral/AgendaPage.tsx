'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ChevronLeft, ChevronRight, Printer, X } from 'lucide-react';
import {
  cancelarConsulta,
  createConsulta,
  listConsultas,
  listHorariosLivres,
  listPacientes,
  updateConsulta,
  updateConsultaStatus,
} from '@/lib/clinica-geral-api';
import type { Consulta, DiaHorariosLivres, PacienteLista, StatusConsulta } from '@/lib/clinica-geral-types';
import {
  MODALIDADE_LABEL,
  STATUS_LABEL,
  TIPO_CONSULTA_LABEL,
} from '@/lib/clinica-geral-types';
import {
  addDays,
  formatHora,
  formatLongDate,
  formatShortDate,
  slotTimes,
  toISODate,
} from '@/lib/clinica-geral-utils';

const TEAL = '#0D9B9B';
const SLOTS = slotTimes();

export function AgendaPage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const search = useSearchParams();
  const data = search.get('data') || toISODate(new Date());

  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [livres, setLivres] = useState<DiaHorariosLivres[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [slotAberto, setSlotAberto] = useState<string | null>(null);
  const [resumo, setResumo] = useState<Consulta | null>(null);

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

  const porHora = useMemo(() => {
    const map = new Map<string, Consulta>();
    for (const c of consultas) map.set(formatHora(c.hora), c);
    return map;
  }, [consultas]);

  return (
    <div className="flex min-h-full">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 bg-white px-4 py-3">
          <button
            type="button"
            onClick={() => setSlotAberto(SLOTS[0] || '08:00')}
            className="rounded-md px-4 py-2 text-sm font-medium text-white"
            style={{ backgroundColor: TEAL }}
          >
            nova consulta
          </button>
          <button
            type="button"
            onClick={() => setData(toISODate(new Date()))}
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
                return (
                  <button
                    key={slot}
                    type="button"
                    onClick={() => (consulta ? setResumo(consulta) : setSlotAberto(slot))}
                    className={`flex w-full items-stretch border-b border-slate-100 text-left ${
                      i % 2 === 0 ? 'bg-white' : 'bg-slate-50/80'
                    }`}
                  >
                    <span className="w-16 shrink-0 px-3 py-2 text-xs text-slate-400">{slot}</span>
                    <span className="min-h-[40px] flex-1 px-2 py-1">
                      {consulta && (
                        <span className="flex items-center gap-2 rounded-md bg-[#E8EEF6] px-3 py-1.5 text-sm text-slate-800">
                          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-300 text-[10px]">
                            {consulta.paciente_nome.slice(0, 1)}
                          </span>
                          <span className="font-medium">{consulta.paciente_nome}</span>
                          <span className="text-slate-500">
                            {TIPO_CONSULTA_LABEL[consulta.tipo]} | {consulta.convenio || 'PARTICULAR'}
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

      <aside className="hidden w-64 shrink-0 border-l border-slate-200 bg-white p-4 xl:block">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Próximos horários livres</h2>
        {livres.map((dia) => (
          <div key={dia.data} className="mb-4">
            <p className="mb-2 text-xs capitalize text-slate-500">{formatShortDate(dia.data)}</p>
            <div className="grid grid-cols-3 gap-1.5">
              {dia.horarios.slice(0, 16).map((h) => (
                <button
                  key={`${dia.data}-${h}`}
                  type="button"
                  onClick={() => {
                    if (dia.data !== data) setData(dia.data);
                    setSlotAberto(h);
                  }}
                  className="rounded border border-slate-200 px-1 py-1 text-xs text-slate-600 hover:border-teal-400"
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
          onClose={() => setSlotAberto(null)}
          onSaved={async () => {
            setSlotAberto(null);
            await carregar();
          }}
        />
      )}

      {resumo && (
        <ResumoAgendamento
          consulta={resumo}
          onClose={() => setResumo(null)}
          onChanged={async () => {
            setResumo(null);
            await carregar();
          }}
        />
      )}
    </div>
  );
}

function AgendamentoRapido({
  data,
  hora,
  onClose,
  onSaved,
}: {
  data: string;
  hora: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [q, setQ] = useState('');
  const [opcoes, setOpcoes] = useState<PacienteLista[]>([]);
  const [paciente, setPaciente] = useState<PacienteLista | null>(null);
  const [telefone, setTelefone] = useState('');
  const [email, setEmail] = useState('');
  const [convenio, setConvenio] = useState('PARTICULAR');
  const [tipo, setTipo] = useState<Consulta['tipo']>('consulta');
  const [modalidade, setModalidade] = useState<Consulta['modalidade']>('presencial');
  const [saving, setSaving] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    const t = setTimeout(() => {
      if (!q.trim()) {
        setOpcoes([]);
        return;
      }
      void listPacientes({ q: q.trim() }).then(setOpcoes).catch(() => setOpcoes([]));
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  const escolher = (p: PacienteLista) => {
    setPaciente(p);
    setQ(p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome);
    setTelefone(p.telefone);
    setEmail(p.email);
    setOpcoes([]);
  };

  const salvar = async () => {
    if (!paciente) {
      setErro('Selecione um paciente cadastrado.');
      return;
    }
    setSaving(true);
    setErro('');
    try {
      await createConsulta({
        paciente: paciente.id,
        data,
        hora: `${hora}:00`,
        tipo,
        modalidade,
        convenio,
        status: 'agendado',
      });
      await onSaved();
    } catch {
      setErro('Não foi possível agendar.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex bg-black/20">
      <div className="flex h-full w-full max-w-md flex-col bg-white shadow-xl">
        <div className="flex items-start justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Agendamento rápido</h2>
            <p className="mt-1 text-sm capitalize text-slate-500">
              {formatShortDate(data)}, às {hora}
            </p>
          </div>
          <button type="button" onClick={onClose} aria-label="Fechar">
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>
        <div className="flex-1 space-y-3 overflow-auto px-5 py-4">
          <div className="relative">
            <input
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setPaciente(null);
              }}
              placeholder="Nome ou CPF do paciente"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500"
            />
            {opcoes.length > 0 && (
              <ul className="absolute z-10 mt-1 w-full rounded-md border border-slate-200 bg-white shadow">
                {opcoes.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => escolher(p)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-slate-50"
                    >
                      {p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <input
            value={telefone}
            onChange={(e) => setTelefone(e.target.value)}
            placeholder="Telefone"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="E-mail"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <select
            value={convenio}
            onChange={(e) => setConvenio(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="PARTICULAR">PARTICULAR</option>
          </select>
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value as Consulta['tipo'])}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {Object.entries(TIPO_CONSULTA_LABEL).map(([k, label]) => (
              <option key={k} value={k}>
                {label}
              </option>
            ))}
          </select>
          <select
            value={modalidade}
            onChange={(e) => setModalidade(e.target.value as Consulta['modalidade'])}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {Object.entries(MODALIDADE_LABEL).map(([k, label]) => (
              <option key={k} value={k}>
                {label}
              </option>
            ))}
          </select>
          {erro && <p className="text-sm text-red-600">{erro}</p>}
        </div>
        <div className="flex gap-2 border-t border-slate-100 px-5 py-4">
          <button type="button" onClick={onClose} className="flex-1 rounded-md border border-slate-300 py-2 text-sm">
            Cancelar
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => void salvar()}
            className="flex-1 rounded-md py-2 text-sm font-medium text-white disabled:opacity-60"
            style={{ backgroundColor: TEAL }}
          >
            {saving ? 'Agendando...' : 'Agendar'}
          </button>
        </div>
      </div>
    </div>
  );
}

function ResumoAgendamento({
  consulta,
  onClose,
  onChanged,
}: {
  consulta: Consulta;
  onClose: () => void;
  onChanged: () => Promise<void>;
}) {
  const [busy, setBusy] = useState<string | null>(null);

  const agir = async (acao: StatusConsulta | 'desmarcar') => {
    setBusy(acao);
    try {
      if (acao === 'desmarcar') await cancelarConsulta(consulta.id);
      else await updateConsultaStatus(consulta.id, acao);
      await onChanged();
    } finally {
      setBusy(null);
    }
  };

  const remarcar = async () => {
    const novaData = window.prompt('Nova data (AAAA-MM-DD)', consulta.data);
    if (!novaData) return;
    const novaHora = window.prompt('Novo horário (HH:MM)', formatHora(consulta.hora));
    if (!novaHora) return;
    setBusy('remarcar');
    try {
      await updateConsulta(consulta.id, { data: novaData, hora: `${formatHora(novaHora)}:00`, status: 'agendado' });
      await onChanged();
    } finally {
      setBusy(null);
    }
  };

  const acoes: { id: StatusConsulta | 'desmarcar' | 'remarcar'; label: string }[] = [
    { id: 'confirmado', label: 'Confirmar' },
    { id: 'recepcionado', label: 'Recepcionar' },
    { id: 'desmarcar', label: 'Desmarcar' },
    { id: 'remarcar', label: 'Remarcar' },
    { id: 'faltou', label: 'Faltou' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/20">
      <div className="flex h-full w-full max-w-md flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="text-lg font-semibold text-slate-800">Resumo do agendamento</h2>
          <button type="button" onClick={onClose} aria-label="Fechar">
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>
        <div className="flex-1 space-y-3 overflow-auto px-5 py-4 text-sm">
          <p className="text-lg font-medium">{consulta.paciente_nome}</p>
          <p className="capitalize text-slate-500">
            {formatShortDate(consulta.data)} às {formatHora(consulta.hora)}
          </p>
          <p><span className="text-slate-500">Tipo: </span>{TIPO_CONSULTA_LABEL[consulta.tipo]}</p>
          <p><span className="text-slate-500">Atendimento: </span>{MODALIDADE_LABEL[consulta.modalidade]}</p>
          <p><span className="text-slate-500">Convênio: </span>{consulta.convenio || 'PARTICULAR'}</p>
          <p><span className="text-slate-500">E-mail: </span>{consulta.paciente_email || '—'}</p>
          <p><span className="text-slate-500">Celular: </span>{consulta.paciente_telefone || '—'}</p>
          <p><span className="text-slate-500">Status: </span>{STATUS_LABEL[consulta.status]}</p>
        </div>
        <div className="border-t border-slate-100 px-5 py-4">
          <p className="mb-2 text-sm font-medium text-slate-700">O que você gostaria de fazer agora?</p>
          <div className="grid grid-cols-2 gap-2">
            {acoes.map((a) => (
              <button
                key={a.id}
                type="button"
                disabled={busy !== null}
                onClick={() => (a.id === 'remarcar' ? void remarcar() : void agir(a.id))}
                className="rounded-md border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-60"
              >
                {busy === a.id ? '...' : a.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
