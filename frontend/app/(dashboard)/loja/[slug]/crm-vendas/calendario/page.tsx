'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import apiClient from '@/lib/api-client';

const MOBILE_BREAKPOINT = 640;

const FullCalendar = dynamic(() => import('@fullcalendar/react'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-[400px] text-gray-500 dark:text-gray-400">
      Carregando calendário...
    </div>
  ),
});

const API_CRM = '/crm-vendas';
const API_GOOGLE_STATUS = `${API_CRM}/google-calendar/status/`;
const API_GOOGLE_AUTH = `${API_CRM}/google-calendar/auth/`;
const API_GOOGLE_SYNC = `${API_CRM}/google-calendar/sync/`;
const API_GOOGLE_DISCONNECT = `${API_CRM}/google-calendar/disconnect/`;

const SYNC_RESULT_DISPLAY_MS = 5000;

export interface Atividade {
  id: number;
  titulo: string;
  tipo: 'call' | 'meeting' | 'email' | 'task';
  oportunidade: number | null;
  lead: number | null;
  data: string;
  duracao_minutos?: number;
  concluido: boolean;
  observacoes: string;
  created_at: string;
  updated_at: string;
}

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  borderColor: string;
  extendedProps: { atividade: Atividade };
}

const TIPO_LABEL: Record<string, string> = {
  call: 'Ligação',
  meeting: 'Reunião',
  email: 'Email',
  task: 'Tarefa',
};

const TIPO_COR: Record<string, { bg: string; border: string }> = {
  call: { bg: '#0ea5e9', border: '#0284c7' },
  meeting: { bg: '#6366f1', border: '#4f46e5' },
  email: { bg: '#8b5cf6', border: '#7c3aed' },
  task: { bg: '#22c55e', border: '#16a34a' },
};

function toISO(date: Date): string {
  return date.toISOString().slice(0, 19) + 'Z';
}

function atividadeToEvent(a: Atividade): CalendarEvent {
  const d = new Date(a.data);
  const end = new Date(d);
  const duracao = a.duracao_minutos ?? 60;
  end.setMinutes(end.getMinutes() + duracao);
  const cor = TIPO_COR[a.tipo] ?? TIPO_COR.task;
  return {
    id: String(a.id),
    title: a.concluido ? `✓ ${a.titulo}` : a.titulo,
    start: a.data,
    end: toISO(end),
    backgroundColor: a.concluido ? '#94a3b8' : cor.bg,
    borderColor: a.concluido ? '#64748b' : cor.border,
    extendedProps: { atividade: a },
  };
}

