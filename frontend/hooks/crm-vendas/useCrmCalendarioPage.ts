'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail, normalizeListResponse } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import { formatTelefone, telefoneInternacionalBr } from '@/lib/format-br';
import { obterFeriadosBrasil } from '@/lib/feriados-brasil';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import {
  API_CRM_CALENDARIO as API_CRM,
  API_GOOGLE_AUTH,
  API_GOOGLE_DISCONNECT,
  API_GOOGLE_STATUS,
  API_GOOGLE_SYNC,
  MOBILE_BREAKPOINT,
  SYNC_RESULT_DISPLAY_MS,
  atividadeToEvent,
  emptyAtividadeForm,
  localDateTimeInputFromDate,
  toISO,
  type Atividade,
  type AtividadeFormState,
  type CalendarEvent,
} from '@/lib/crm-calendario';

export function useCrmCalendarioPage() {
  const toast = useToast();
  const searchParams = useSearchParams();
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
  const [form, setForm] = useState({
  titulo: '',
  tipo: 'task' as Atividade['tipo'],
  data: '',
  duracao_minutos: 60,
  observacoes: '',
  conta: null as number | null,
  lead: null as number | null,
  lembrete_whatsapp: false,
  lembrete_whatsapp_telefone: '',
  });
  const patchForm = useCallback((patch: Partial<typeof form>) => {
  setForm((prev) => ({ ...prev, ...patch }));
  }, []);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { whatsappAtivo } = useWhatsappEnvioFlags();
  const [googleStatus, setGoogleStatus] = useState<{ connected: boolean; email: string | null }>({ connected: false, email: null });
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleSyncResult, setGoogleSyncResult] = useState<{ pushed: number; pulled: number } | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const syncingRef = useRef(false);
  const [confirmAction, setConfirmAction] = useState<'delete_atividade' | 'disconnect_google' | null>(null);
  const [confirmando, setConfirmando] = useState(false);

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
      const list = normalizeListResponse(res.data);
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

  const handleSyncGoogle = useCallback(async (direction: 'push_only' | 'pull' | 'both' = 'both') => {
  if (syncingRef.current) return;
  syncingRef.current = true;
  setGoogleLoading(true);
  setGoogleSyncResult(null);
  setSyncError(null);
  try {
    const res = await apiClient.post<{ pushed: number; pulled: number }>(API_GOOGLE_SYNC, {
      direction,
    });
    setGoogleSyncResult({ pushed: res.data.pushed, pulled: res.data.pulled });
    if (range) await fetchAtividades(range.start, range.end);
    if (SYNC_RESULT_DISPLAY_MS > 0 && typeof window !== 'undefined') {
      window.setTimeout(() => setGoogleSyncResult(null), SYNC_RESULT_DISPLAY_MS);
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string }; status?: number } };
    let msg = err?.response?.data?.detail || 'Erro ao sincronizar com o Google Calendar.';
    if (msg.includes('Contexto de loja') || msg.includes('não identificado')) {
      msg += ' Atualize a página e tente novamente.';
    } else if (err?.response?.status === 502 || err?.response?.status === 503) {
      msg = 'Servidor temporariamente indisponível. Tente novamente em alguns segundos.';
    }
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

  const requestDisconnectGoogle = useCallback(() => {
    setConfirmAction('disconnect_google');
  }, []);

  const executeDisconnectGoogle = useCallback(async () => {
    setGoogleLoading(true);
    setSyncError(null);
    try {
      await apiClient.delete(API_GOOGLE_DISCONNECT);
      setGoogleStatus({ connected: false, email: null });
      setGoogleSyncResult(null);
      setConfirmAction(null);
    } finally {
      setGoogleLoading(false);
    }
  }, []);

  const handleDisconnectGoogle = requestDisconnectGoogle;

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

  const eventosComFeriados = useMemo(() => {
  const feriados = range ? obterFeriadosBrasil(range.start, range.end) : [];
  return [...events, ...feriados];
  }, [events, range]);

  const openNovaAtividade = useCallback(() => {
  const now = new Date();
  const start = new Date(now);
  start.setMinutes(Math.ceil(start.getMinutes() / 15) * 15);
  start.setSeconds(0, 0);
  // Converter para formato local (sem ajuste de timezone)
  const year = start.getFullYear();
  const month = String(start.getMonth() + 1).padStart(2, '0');
  const day = String(start.getDate()).padStart(2, '0');
  const hours = String(start.getHours()).padStart(2, '0');
  const minutes = String(start.getMinutes()).padStart(2, '0');
  const localDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
  
  setModalAtividade(null);
  setForm({
    titulo: '',
    tipo: 'task',
    data: localDateTime,
    duracao_minutos: 60,
    observacoes: '',
    conta: null,
    lead: null,
    lembrete_whatsapp: whatsappAtivo,
    lembrete_whatsapp_telefone: '',
  });
  setModalOpen(true);
  setError(null);
  }, [whatsappAtivo]);

  const handleDateClick = useCallback((arg: { date: Date; dateStr: string; allDay: boolean }) => {
  // Função para criar tarefa ao clicar em um dia/horário vazio
  // Funciona tanto no desktop quanto no mobile
  const clickedDate = arg.date;
  
  // Se for all-day, usar 9:00 como padrão
  if (arg.allDay) {
    clickedDate.setHours(9, 0, 0, 0);
  }
  
  // Converter para formato local
  const year = clickedDate.getFullYear();
  const month = String(clickedDate.getMonth() + 1).padStart(2, '0');
  const day = String(clickedDate.getDate()).padStart(2, '0');
  const hours = String(clickedDate.getHours()).padStart(2, '0');
  const minutes = String(clickedDate.getMinutes()).padStart(2, '0');
  const localDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
  
  setModalAtividade(null);
  setForm({
    titulo: '',
    tipo: 'task',
    data: localDateTime,
    duracao_minutos: 60,
    observacoes: '',
    conta: null,
    lead: null,
    lembrete_whatsapp: whatsappAtivo,
    lembrete_whatsapp_telefone: '',
  });
  setModalOpen(true);
  setError(null);
  }, [whatsappAtivo]);

  const handleSelect = useCallback((arg: { start: Date; end: Date }) => {
  // Corrigir timezone: FullCalendar retorna em UTC, precisamos converter para local
  const localDate = new Date(arg.start.getTime() - arg.start.getTimezoneOffset() * 60000);
  setModalAtividade(null);
  setForm({
    titulo: '',
    tipo: 'task',
    data: localDate.toISOString().slice(0, 16),
    duracao_minutos: 60,
    observacoes: '',
    conta: null,
    lead: null,
    lembrete_whatsapp: whatsappAtivo,
    lembrete_whatsapp_telefone: '',
  });
  setModalOpen(true);
  setError(null);
  }, [whatsappAtivo]);

  const handleEventClick = useCallback((arg: { event: { extendedProps?: { atividade?: Atividade; tipo?: string } }; jsEvent: MouseEvent }) => {
  arg.jsEvent.preventDefault();
  if (arg.event.extendedProps?.tipo === 'feriado') return;
  const a = arg.event.extendedProps?.atividade;
  if (!a) return;
  
  // Converter data UTC para local
  const dataUTC = new Date(a.data);
  const year = dataUTC.getFullYear();
  const month = String(dataUTC.getMonth() + 1).padStart(2, '0');
  const day = String(dataUTC.getDate()).padStart(2, '0');
  const hours = String(dataUTC.getHours()).padStart(2, '0');
  const minutes = String(dataUTC.getMinutes()).padStart(2, '0');
  const localDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
  
  setModalAtividade(a);
  setForm({
    titulo: a.titulo,
    tipo: a.tipo,
    data: localDateTime,
    duracao_minutos: a.duracao_minutos ?? 60,
    observacoes: a.observacoes || '',
    conta: (a as any).conta ?? null,
    lead: (a as any).lead ?? null,
    lembrete_whatsapp: a.lembrete_whatsapp ?? false,
    lembrete_whatsapp_telefone: a.lembrete_whatsapp_telefone
      ? formatTelefone(a.lembrete_whatsapp_telefone)
      : '',
  });
  setModalOpen(true);
  setError(null);
  }, []);

  const handleCloseModal = useCallback(() => {
  setModalOpen(false);
  setModalAtividade(null);
  setError(null);
  }, []);

  const buildAtividadePayload = useCallback(() => ({
  titulo: form.titulo.trim(),
  tipo: form.tipo,
  data: new Date(form.data).toISOString(),
  duracao_minutos: form.duracao_minutos,
  observacoes: form.observacoes.trim(),
  conta: form.conta || null,
  lead: form.lead || null,
  lembrete_whatsapp: form.lembrete_whatsapp,
  lembrete_whatsapp_telefone: form.lembrete_whatsapp
    ? telefoneInternacionalBr(form.lembrete_whatsapp_telefone)
    : '',
  }), [form]);

  const persistAtividade = useCallback(async (): Promise<number> => {
  const payload = buildAtividadePayload();
  if (modalAtividade) {
    await apiClient.patch(`${API_CRM}/atividades/${modalAtividade.id}/`, payload);
    return modalAtividade.id;
  }
  const res = await apiClient.post<{ id: number }>(`${API_CRM}/atividades/`, payload);
  return res.data.id;
  }, [buildAtividadePayload, modalAtividade]);

  const afterSaveSuccess = useCallback(async () => {
  if (range) {
    await fetchAtividades(range.start, range.end);
  }
  handleCloseModal();
  if (googleStatus.connected && !syncingRef.current) {
    setTimeout(() => {
      handleSyncGoogle('push_only').catch(() => {});
    }, 100);
  }
  }, [range, fetchAtividades, handleCloseModal, googleStatus.connected, handleSyncGoogle]);

  const handleSave = useCallback(async () => {
  if (!form.titulo.trim()) {
    setError('Preencha o título.');
    return;
  }
  if (form.lembrete_whatsapp && form.lembrete_whatsapp_telefone.replace(/\D/g, '').length < 10) {
    setError('Informe um WhatsApp válido para os lembretes automáticos.');
    return;
  }
  setSaving(true);
  setError(null);
  try {
    await persistAtividade();
    await afterSaveSuccess();
  } catch (e: unknown) {
    setError(getCrmApiErrorDetail(e, 'Erro ao salvar.'));
  } finally {
    setSaving(false);
  }
  }, [form.titulo, form.lembrete_whatsapp, form.lembrete_whatsapp_telefone, persistAtividade, afterSaveSuccess]);

  const handleSaveAndWhatsapp = useCallback(async (telefone: string) => {
  if (!form.titulo.trim()) {
    setError('Preencha o título.');
    return;
  }
  setSaving(true);
  setError(null);
  try {
    const id = await persistAtividade();
    const res = await apiClient.post<{ message?: string }>(
      `${API_CRM}/atividades/${id}/enviar-whatsapp/`,
      { telefone },
    );
    await afterSaveSuccess();
    if (typeof window !== 'undefined') {
      toast.success(res.data.message || 'Atividade salva e lembrete enviado por WhatsApp.');
    }
  } catch (e: unknown) {
    setError(getCrmApiErrorDetail(e, 'Erro ao salvar ou enviar WhatsApp.'));
  } finally {
    setSaving(false);
  }
  }, [form.titulo, persistAtividade, afterSaveSuccess, toast]);

  const handleEnviarWhatsapp = useCallback(async (telefone: string) => {
  if (!modalAtividade) return;
  setSaving(true);
  setError(null);
  try {
    const res = await apiClient.post<{ message?: string }>(
      `${API_CRM}/atividades/${modalAtividade.id}/enviar-whatsapp/`,
      { telefone },
    );
    toast.success(res.data.message || 'Lembrete enviado por WhatsApp.');
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string; detail?: string } } };
    setError(err.response?.data?.error || err.response?.data?.detail || 'Erro ao enviar WhatsApp.');
  } finally {
    setSaving(false);
  }
  }, [modalAtividade, toast]);

  const handleToggleConcluido = useCallback(async () => {
  if (!modalAtividade) return;
  setSaving(true);
  setError(null);
  try {
    await apiClient.patch(`${API_CRM}/atividades/${modalAtividade.id}/`, {
      concluido: !modalAtividade.concluido,
    });
    
    // ESPERAR recarregar antes de fechar o modal
    if (range) {
      await fetchAtividades(range.start, range.end);
    }
    
    handleCloseModal();
    
    // Sincronizar com Google em background (não esperar)
    if (googleStatus.connected && !syncingRef.current) {
      setTimeout(() => {
        handleSyncGoogle('push_only').catch(() => {});
      }, 100);
    }
    
  } catch (e: any) {
    setError(e.response?.data?.detail || 'Erro ao atualizar.');
  } finally {
    setSaving(false);
  }
  }, [modalAtividade, range, fetchAtividades, handleCloseModal, googleStatus.connected, handleSyncGoogle]);

  const executeDeleteAtividade = useCallback(async () => {
    if (!modalAtividade) return;
    setSaving(true);
    setError(null);

    const atividadeId = modalAtividade.id;
    setEvents((prevEvents) => prevEvents.filter((e) => e.id !== String(atividadeId)));
    handleCloseModal();
    setConfirmAction(null);

    try {
      await apiClient.delete(`${API_CRM}/atividades/${atividadeId}/`);
      if (range) {
        fetchAtividades(range.start, range.end).catch(() => {});
      }
    } catch (e: unknown) {
      if (range) {
        await fetchAtividades(range.start, range.end);
      }
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || 'Erro ao excluir.');
      setModalOpen(true);
      setModalAtividade(modalAtividade);
    } finally {
      setSaving(false);
    }
  }, [modalAtividade, range, fetchAtividades, handleCloseModal]);

  const requestDeleteAtividade = useCallback(() => {
    if (!modalAtividade) return;
    setConfirmAction('delete_atividade');
  }, [modalAtividade]);

  const closeConfirm = useCallback(() => {
    if (confirmando || saving) return;
    setConfirmAction(null);
  }, [confirmando, saving]);

  const executeConfirm = useCallback(async () => {
    if (!confirmAction) return;
    setConfirmando(true);
    try {
      if (confirmAction === 'delete_atividade') {
        await executeDeleteAtividade();
      } else {
        await executeDisconnectGoogle();
      }
    } finally {
      setConfirmando(false);
    }
  }, [confirmAction, executeDeleteAtividade, executeDisconnectGoogle]);

  const handleDelete = requestDeleteAtividade;

  const handleEventDrop = useCallback(async (info: { event: any; revert: () => void }) => {
  const atividade = info.event.extendedProps?.atividade;
  if (!atividade) {
    info.revert();
    return;
  }
  try {
    const newStart = info.event.start;
    if (!newStart) {
      info.revert();
      return;
    }
    
    await apiClient.patch(`${API_CRM}/atividades/${atividade.id}/`, {
      data: newStart.toISOString(),
    });
    
    // Recarregar e sincronizar em PARALELO
    const reloadPromise = range ? fetchAtividades(range.start, range.end) : Promise.resolve();
    const syncPromise = (googleStatus.connected && !syncingRef.current) 
      ? new Promise<void>(resolve => setTimeout(() => {
          handleSyncGoogle('push_only').finally(() => resolve());
        }, 100))
      : Promise.resolve();
    
    // Não esperar - deixar rodar em background
    Promise.all([reloadPromise, syncPromise]).catch(() => {});
    
  } catch (e: any) {
    info.revert();
    toast.error(e.response?.data?.detail || 'Erro ao mover atividade.');
  }
  }, [range, fetchAtividades, googleStatus.connected, handleSyncGoogle, toast]);

  const handleEventResize = useCallback(async (info: { event: any; revert: () => void }) => {
  const atividade = info.event.extendedProps?.atividade;
  if (!atividade) {
    info.revert();
    return;
  }
  try {
    const newStart = info.event.start;
    const newEnd = info.event.end;
    if (!newStart || !newEnd) {
      info.revert();
      return;
    }
    const duracaoMs = newEnd.getTime() - newStart.getTime();
    const duracaoMinutos = Math.round(duracaoMs / 60000);
    
    await apiClient.patch(`${API_CRM}/atividades/${atividade.id}/`, {
      duracao_minutos: duracaoMinutos,
    });
    
    // Recarregar e sincronizar em PARALELO
    const reloadPromise = range ? fetchAtividades(range.start, range.end) : Promise.resolve();
    const syncPromise = (googleStatus.connected && !syncingRef.current) 
      ? new Promise<void>(resolve => setTimeout(() => {
          handleSyncGoogle('push_only').finally(() => resolve());
        }, 100))
      : Promise.resolve();
    
    // Não esperar - deixar rodar em background
    Promise.all([reloadPromise, syncPromise]).catch(() => {});
    
  } catch (e: any) {
    info.revert();
    toast.error(e.response?.data?.detail || 'Erro ao redimensionar atividade.');
  }
  }, [range, fetchAtividades, googleStatus.connected, handleSyncGoogle, toast]);
  return {
      searchParams,
      events,
      loading,
      plugins,
      locale,
      isMobile,
      modalOpen,
      modalAtividade,
      form,
      patchForm,
      saving,
      error,
      whatsappAtivo,
      googleStatus,
      googleLoading,
      googleSyncResult,
      syncError,
      eventosComFeriados,
      handleConnectGoogle,
      handleSyncGoogle,
      handleDisconnectGoogle,
      handleDatesSet,
      openNovaAtividade,
      handleDateClick,
      handleSelect,
      handleEventClick,
      handleCloseModal,
      handleSave,
      handleSaveAndWhatsapp,
      handleEnviarWhatsapp,
      handleToggleConcluido,
      handleDelete,
      handleEventDrop,
      handleEventResize,
      confirmAction,
      confirmando,
      closeConfirm,
      executeConfirm,
    };
}
