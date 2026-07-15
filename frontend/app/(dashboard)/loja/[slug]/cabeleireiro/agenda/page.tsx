'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { CalendarDays, Check, List, Lock, MessageCircle, Plus, Trash2 } from 'lucide-react';
import type { DatesSetArg, EventClickArg, EventDropArg } from '@fullcalendar/core';
import type { DateClickArg, EventResizeDoneArg } from '@fullcalendar/interaction';
import { Modal } from '@/components/ui/Modal';
import { SalaoPageHeader } from '@/components/cabeleireiro/SalaoPageHeader';
import { SalaoAgendaLista } from '@/components/cabeleireiro/SalaoAgendaLista';
import { ModalBloqueioSalao } from '@/components/cabeleireiro/ModalBloqueioSalao';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import {
  dateFromFc,
  formatDateRangeISO,
  mergeSalaoAgendaStatusColors,
  salaoAgendamentoToEvent,
  salaoBloqueioToEvent,
  SALAO_STATUS_COLORS,
  SALAO_STATUS_LABEL,
  shiftRange,
  weekRangeAround,
  type SalaoCalendarEvent,
  type SalaoStatusColorMap,
} from '@/components/cabeleireiro/salao-agenda-mappers';
import {
  CabeleireiroAPI,
  type SalaoAgendamento,
  type SalaoCliente,
  type SalaoProfissional,
  type SalaoServico,
} from '@/lib/cabeleireiro-api';
import apiClient from '@/lib/api-client';

const FullCalendar = dynamic(() => import('@fullcalendar/react'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-[420px] text-sm text-gray-500">
      Carregando calendário...
    </div>
  ),
});

const MOBILE_BP = 640;