export default function CalendarioCrmPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [plugins, setPlugins] = useState<any[]>([]);
  const [locale, setLocale] = useState<any>(null);
  const [range, setRange] = useState<{ start: Date; end: Date } | null>(null);
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' && window.innerWidth < MOBILE_BREAKPOINT
  );
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAtividade, setModalAtividade] = useState<Atividade | null>(null);
  const [form, setForm] = useState({ titulo: '', tipo: 'task' as Atividade['tipo'], data: '', duracao_minutos: 60, observacoes: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [googleStatus, setGoogleStatus] = useState<{ connected: boolean; email: string | null }>({ connected: false, email: null });
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleSyncResult, setGoogleSyncResult] = useState<{ pushed: number; pulled: number } | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const syncingRef = useRef(false);
  const searchParams = useSearchParams();

  const loadPlugins = useCallback(async () => {
    const [dayGrid, timeGrid, interaction, ptBr] = await Promise.all([
      import('@fullcalendar/daygrid').then((m) => m.default),
      import('@fullcalendar/timegrid').then((m) => m.default),
      import('@fullcalendar/interaction').then((m) => m.default),
      import('@fullcalendar/core/locales/pt-br').then((m) => m.default),
    ]);
    setPlugins([dayGrid, timeGrid, interaction]);
    setLocale(ptBr);
  }, []);

  const fetchAtividades = useCallback(
    async (start: Date, end: Date) => {
      const dataInicio = toISO(start);
      const dataFim = toISO(end);
      try {
        const res = await apiClient.get<Atividade[] | { results: Atividade[] }>(
          `${API_CRM}/atividades/`,
          { params: { data_inicio: dataInicio, data_fim: dataFim } }
        );
        const list = Array.isArray(res.data) ? res.data : (res.data as { results: Atividade[] }).results ?? [];
        setEvents(list.map(atividadeToEvent));
      } catch (e) {
        setError('Erro ao carregar atividades.');
        setEvents([]);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const loadGoogleStatus = useCallback(async () => {
    try {
      const res = await apiClient.get<{ connected: boolean; email?: string | null }>(API_GOOGLE_STATUS);
      setGoogleStatus({ connected: !!res.data.connected, email: res.data.email ?? null });
    } catch {
      setGoogleStatus({ connected: false, email: null });
    }
  }, []);

  useEffect(() => {
    loadGoogleStatus();
  }, [loadGoogleStatus]);

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const handle = () => setIsMobile(mql.matches);
    mql.addEventListener('change', handle);
    handle();
    return () => mql.removeEventListener('change', handle);
  }, []);

  useEffect(() => {
    const connected = searchParams.get('google_connected');
    const err = searchParams.get('google_error');
    if (connected === '1') {
      setSyncError(null);
      loadGoogleStatus();
      if (typeof window !== 'undefined') {
        window.history.replaceState({}, '', window.location.pathname);
      }
    }
    if (err === '1' && typeof window !== 'undefined') {
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [searchParams, loadGoogleStatus]);

  const handleConnectGoogle = useCallback(async () => {
    setGoogleLoading(true);
    setSyncError(null);
    try {
      const res = await apiClient.get<{ auth_url: string }>(API_GOOGLE_AUTH);
      if (res.data?.auth_url) {
        window.location.href = res.data.auth_url;
        return;
      }
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Google Calendar não configurado. Entre em contato com o suporte.';
      setSyncError(msg);
    } finally {
      setGoogleLoading(false);
    }
  }, []);

  const handleSyncGoogle = useCallback(async () => {
    if (syncingRef.current) return;
    syncingRef.current = true;
    setGoogleLoading(true);
    setGoogleSyncResult(null);
    setSyncError(null);
    try {
      const res = await apiClient.post<{ pushed: number; pulled: number }>(API_GOOGLE_SYNC, {
        direction: 'both',
      });
      setGoogleSyncResult({ pushed: res.data.pushed, pulled: res.data.pulled });
      if (range) await fetchAtividades(range.start, range.end);
      if (SYNC_RESULT_DISPLAY_MS > 0 && typeof window !== 'undefined') {
        window.setTimeout(() => setGoogleSyncResult(null), SYNC_RESULT_DISPLAY_MS);
      }
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Erro ao sincronizar com o Google Calendar.';
      setSyncError(msg);
      if (msg.includes('Token expirado') || msg.includes('inválido')) {
        setGoogleStatus({ connected: false, email: null });
        loadGoogleStatus();
      }
    } finally {
      syncingRef.current = false;
      setGoogleLoading(false);
    }
  }, [range, fetchAtividades, loadGoogleStatus]);

  const handleDisconnectGoogle = useCallback(async () => {
    if (
      !confirm(
        'Desconectar o Google Calendar? Os eventos já enviados permanecem no Google.'
      )
    )
      return;
    setGoogleLoading(true);
    setSyncError(null);
    try {
      await apiClient.delete(API_GOOGLE_DISCONNECT);
      setGoogleStatus({ connected: false, email: null });
      setGoogleSyncResult(null);
    } finally {
      setGoogleLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlugins();
  }, [loadPlugins]);

  useEffect(() => {
    if (!range) return;
    fetchAtividades(range.start, range.end);
  }, [range, fetchAtividades]);

  const handleDatesSet = useCallback((arg: { start: Date; end: Date }) => {
    setRange({ start: arg.start, end: arg.end });
  }, []);

  const handleSelect = useCallback((arg: { start: Date; end: Date }) => {
    setModalAtividade(null);
    setForm({
      titulo: '',
      tipo: 'task',
      data: arg.start.toISOString().slice(0, 16),
      duracao_minutos: 60,
      observacoes: '',
    });
    setModalOpen(true);
    setError(null);
  }, []);

  const handleEventClick = useCallback((arg: { event: { extendedProps?: { atividade?: Atividade } }; jsEvent: MouseEvent }) => {
    arg.jsEvent.preventDefault();
    const a = arg.event.extendedProps?.atividade;
    if (!a) return;
    setModalAtividade(a);
    setForm({
      titulo: a.titulo,
      tipo: a.tipo,
      data: a.data.slice(0, 16),
      duracao_minutos: a.duracao_minutos ?? 60,
      observacoes: a.observacoes || '',
    });
    setModalOpen(true);
    setError(null);
  }, []);

  const handleCloseModal = useCallback(() => {
    setModalOpen(false);
    setModalAtividade(null);
    setError(null);
  }, []);

  const handleSave = useCallback(async () => {
    if (!form.titulo.trim()) {
      setError('Preencha o título.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload = {
        titulo: form.titulo.trim(),
        tipo: form.tipo,
        data: new Date(form.data).toISOString(),
        duracao_minutos: form.duracao_minutos,
        observacoes: form.observacoes.trim(),
      };
      if (modalAtividade) {
        await apiClient.patch(`${API_CRM}/atividades/${modalAtividade.id}/`, payload);
      } else {
        await apiClient.post(`${API_CRM}/atividades/`, payload);
      }
      handleCloseModal();
      if (range) fetchAtividades(range.start, range.end);
      if (googleStatus.connected && !syncingRef.current) {
        handleSyncGoogle();
      }
    } catch (e: any) {
      setError(e.response?.data?.titulo?.[0] || e.response?.data?.detail || 'Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  }, [form, modalAtividade, range, fetchAtividades, handleCloseModal, googleStatus.connected, handleSyncGoogle]);

  const handleToggleConcluido = useCallback(async () => {
    if (!modalAtividade) return;
    setSaving(true);
    setError(null);
    try {
      await apiClient.patch(`${API_CRM}/atividades/${modalAtividade.id}/`, {
        concluido: !modalAtividade.concluido,
      });
      handleCloseModal();
      if (range) fetchAtividades(range.start, range.end);
      if (googleStatus.connected && !syncingRef.current) {
        handleSyncGoogle();
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Erro ao atualizar.');
    } finally {
      setSaving(false);
    }
  }, [modalAtividade, range, fetchAtividades, handleCloseModal, googleStatus.connected, handleSyncGoogle]);

  const handleDelete = useCallback(async () => {
    if (!modalAtividade || !confirm('Excluir esta atividade?')) return;
    setSaving(true);
    setError(null);
    try {
      await apiClient.delete(`${API_CRM}/atividades/${modalAtividade.id}/`);
      handleCloseModal();
      if (range) fetchAtividades(range.start, range.end);
      if (googleStatus.connected && !syncingRef.current) {
        handleSyncGoogle();
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Erro ao excluir.');
    } finally {
      setSaving(false);
    }
  }, [modalAtividade, range, fetchAtividades, handleCloseModal, googleStatus.connected, handleSyncGoogle]);

  return (
    <div className="h-full min-h-0 flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-3 sm:gap-4 mb-3 sm:mb-4 shrink-0">
        <div className="min-w-0">
          <h1 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white truncate">
            Calendário
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
            Sincronizado com as atividades do CRM
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 shrink-0">
          {googleStatus.connected ? (
            <>
              <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 truncate max-w-[120px] sm:max-w-none" title={googleStatus.email ?? undefined}>
                {googleStatus.email ? `Google: ${googleStatus.email}` : 'Google conectado'}
              </span>
              <button
                type="button"
                onClick={handleSyncGoogle}
                disabled={googleLoading}
                className="px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium bg-[#0176d3] hover:bg-[#0159a8] text-white disabled:opacity-50 touch-manipulation"
              >
                {googleLoading ? '...' : 'Sincronizar'}
              </button>
              <button
                type="button"
                onClick={handleDisconnectGoogle}
                disabled={googleLoading}
                className="px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 touch-manipulation"
              >
                Desconectar
              </button>
            </>
          ) : (
            <div className="flex flex-col gap-2">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Para sincronizar, conecte sua conta Google e autorize o acesso ao calendário.
              </p>
              <details className="text-xs text-gray-500 dark:text-gray-400 group">
                <summary className="cursor-pointer hover:text-gray-700 dark:hover:text-gray-300 list-none [&::-webkit-details-marker]:hidden">
                  <span className="inline-flex items-center gap-1">
                    <span className="group-open:rotate-90 transition-transform">▶</span>
                    Ver aviso sobre a tela do Google
                  </span>
                </summary>
                <p className="mt-2 pl-4 border-l-2 border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400">
                  O Google pode exibir &quot;O app não foi verificado&quot; — isso é normal. O LWK Sistemas usa a integração de forma segura apenas para sincronizar seu calendário. Clique em <strong>Continuar</strong> ou <strong>Avançado → Acessar</strong> para autorizar.
                </p>
              </details>
              <button
                type="button"
                onClick={handleConnectGoogle}
                disabled={googleLoading}
                className="px-3 py-2 rounded-lg text-sm font-medium bg-[#4285f4] hover:bg-[#3367d6] text-white disabled:opacity-50 flex items-center gap-2 w-fit"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24"><path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                Conectar Google Calendar
              </button>
            </div>
          )}
        </div>
      </div>
      {(searchParams.get('google_error') === '1' || syncError) && (
        <p className="mb-3 text-sm text-amber-600 dark:text-amber-400">
          {syncError || 'Não foi possível conectar ao Google. Tente novamente.'}
        </p>
      )}
      {googleSyncResult && !syncError && (
        <p className="mb-3 text-sm text-green-600 dark:text-green-400">
          Sincronizado: {googleSyncResult.pushed} enviado(s) ao Google, {googleSyncResult.pulled} importado(s) do Google.
        </p>
      )}

      <div className="flex-1 min-h-[400px] sm:min-h-[500px] rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 overflow-hidden fc-agenda-mobile">
        {plugins.length > 0 && locale && (
          <FullCalendar
            key={isMobile ? 'mobile' : 'desktop'}
            plugins={plugins}
            locale={locale}
            themeSystem="standard"
            initialView={isMobile ? 'timeGridDay' : 'dayGridMonth'}
            headerToolbar={
              isMobile
                ? { left: 'prev,next', center: 'title', right: 'today' }
                : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay' }
            }
            buttonText={
              isMobile
                ? { today: 'Hoje' }
                : { today: 'Hoje', month: 'Mês', week: 'Semana', day: 'Dia' }
            }
            slotMinTime="06:00:00"
            slotMaxTime="22:00:00"
            allDaySlot={false}
            editable
            selectable
            selectMirror
            dayMaxEvents={isMobile ? 6 : 4}
            weekends
            events={events}
            datesSet={handleDatesSet}
            select={handleSelect}
            eventClick={handleEventClick}
            height="100%"
            eventDisplay="block"
          />
        )}
        {loading && plugins.length === 0 && (
          <div className="flex items-center justify-center min-h-[400px] text-gray-500">
            Carregando...
          </div>
        )}
      </div>

      {modalOpen && (
        <>
          <div className="fixed inset-0 bg-black/50 z-40" onClick={handleCloseModal} aria-hidden="true" />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {modalAtividade ? 'Editar atividade' : 'Nova atividade'}
                </h2>
              </div>
              <div className="p-6 space-y-4">
                {error && (
                  <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Título
                  </label>
                  <input
                    type="text"
                    value={form.titulo}
                    onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Ex: Ligar para cliente"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tipo
                  </label>
                  <select
                    value={form.tipo}
                    onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value as Atividade['tipo'] }))}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    {Object.entries(TIPO_LABEL).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Data e hora
                  </label>
                  <input
                    type="datetime-local"
                    value={form.data}
                    onChange={(e) => setForm((f) => ({ ...f, data: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Duração (minutos)
                  </label>
                  <select
                    value={form.duracao_minutos}
                    onChange={(e) => setForm((f) => ({ ...f, duracao_minutos: Number(e.target.value) }))}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value={15}>15 min</option>
                    <option value={30}>30 min</option>
                    <option value={45}>45 min</option>
                    <option value={60}>1 hora</option>
                    <option value={90}>1h 30min</option>
                    <option value={120}>2 horas</option>
                    <option value={180}>3 horas</option>
                    <option value={240}>4 horas</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Observações
                  </label>
                  <textarea
                    value={form.observacoes}
                    onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))}
                    rows={2}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Opcional"
                  />
                </div>
                {modalAtividade && (
                  <div className="flex gap-2 flex-wrap">
                    <button
                      type="button"
                      onClick={handleToggleConcluido}
                      disabled={saving}
                      className="px-3 py-2 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                    >
                      {modalAtividade.concluido ? 'Desmarcar concluída' : 'Marcar concluída'}
                    </button>
                    <button
                      type="button"
                      onClick={handleDelete}
                      disabled={saving}
                      className="px-3 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
                    >
                      Excluir
                    </button>
                  </div>
                )}
              </div>
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 rounded-lg bg-[#0176d3] hover:bg-[#0159a8] text-white font-medium disabled:opacity-50"
                >
                  {saving ? 'Salvando...' : 'Salvar'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
