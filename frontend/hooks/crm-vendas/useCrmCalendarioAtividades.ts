'use client';

import { useCallback, useEffect, useMemo, useState, type MutableRefObject } from 'react';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail, normalizeListResponse } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import { formatTelefone, telefoneInternacionalBr } from '@/lib/format-br';
import { obterFeriadosBrasil } from '@/lib/feriados-brasil';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import {
  API_CRM_CALENDARIO as API_CRM,
  atividadeToEvent,
  emptyAtividadeForm,
  localDateTimeInputFromDate,
  toISO,
  type Atividade,
  type AtividadeFormState,
  type CalendarEvent,
} from '@/lib/crm-calendario';

export type CrmCalendarioGoogleHelpersRef = MutableRefObject<{
  googleConnected: boolean;
  syncingRef: MutableRefObject<boolean>;
  schedulePushToGoogle: () => void;
  handleSyncGoogle: (direction: 'push_only' | 'pull' | 'both') => Promise<void>;
}>;

export function useCrmCalendarioAtividades(googleRef: CrmCalendarioGoogleHelpersRef) {
  const toast = useToast();
  const { whatsappAtivo } = useWhatsappEnvioFlags();

  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<{ start: Date; end: Date } | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAtividade, setModalAtividade] = useState<Atividade | null>(null);
  const [form, setForm] = useState<AtividadeFormState>(emptyAtividadeForm(false));
  const patchForm = useCallback((patch: Partial<AtividadeFormState>) => {
    setForm((prev) => ({ ...prev, ...patch }));
  }, []);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAtividades = useCallback(async (start: Date, end: Date) => {
    const dataInicio = toISO(start);
    const dataFim = toISO(end);
    try {
      const res = await apiClient.get<Atividade[] | { results: Atividade[] }>(
        `${API_CRM}/atividades/`,
        { params: { data_inicio: dataInicio, data_fim: dataFim } },
      );
      const list = normalizeListResponse(res.data);
      setEvents(list.map(atividadeToEvent));
    } catch {
      setError('Erro ao carregar atividades.');
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, []);

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

  const openFormForNew = useCallback(
    (start: Date) => {
      setModalAtividade(null);
      setForm({
        ...emptyAtividadeForm(whatsappAtivo),
        data: localDateTimeInputFromDate(start),
      });
      setModalOpen(true);
      setError(null);
    },
    [whatsappAtivo],
  );

  const openNovaAtividade = useCallback(() => {
    const now = new Date();
    const start = new Date(now);
    start.setMinutes(Math.ceil(start.getMinutes() / 15) * 15);
    start.setSeconds(0, 0);
    openFormForNew(start);
  }, [openFormForNew]);

  const handleDateClick = useCallback(
    (arg: { date: Date; dateStr: string; allDay: boolean }) => {
      const clickedDate = new Date(arg.date);
      if (arg.allDay) {
        clickedDate.setHours(9, 0, 0, 0);
      }
      openFormForNew(clickedDate);
    },
    [openFormForNew],
  );

  const handleSelect = useCallback(
    (arg: { start: Date; end: Date }) => {
      const localDate = new Date(arg.start.getTime() - arg.start.getTimezoneOffset() * 60000);
      openFormForNew(localDate);
    },
    [openFormForNew],
  );

  const handleEventClick = useCallback(
    (arg: { event: { extendedProps?: { atividade?: Atividade; tipo?: string } }; jsEvent: MouseEvent }) => {
      arg.jsEvent.preventDefault();
      if (arg.event.extendedProps?.tipo === 'feriado') return;
      const a = arg.event.extendedProps?.atividade;
      if (!a) return;

      const dataUTC = new Date(a.data);
      setModalAtividade(a);
      setForm({
        titulo: a.titulo,
        tipo: a.tipo,
        data: localDateTimeInputFromDate(dataUTC),
        duracao_minutos: a.duracao_minutos ?? 60,
        observacoes: a.observacoes || '',
        conta: a.conta ?? null,
        lead: a.lead ?? null,
        lembrete_whatsapp: a.lembrete_whatsapp ?? false,
        lembrete_whatsapp_telefone: a.lembrete_whatsapp_telefone
          ? formatTelefone(a.lembrete_whatsapp_telefone)
          : '',
      });
      setModalOpen(true);
      setError(null);
    },
    [],
  );

  const handleCloseModal = useCallback(() => {
    setModalOpen(false);
    setModalAtividade(null);
    setError(null);
  }, []);

  const buildAtividadePayload = useCallback(
    () => ({
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
    }),
    [form],
  );

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
    googleRef.current.schedulePushToGoogle();
  }, [range, fetchAtividades, handleCloseModal, googleRef]);

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

  const handleSaveAndWhatsapp = useCallback(
    async (telefone: string) => {
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
    },
    [form.titulo, persistAtividade, afterSaveSuccess, toast],
  );

  const handleEnviarWhatsapp = useCallback(
    async (telefone: string) => {
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
    },
    [modalAtividade, toast],
  );

  const handleToggleConcluido = useCallback(async () => {
    if (!modalAtividade) return;
    setSaving(true);
    setError(null);
    try {
      await apiClient.patch(`${API_CRM}/atividades/${modalAtividade.id}/`, {
        concluido: !modalAtividade.concluido,
      });
      if (range) {
        await fetchAtividades(range.start, range.end);
      }
      handleCloseModal();
      googleRef.current.schedulePushToGoogle();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || 'Erro ao atualizar.');
    } finally {
      setSaving(false);
    }
  }, [modalAtividade, range, fetchAtividades, handleCloseModal, googleRef]);

  const executeDeleteAtividade = useCallback(async () => {
    if (!modalAtividade) return;
    setSaving(true);
    setError(null);

    const atividadeId = modalAtividade.id;
    const atividadeBackup = modalAtividade;
    setEvents((prevEvents) => prevEvents.filter((e) => e.id !== String(atividadeId)));
    handleCloseModal();

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
      setModalAtividade(atividadeBackup);
    } finally {
      setSaving(false);
    }
  }, [modalAtividade, range, fetchAtividades, handleCloseModal]);

  const requestDeleteAtividade = useCallback(() => {
    if (!modalAtividade) return false;
    return true;
  }, [modalAtividade]);

  const patchEventOnCalendar = useCallback(
    async (
      atividade: Atividade,
      payload: Record<string, unknown>,
      revert: () => void,
      errorMessage: string,
    ) => {
      try {
        await apiClient.patch(`${API_CRM}/atividades/${atividade.id}/`, payload);
        const reloadPromise = range ? fetchAtividades(range.start, range.end) : Promise.resolve();
        const helpers = googleRef.current;
        const syncPromise =
          helpers.googleConnected && !helpers.syncingRef.current
            ? new Promise<void>((resolve) => {
                setTimeout(() => {
                  helpers.handleSyncGoogle('push_only').finally(() => resolve());
                }, 100);
              })
            : Promise.resolve();
        Promise.all([reloadPromise, syncPromise]).catch(() => {});
      } catch (e: unknown) {
        revert();
        const err = e as { response?: { data?: { detail?: string } } };
        toast.error(err.response?.data?.detail || errorMessage);
      }
    },
    [range, fetchAtividades, googleRef, toast],
  );

  const handleEventDrop = useCallback(
    async (info: { event: { extendedProps?: { atividade?: Atividade }; start: Date | null }; revert: () => void }) => {
      const atividade = info.event.extendedProps?.atividade;
      if (!atividade || !info.event.start) {
        info.revert();
        return;
      }
      await patchEventOnCalendar(
        atividade,
        { data: info.event.start.toISOString() },
        info.revert,
        'Erro ao mover atividade.',
      );
    },
    [patchEventOnCalendar],
  );

  const handleEventResize = useCallback(
    async (info: {
      event: { extendedProps?: { atividade?: Atividade }; start: Date | null; end: Date | null };
      revert: () => void;
    }) => {
      const atividade = info.event.extendedProps?.atividade;
      if (!atividade || !info.event.start || !info.event.end) {
        info.revert();
        return;
      }
      const duracaoMs = info.event.end.getTime() - info.event.start.getTime();
      const duracaoMinutos = Math.round(duracaoMs / 60000);
      await patchEventOnCalendar(
        atividade,
        { duracao_minutos: duracaoMinutos },
        info.revert,
        'Erro ao redimensionar atividade.',
      );
    },
    [patchEventOnCalendar],
  );

  return {
    range,
    events,
    loading,
    modalOpen,
    modalAtividade,
    form,
    patchForm,
    saving,
    error,
    whatsappAtivo,
    eventosComFeriados,
    fetchAtividades,
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
    requestDeleteAtividade,
    executeDeleteAtividade,
    handleEventDrop,
    handleEventResize,
  };
}