export default function SalaoAgendaPage() {
  const [plugins, setPlugins] = useState<unknown[]>([]);
  const [locale, setLocale] = useState<unknown>(null);
  const [isMobile, setIsMobile] = useState(false);
  const [modoAgenda, setModoAgenda] = useState<'grade' | 'lista'>('grade');
  const [events, setEvents] = useState<SalaoCalendarEvent[]>([]);
  const [clientes, setClientes] = useState<SalaoCliente[]>([]);
  const [profissionais, setProfissionais] = useState<SalaoProfissional[]>([]);
  const [servicos, setServicos] = useState<SalaoServico[]>([]);
  const [statusColors, setStatusColors] = useState<SalaoStatusColorMap>(() =>
    mergeSalaoAgendaStatusColors(),
  );
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<{ data_inicio: string; data_fim: string } | null>(() =>
    weekRangeAround(),
  );
  const [openCreate, setOpenCreate] = useState(false);
  const [openBloqueio, setOpenBloqueio] = useState(false);
  const [detail, setDetail] = useState<SalaoAgendamento | null>(null);
  const [bloqueioDetail, setBloqueioDetail] = useState<SalaoCalendarEvent | null>(null);
  const [saving, setSaving] = useState(false);
  const [reenviando, setReenviando] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    cliente: '',
    profissional: '',
    servico: '',
    data: '',
    hora_inicio: '09:00',
    observacoes: '',
  });
  const loadRef = useRef<(a: string, b: string) => Promise<void>>(async () => undefined);

  const servicosById = useMemo(() => new Map(servicos.map((s) => [s.id, s])), [servicos]);

  useEffect(() => {
    void Promise.all([
      import('@fullcalendar/daygrid').then((m) => m.default),
      import('@fullcalendar/timegrid').then((m) => m.default),
      import('@fullcalendar/interaction').then((m) => m.default),
      import('@fullcalendar/core/locales/pt-br').then((m) => m.default),
    ]).then(([dayGrid, timeGrid, interaction, ptBr]) => {
      setPlugins([dayGrid, timeGrid, interaction]);
      setLocale(ptBr);
    });
  }, []);

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BP - 1}px)`);
    const sync = () => setIsMobile(mql.matches);
    sync();
    mql.addEventListener('change', sync);
    return () => mql.removeEventListener('change', sync);
  }, []);

  useEffect(() => {
    void Promise.all([
      CabeleireiroAPI.clientes.list(),
      CabeleireiroAPI.profissionais.list(),
      CabeleireiroAPI.servicos.list(),
      apiClient
        .get<{ agenda_status_colors?: Record<string, { bg?: string; border?: string }> | null }>(
          '/crm-vendas/login-config/',
        )
        .then((r) => r.data)
        .catch(() => null),
    ])
      .then(([cls, prs, svs, loginCfg]) => {
        setClientes(cls);
        setProfissionais(prs);
        setServicos(svs);
        if (loginCfg) {
          setStatusColors(mergeSalaoAgendaStatusColors(loginCfg.agenda_status_colors));
        }
      })
      .catch(() => undefined);
  }, []);

  const loadRange = useCallback(
    async (data_inicio: string, data_fim: string) => {
      setLoading(true);
      try {
        const [list, bloqueios] = await Promise.all([
          CabeleireiroAPI.agendamentos.list({ data_inicio, data_fim }),
          CabeleireiroAPI.bloqueios.list({ start: data_inicio, end: data_fim }),
        ]);
        setEvents([
          ...list.map((ag) => salaoAgendamentoToEvent(ag, servicosById, statusColors)),
          ...bloqueios.map(salaoBloqueioToEvent),
        ]);
      } catch {
        setEvents([]);
      } finally {
        setLoading(false);
      }
    },
    [servicosById, statusColors],
  );

  loadRef.current = loadRange;

  useEffect(() => {
    if (!range) return;
    void loadRange(range.data_inicio, range.data_fim);
  }, [range, loadRange]);

  // Polling: atualiza cor após confirmação WhatsApp sem precisar F5
  useEffect(() => {
    if (!range) return;
    const timer = window.setInterval(() => {
      void loadRef.current(range.data_inicio, range.data_fim);
    }, 8000);
    return () => window.clearInterval(timer);
  }, [range]);

  // Sincroniza modal de detalhe quando o status muda (ex.: CLIENT_CONFIRMED)
  useEffect(() => {
    if (!detail) return;
    const found = events.find((e) => e.extendedProps.agendamento?.id === detail.id);
    const ag = found?.extendedProps.agendamento;
    if (ag && ag.status !== detail.status) {
      setDetail(ag);
    }
  }, [events, detail]);

  const onDatesSet = (arg: DatesSetArg) => {
    const next = formatDateRangeISO(arg.start, arg.end);
    setRange((prev) => {
      if (prev?.data_inicio === next.data_inicio && prev?.data_fim === next.data_fim) return prev;
      return next;
    });
  };

  const openNew = (prefill?: { data?: string; hora_inicio?: string }) => {
    setForm({
      cliente: clientes[0] ? String(clientes[0].id) : '',
      profissional: profissionais[0] ? String(profissionais[0].id) : '',
      servico: servicos[0] ? String(servicos[0].id) : '',
      data: prefill?.data || new Date().toISOString().slice(0, 10),
      hora_inicio: prefill?.hora_inicio || '09:00',
      observacoes: '',
    });
    setError('');
    setOpenCreate(true);
  };

  const saveCreate = async () => {
    if (!form.cliente || !form.data) {
      setError('Selecione cliente e data');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const servico = servicos.find((s) => String(s.id) === form.servico);
      await CabeleireiroAPI.agendamentos.create({
        cliente: Number(form.cliente),
        profissional: form.profissional ? Number(form.profissional) : null,
        servico: form.servico ? Number(form.servico) : null,
        data: form.data,
        hora_inicio: form.hora_inicio,
        valor: servico?.preco ?? 0,
        observacoes: form.observacoes,
        status: 'SCHEDULED',
      });
      setOpenCreate(false);
      if (range) await loadRange(range.data_inicio, range.data_fim);
    } catch {
      setError('Erro ao criar agendamento');
    } finally {
      setSaving(false);
    }
  };

  const onEventClick = (info: EventClickArg) => {
    const props = info.event.extendedProps as SalaoCalendarEvent['extendedProps'];
    if (props.isBloqueio) {
      setBloqueioDetail({
        id: String(info.event.id),
        title: info.event.title,
        start: info.event.startStr,
        end: info.event.endStr,
        backgroundColor: info.event.backgroundColor || '#4f46e5',
        borderColor: info.event.borderColor || '#4338ca',
        textColor: '#fff',
        extendedProps: props,
      });
      return;
    }
    if (props.agendamento) setDetail(props.agendamento);
  };

  const onListaAbrir = (evt: SalaoCalendarEvent) => {
    if (evt.extendedProps.isBloqueio) {
      setBloqueioDetail(evt);
      return;
    }
    if (evt.extendedProps.agendamento) setDetail(evt.extendedProps.agendamento);
  };

  const onDateClick = (info: DateClickArg) => {
    const { data, hora_inicio } = dateFromFc(info.date);
    openNew({ data, hora_inicio: info.allDay ? '09:00' : hora_inicio });
  };

  const patchFromCalendar = async (agId: number, start: Date, end: Date | null) => {
    const { data, hora_inicio } = dateFromFc(start);
    const payload: Record<string, unknown> = { data, hora_inicio };
    if (end) {
      payload.hora_fim = `${String(end.getHours()).padStart(2, '0')}:${String(end.getMinutes()).padStart(2, '0')}`;
    }
    await CabeleireiroAPI.agendamentos.update(agId, payload);
    if (range) await loadRange(range.data_inicio, range.data_fim);
  };

  const onEventDrop = async (info: EventDropArg) => {
    if (info.event.extendedProps.isBloqueio) {
      info.revert();
      return;
    }
    try {
      await patchFromCalendar(Number(info.event.id), info.event.start!, info.event.end);
    } catch {
      info.revert();
      alert('Não foi possível mover o agendamento');
    }
  };

  const onEventResize = async (info: EventResizeDoneArg) => {
    if (info.event.extendedProps.isBloqueio) {
      info.revert();
      return;
    }
    try {
      await patchFromCalendar(Number(info.event.id), info.event.start!, info.event.end);
    } catch {
      info.revert();
      alert('Não foi possível alterar a duração');
    }
  };

  const confirmarChegada = async () => {
    if (!detail) return;
    try {
      const updated = await CabeleireiroAPI.confirmarChegada(detail.id);
      setDetail(updated);
      if (range) await loadRange(range.data_inicio, range.data_fim);
    } catch {
      alert('Não foi possível confirmar chegada');
    }
  };

  const reenviarWhatsApp = async () => {
    if (!detail) return;
    setReenviando(true);
    try {
      await CabeleireiroAPI.reenviarConfirmacaoWhatsApp(detail.id);
      alert('Confirmação reenviada por WhatsApp.');
    } catch (e: unknown) {
      const detailMsg =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      alert(detailMsg || 'Não foi possível reenviar. Verifique WhatsApp em Configurações.');
    } finally {
      setReenviando(false);
    }
  };

  const removerBloqueio = async () => {
    const id = bloqueioDetail?.extendedProps.bloqueioId;
    if (!id) return;
    if (!confirm('Remover este bloqueio?')) return;
    try {
      await CabeleireiroAPI.bloqueios.remove(id);
      setBloqueioDetail(null);
      if (range) await loadRange(range.data_inicio, range.data_fim);
    } catch {
      alert('Não foi possível remover o bloqueio');
    }
  };

  const statusColor = detail
    ? SALAO_STATUS_COLORS[detail.status] || { bg: SALAO_PRIMARY, border: SALAO_PRIMARY, text: '#fff' }
    : null;

  return (
    <div className="flex flex-col h-full min-h-[70vh]">
      <SalaoPageHeader
        title="Agenda"
        subtitle="Calendário, lista e bloqueios — mesmo padrão da clínica"
        icon={CalendarDays}
        onNew={() => openNew()}
        newLabel="Novo agendamento"
      >
        <button
          type="button"
          onClick={() => setModoAgenda((m) => (m === 'grade' ? 'lista' : 'grade'))}
          className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 border border-[#E8D5DC] rounded-lg bg-white text-gray-800 text-xs sm:text-sm hover:bg-[#FBF5F7] shrink-0"
          title={modoAgenda === 'grade' ? 'Ver agenda em lista' : 'Ver agenda em calendário'}
        >
          {modoAgenda === 'grade' ? <List size={16} /> : <CalendarDays size={16} />}
          <span className="hidden sm:inline">{modoAgenda === 'grade' ? 'Lista' : 'Calendário'}</span>
        </button>
        <button
          type="button"
          onClick={() => setOpenBloqueio(true)}
          className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-amber-500 text-white rounded-lg hover:bg-amber-600 shrink-0 text-xs sm:text-sm"
          title="Bloquear horário"
        >
          <Lock size={16} />
          <span className="hidden sm:inline">Bloquear</span>
        </button>
      </SalaoPageHeader>

      <div className="relative flex-1 min-h-0 p-3 md:p-4 overflow-y-auto">
        {loading && (
          <div className="absolute top-4 right-4 z-10 text-xs text-gray-500 bg-white/90 px-2 py-1 rounded-md border border-[#E8D5DC]">
            Atualizando...
          </div>
        )}

        {modoAgenda === 'lista' ? (
          <div className="bg-white rounded-xl border border-[#E8D5DC] p-3 md:p-4 min-h-[520px]">
            <div className="flex items-center gap-2 mb-4">
              <button
                type="button"
                className="px-2.5 py-1.5 border rounded-lg text-sm"
                onClick={() => range && setRange(shiftRange(range, -7))}
              >
                ← Semana
              </button>
              <button
                type="button"
                className="px-2.5 py-1.5 border rounded-lg text-sm"
                onClick={() => setRange(weekRangeAround())}
              >
                Hoje
              </button>
              <button
                type="button"
                className="px-2.5 py-1.5 border rounded-lg text-sm"
                onClick={() => range && setRange(shiftRange(range, 7))}
              >
                Semana →
              </button>
              {range && (
                <span className="text-xs text-gray-500 ml-2">
                  {range.data_inicio} — {range.data_fim}
                </span>
              )}
            </div>
            <SalaoAgendaLista eventos={events} onAbrir={onListaAbrir} />
          </div>
        ) : plugins.length > 0 && locale ? (
          <div className="fc-salao-agenda bg-white rounded-xl border border-[#E8D5DC] p-2 md:p-3 min-h-[520px]">
            <FullCalendar
              key={isMobile ? 'mobile' : 'desktop'}
              plugins={plugins as never[]}
              initialView={isMobile ? 'timeGridDay' : 'timeGridWeek'}
              locale={locale as never}
              editable
              eventStartEditable
              eventDurationEditable
              selectable
              selectMirror
              dayMaxEvents={isMobile ? 6 : true}
              weekends
              events={events}
              datesSet={onDatesSet}
              eventDrop={onEventDrop}
              eventResize={onEventResize}
              eventClick={onEventClick}
              dateClick={onDateClick}
              height="auto"
              headerToolbar={
                isMobile
                  ? { left: 'prev,next', center: 'title', right: 'today' }
                  : {
                      left: 'prev,next today',
                      center: 'title',
                      right: 'timeGridDay,timeGridWeek,dayGridMonth',
                    }
              }
              buttonText={isMobile ? { today: 'Hoje' } : undefined}
              slotMinTime="07:00:00"
              slotMaxTime="21:00:00"
              allDaySlot={false}
              slotDuration="00:15:00"
              slotLabelInterval="01:00:00"
              snapDuration="00:15:00"
            />
          </div>
        ) : (
          <div className="flex items-center justify-center min-h-[420px] text-sm text-gray-500">
            Carregando calendário...
          </div>
        )}
      </div>

      <Modal isOpen={openCreate} onClose={() => setOpenCreate(false)} maxWidth="lg">
        <div className="p-6 space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Plus size={18} /> Novo agendamento
          </h2>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="sm:col-span-2 text-sm space-y-1">
              <span>Cliente *</span>
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={form.cliente}
                onChange={(e) => setForm((f) => ({ ...f, cliente: e.target.value }))}
              >
                <option value="">Selecione</option>
                {clientes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome || c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm space-y-1">
              <span>Profissional</span>
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={form.profissional}
                onChange={(e) => setForm((f) => ({ ...f, profissional: e.target.value }))}
              >
                <option value="">—</option>
                {profissionais.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm space-y-1">
              <span>Serviço</span>
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={form.servico}
                onChange={(e) => setForm((f) => ({ ...f, servico: e.target.value }))}
              >
                <option value="">—</option>
                {servicos.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm space-y-1">
              <span>Data</span>
              <input
                type="date"
                className="w-full border rounded-lg px-3 py-2"
                value={form.data}
                onChange={(e) => setForm((f) => ({ ...f, data: e.target.value }))}
              />
            </label>
            <label className="text-sm space-y-1">
              <span>Horário</span>
              <input
                type="time"
                className="w-full border rounded-lg px-3 py-2"
                value={form.hora_inicio}
                onChange={(e) => setForm((f) => ({ ...f, hora_inicio: e.target.value }))}
              />
            </label>
            <label className="sm:col-span-2 text-sm space-y-1">
              <span>Observações</span>
              <textarea
                className="w-full border rounded-lg px-3 py-2 min-h-[70px]"
                value={form.observacoes}
                onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))}
              />
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setOpenCreate(false)} className="px-4 py-2 border rounded-lg text-sm">
              Cancelar
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => void saveCreate()}
              className="px-4 py-2 rounded-lg text-sm text-white disabled:opacity-60"
              style={{ backgroundColor: SALAO_PRIMARY }}
            >
              {saving ? 'Salvando...' : 'Agendar'}
            </button>
          </div>
        </div>
      </Modal>

      <ModalBloqueioSalao
        isOpen={openBloqueio}
        onClose={() => setOpenBloqueio(false)}
        onSuccess={() => {
          if (range) void loadRange(range.data_inicio, range.data_fim);
        }}
        profissionais={profissionais}
        dataSugerida={range?.data_inicio}
      />

      <Modal isOpen={Boolean(detail)} onClose={() => setDetail(null)} maxWidth="md">
        {detail && (
          <div className="p-6 space-y-4">
            <div className="flex items-start gap-3">
              <span
                className="mt-1 w-3 h-3 rounded-full shrink-0"
                style={{ backgroundColor: statusColor?.bg }}
                aria-hidden
              />
              <div>
                <h2 className="text-lg font-semibold">{detail.cliente_nome}</h2>
                <p className="text-xs font-medium mt-0.5" style={{ color: statusColor?.bg }}>
                  {SALAO_STATUS_LABEL[detail.status] || detail.status_display || detail.status}
                </p>
              </div>
            </div>
            <div className="text-sm text-gray-600 space-y-1">
              <p>
                <strong>Quando:</strong> {detail.data} às {(detail.hora_inicio || '').slice(0, 5)}
              </p>
              <p>
                <strong>Serviço:</strong> {detail.servico_nome || '—'}
              </p>
              <p>
                <strong>Profissional:</strong> {detail.profissional_nome || '—'}
              </p>
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              {detail.status === 'SCHEDULED' && (
                <button
                  type="button"
                  disabled={reenviando}
                  onClick={() => void reenviarWhatsApp()}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border"
                  style={{ color: SALAO_PRIMARY, borderColor: '#E8D5DC' }}
                >
                  <MessageCircle size={14} />
                  {reenviando ? 'Enviando...' : 'Reenviar WhatsApp'}
                </button>
              )}
              {(detail.status === 'SCHEDULED' ||
                detail.status === 'CLIENT_CONFIRMED' ||
                detail.status === 'ARRIVED') && (
                <button
                  type="button"
                  disabled={detail.status === 'ARRIVED'}
                  onClick={() => void confirmarChegada()}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-white disabled:opacity-60"
                  style={{ backgroundColor: SALAO_PRIMARY }}
                >
                  <Check size={14} />
                  {detail.status === 'ARRIVED' ? 'Chegou' : 'Confirmar chegada'}
                </button>
              )}
              <button type="button" onClick={() => setDetail(null)} className="ml-auto px-3 py-2 text-sm border rounded-lg">
                Fechar
              </button>
            </div>
          </div>
        )}
      </Modal>

      <Modal isOpen={Boolean(bloqueioDetail)} onClose={() => setBloqueioDetail(null)} maxWidth="sm">
        {bloqueioDetail && (
          <div className="p-6 space-y-4">
            <h2 className="text-lg font-semibold">Bloqueio</h2>
            <p className="text-sm text-gray-700">{bloqueioDetail.extendedProps.motivo || bloqueioDetail.title}</p>
            <p className="text-xs text-gray-500">
              Profissional: {bloqueioDetail.extendedProps.professional_name || 'Todos'}
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => void removerBloqueio()}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-white bg-red-600 hover:bg-red-700"
              >
                <Trash2 size={14} /> Remover
              </button>
              <button type="button" onClick={() => setBloqueioDetail(null)} className="px-3 py-2 text-sm border rounded-lg">
                Fechar
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
