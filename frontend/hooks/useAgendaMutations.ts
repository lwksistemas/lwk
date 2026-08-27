"use client";

import { useCallback, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { clinicaBelezaQueryKeys } from "@/lib/clinica-beleza-cadastros-api";
import { arredondarDuracaoAgendaMin } from "@/lib/clinica-beleza-datetime";
import type { AgendaConflictPayload, AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { ConflitoAgendaData } from "@/components/clinica-beleza/ModalConflitoAgenda";
import { mergeRawAgendaEvent, versaoAgenda } from "@/hooks/clinica-beleza/agenda-data/agenda-event-mappers";
import { useToast } from "@/components/ui/Toast";
import { logger } from "@/lib/logger";
import type { EventDropArg } from "@fullcalendar/core";
import type { EventResizeDoneArg } from "@fullcalendar/interaction";

type ConflictState = (ConflitoAgendaData & {
  appointmentId: number;
  payloadForResolve: AgendaConflictPayload;
}) | null;

interface UseAgendaMutationsOptions {
  onReload: () => void;
  selectedProfessional?: string;
  selectedEvent: AgendaEventData | null;
  setSelectedEvent: React.Dispatch<React.SetStateAction<AgendaEventData | null>>;
  setShowModal: (open: boolean) => void;
  isMutatingRef?: React.MutableRefObject<boolean>;
}

export function useAgendaMutations({
  onReload,
  selectedProfessional = "",
  selectedEvent,
  setSelectedEvent,
  setShowModal,
  isMutatingRef: externalMutatingRef,
}: UseAgendaMutationsOptions) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [reenviandoMensagem, setReenviandoMensagem] = useState(false);
  const [salvandoDetalhe, setSalvandoDetalhe] = useState(false);
  const [conflictData, setConflictData] = useState<ConflictState>(null);
  const [conflictResolving, setConflictResolving] = useState(false);
  const internalMutatingRef = useRef(false);
  const isMutatingRef = externalMutatingRef ?? internalMutatingRef;

  const atualizarBloqueioHorario = useCallback(async (info: { event: { extendedProps?: Record<string, unknown>; start: Date | null; end: Date | null; title?: string }; revert: () => void }) => {
    const bloqueioId = info.event.extendedProps?.bloqueioId;
    const start = info.event.start;
    const end = info.event.end;
    if (!bloqueioId || !start || !end) {
      info.revert();
      return;
    }
    if (end <= start) {
      toast.error("O fim do bloqueio deve ser depois do início.");
      info.revert();
      return;
    }
    const motivoRaw = info.event.extendedProps?.motivo || info.event.title || "Bloqueio";
    const motivo = String(motivoRaw).replace(/^🚫\s*/, "").trim() || "Bloqueio";
    const body: Record<string, unknown> = {
      data_inicio: start.toISOString(),
      data_fim: end.toISOString(),
      motivo,
    };
    const prof = info.event.extendedProps?.professional;
    if (prof != null && prof !== "") body.professional = prof;

    try {
      const res = await clinicaBelezaFetch(`/bloqueios/${bloqueioId}/`, {
        method: "PUT",
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.error || data.detail || (Array.isArray(data.data_fim) ? data.data_fim[0] : null) || "Erro ao atualizar bloqueio.";
        toast.error(typeof msg === "string" ? msg : "Erro ao atualizar bloqueio.");
        info.revert();
        return;
      }
      onReload();
    } catch (error) {
      logger.warn("Erro ao atualizar bloqueio:", error);
      toast.error("Erro ao atualizar bloqueio. Tente novamente.");
      info.revert();
    }
  }, [onReload, toast]);

  const patchAgendamento = useCallback(async (
    id: number | string,
    body: Record<string, unknown>,
    revert?: () => void,
  ): Promise<Record<string, unknown> | false> => {
    const res = await clinicaBelezaFetch(`/agenda/${id}/update/`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 409 && data.conflict) {
      revert?.();
      setConflictData({
        server: data.server,
        local: data.local,
        resolution_hint: data.resolution_hint,
        appointmentId: Number(id),
        payloadForResolve: body as AgendaConflictPayload,
      });
      return false;
    }
    if (!res.ok) {
      revert?.();
      throw new Error(data.error || "Erro ao atualizar agendamento");
    }
    return data;
  }, []);

  const gravarEventoSalvo = useCallback(
    (info: { event: { setExtendedProp: (k: string, v: unknown) => void } }, result: Record<string, unknown>) => {
      const version = versaoAgenda(result.version);
      if (version != null) info.event.setExtendedProp("version", version);
      if (result.updated_at) info.event.setExtendedProp("updated_at", result.updated_at);
      queryClient.setQueryData(
        clinicaBelezaQueryKeys.agendaEvents(selectedProfessional),
        (old) => mergeRawAgendaEvent(old, result),
      );
    },
    [queryClient, selectedProfessional],
  );

  const moverEvento = useCallback(async (info: EventDropArg) => {
    if (!info.event.start) {
      info.revert();
      return;
    }
    if (info.event.extendedProps?.isIntervalo) return;
    if (isMutatingRef.current) {
      info.revert();
      toast.warning("Aguarde o agendamento salvar antes de mover de novo.");
      return;
    }
    if (info.event.extendedProps?.isBloqueio) {
      await atualizarBloqueioHorario(info as Parameters<typeof atualizarBloqueioHorario>[0]);
      return;
    }
    const startIso = info.event.start.toISOString();
    const endIso = info.event.end?.toISOString();
    const version = versaoAgenda(info.event.extendedProps?.version);
    const updatedAt = info.event.extendedProps?.updated_at;
    const body: Record<string, unknown> = { date: startIso };
    if (version != null) body.version = version;
    if (updatedAt) body.updated_at = updatedAt;
    const cacheKey = clinicaBelezaQueryKeys.agendaEvents(selectedProfessional);
    const previous = queryClient.getQueryData(cacheKey);
    queryClient.setQueryData(cacheKey, (old) =>
      mergeRawAgendaEvent(old, { id: info.event.id, start: startIso, ...(endIso ? { end: endIso } : {}) }),
    );
    isMutatingRef.current = true;
    try {
      const result = await patchAgendamento(info.event.id, body, info.revert);
      if (result) gravarEventoSalvo(info, result);
      else queryClient.setQueryData(cacheKey, previous);
    } catch (error) {
      queryClient.setQueryData(cacheKey, previous);
      logger.warn("Erro ao mover evento:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao mover evento. Tente novamente.");
      info.revert();
    } finally {
      setTimeout(() => { isMutatingRef.current = false; }, 400);
    }
  }, [atualizarBloqueioHorario, gravarEventoSalvo, patchAgendamento, queryClient, selectedProfessional, toast]);

  const moverAgendamentoGrade = useCallback(async (
    evt: AgendaEventData,
    start: Date,
    professionalId: number,
  ) => {
    if (evt.extendedProps?.isIntervalo || evt.extendedProps?.isBloqueio) return;
    const dbId = evt.extendedProps?.dbId ?? evt.id;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      toast.warning("Agendamento offline. Aguarde a sincronização para mover.");
      return;
    }
    if (isMutatingRef.current) {
      toast.warning("Aguarde o agendamento salvar antes de mover de novo.");
      return;
    }
    const startIso = start.toISOString();
    const duracao = Number(evt.extendedProps?.duracao_minutos || evt.extendedProps?.procedure_duration || 30);
    const endIso = new Date(start.getTime() + Math.max(5, duracao) * 60_000).toISOString();
    const version = versaoAgenda(evt.extendedProps?.version);
    const updatedAt = evt.extendedProps?.updated_at;
    const body: Record<string, unknown> = { date: startIso };
    if (version != null) body.version = version;
    if (updatedAt) body.updated_at = updatedAt;
    const atual = evt.extendedProps?.professional;
    if (professionalId && Number(atual) !== professionalId) {
      body.professional = professionalId;
    }
    const cacheKey = clinicaBelezaQueryKeys.agendaEvents(selectedProfessional);
    const previous = queryClient.getQueryData(cacheKey);
    queryClient.setQueryData(cacheKey, (old) =>
      mergeRawAgendaEvent(old, {
        id: evt.id,
        start: startIso,
        end: endIso,
        professional: professionalId,
        professional_id: professionalId,
      }),
    );
    isMutatingRef.current = true;
    try {
      const result = await patchAgendamento(dbId, body);
      if (result) {
        queryClient.setQueryData(cacheKey, (old) => mergeRawAgendaEvent(old, result));
      } else {
        queryClient.setQueryData(cacheKey, previous);
      }
    } catch (error) {
      queryClient.setQueryData(cacheKey, previous);
      logger.warn("Erro ao mover evento da grade:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao mover evento. Tente novamente.");
    } finally {
      setTimeout(() => { isMutatingRef.current = false; }, 400);
    }
  }, [patchAgendamento, queryClient, selectedProfessional, toast]);

  const redimensionarAgendamentoGrade = useCallback(async (
    evt: AgendaEventData,
    duracaoMinutos: number,
  ) => {
    if (evt.extendedProps?.isIntervalo || evt.extendedProps?.isBloqueio) return;
    if (evt.extendedProps?.status === "CANCELLED") {
      toast.warning("Não é possível alterar a duração de um agendamento cancelado.");
      return;
    }
    const dbId = evt.extendedProps?.dbId ?? evt.id;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      toast.warning("Agendamento offline. Aguarde a sincronização para ajustar a duração.");
      return;
    }
    if (isMutatingRef.current) {
      toast.warning("Aguarde o agendamento salvar antes de ajustar de novo.");
      return;
    }
    const duracao = arredondarDuracaoAgendaMin(duracaoMinutos);
    const atual = Number(evt.extendedProps?.duracao_minutos || evt.extendedProps?.procedure_duration || 0);
    if (duracao === atual) return;
    const version = versaoAgenda(evt.extendedProps?.version);
    const updatedAt = evt.extendedProps?.updated_at;
    const body: Record<string, unknown> = { duracao_minutos: duracao };
    if (version != null) body.version = version;
    if (updatedAt) body.updated_at = updatedAt;
    const start = evt.start;
    const endIso = start
      ? new Date(new Date(start).getTime() + duracao * 60_000).toISOString()
      : undefined;
    const cacheKey = clinicaBelezaQueryKeys.agendaEvents(selectedProfessional);
    const previous = queryClient.getQueryData(cacheKey);
    queryClient.setQueryData(cacheKey, (old) =>
      mergeRawAgendaEvent(old, {
        id: evt.id,
        duracao_minutos: duracao,
        ...(endIso ? { end: endIso } : {}),
      }),
    );
    isMutatingRef.current = true;
    try {
      const result = await patchAgendamento(dbId, body);
      if (result) {
        queryClient.setQueryData(cacheKey, (old) => mergeRawAgendaEvent(old, result));
      } else {
        queryClient.setQueryData(cacheKey, previous);
      }
    } catch (error) {
      queryClient.setQueryData(cacheKey, previous);
      logger.warn("Erro ao redimensionar evento da grade:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao ajustar duração. Tente novamente.");
    } finally {
      setTimeout(() => { isMutatingRef.current = false; }, 400);
    }
  }, [patchAgendamento, queryClient, selectedProfessional, toast]);

  const redimensionarEvento = useCallback(async (info: EventResizeDoneArg) => {
    if (info.event.extendedProps?.isIntervalo) {
      info.revert();
      return;
    }
    if (info.event.extendedProps?.isBloqueio) {
      await atualizarBloqueioHorario(info as Parameters<typeof atualizarBloqueioHorario>[0]);
      return;
    }
    if (info.event.extendedProps?.status === "CANCELLED") {
      info.revert();
      toast.warning("Não é possível alterar a duração de um agendamento cancelado.");
      return;
    }
    const dbId = info.event.extendedProps?.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      info.revert();
      toast.warning("Agendamento offline. Aguarde a sincronização para ajustar a duração.");
      return;
    }
    const start = info.event.start;
    const end = info.event.end;
    if (!start || !end) {
      info.revert();
      return;
    }
    const duracaoMinutos = arredondarDuracaoAgendaMin(
      Math.round((end.getTime() - start.getTime()) / 60000),
    );
    const version = versaoAgenda(info.event.extendedProps?.version);
    const updatedAt = info.event.extendedProps?.updated_at;
    const body: Record<string, unknown> = { duracao_minutos: duracaoMinutos };
    if (version != null) body.version = version;
    if (updatedAt) body.updated_at = updatedAt;
    isMutatingRef.current = true;
    try {
      const result = await patchAgendamento(info.event.id, body, info.revert);
      if (result) gravarEventoSalvo(info, result);
    } catch (error) {
      logger.warn("Erro ao redimensionar evento:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao ajustar duração. Tente novamente.");
      info.revert();
    } finally {
      setTimeout(() => { isMutatingRef.current = false; }, 400);
    }
  }, [atualizarBloqueioHorario, gravarEventoSalvo, patchAgendamento, toast]);

  const deletarEvento = useCallback(async () => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      toast.warning("Agendamento criado offline. Aguarde a sincronização para excluir.");
      return;
    }
    if (!confirm("Deseja realmente deletar este agendamento?")) return;
    try {
      const res = await clinicaBelezaFetch(`/agenda/${dbId}/delete/`, { method: "DELETE" });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.error || "Erro ao deletar agendamento");
      }
      setShowModal(false);
      setSelectedEvent(null);
      onReload();
    } catch (error) {
      logger.warn("Erro ao deletar evento:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao deletar agendamento.");
    }
  }, [onReload, selectedEvent, setSelectedEvent, setShowModal, toast]);

  const atualizarDetalheAgendamento = useCallback(async (payload: {
    date?: string;
    professional?: number;
    procedures_ids?: number[];
  }) => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId ?? selectedEvent.id;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      toast.warning("Agendamento criado offline. Aguarde a sincronização para editar.");
      return;
    }
    const body: Record<string, unknown> = { ...payload };
    if (selectedEvent.extendedProps.version != null) body.version = selectedEvent.extendedProps.version;
    if (selectedEvent.extendedProps.updated_at) body.updated_at = selectedEvent.extendedProps.updated_at;
    setSalvandoDetalhe(true);
    try {
      const result = await patchAgendamento(dbId, body);
      if (!result) return;
      queryClient.setQueryData(
        clinicaBelezaQueryKeys.agendaEvents(selectedProfessional),
        (old) => mergeRawAgendaEvent(old, result),
      );
      if (result.confirmacao_reiniciada) {
        toast.success("Agendamento atualizado. O link anterior foi invalidado e um novo será enviado no WhatsApp.");
      } else {
        toast.success("Agendamento atualizado.");
      }
      onReload();
    } catch (error) {
      logger.warn("Erro ao editar agendamento:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao salvar agendamento.");
    } finally {
      setSalvandoDetalhe(false);
    }
  }, [onReload, patchAgendamento, queryClient, selectedEvent, selectedProfessional, toast]);

  const atualizarStatusAgendamento = useCallback(async (novoStatus: string) => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      toast.warning("Agendamento criado offline. Aguarde a sincronização para alterar status.");
      return;
    }
    setUpdatingStatus(true);
    try {
      const body: Record<string, unknown> = { status: novoStatus };
      if (selectedEvent.extendedProps.version != null) body.version = selectedEvent.extendedProps.version;
      if (selectedEvent.extendedProps.updated_at) body.updated_at = selectedEvent.extendedProps.updated_at;
      const res = await clinicaBelezaFetch(`/agenda/${dbId}/update/`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 409 && data.conflict) {
        setConflictData({
          server: data.server,
          local: data.local,
          resolution_hint: data.resolution_hint,
          appointmentId: Number(dbId),
          payloadForResolve: { status: novoStatus },
        });
        return;
      }
      if (!res.ok) throw new Error(data.error || "Erro ao atualizar status");
      setSelectedEvent((prev) =>
        prev
          ? {
              ...prev,
              extendedProps: {
                ...prev.extendedProps,
                status: novoStatus,
                ...(data.consulta_id != null ? { consulta_id: Number(data.consulta_id) } : {}),
              },
            }
          : null,
      );
      if (data.consulta_error) toast.error(data.consulta_error);
      onReload();
    } catch (error) {
      logger.warn("Erro ao atualizar status:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao atualizar status.");
    } finally {
      setUpdatingStatus(false);
    }
  }, [onReload, selectedEvent, setSelectedEvent, toast]);

  const reenviarMensagemWhatsApp = useCallback(async () => {
    if (!selectedEvent) return;
    const dbId = selectedEvent.extendedProps.dbId;
    if (typeof dbId === "string" && dbId.startsWith("offline-")) {
      toast.warning("Agendamento offline. Sincronize antes de reenviar mensagem.");
      return;
    }
    setReenviandoMensagem(true);
    try {
      const res = await clinicaBelezaFetch(`/agenda/${dbId}/reenviar-mensagem/`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (data.sent) {
        toast.success("Mensagem reenviada com sucesso para o paciente.");
      } else {
        toast.warning(data.message || "Não foi possível reenviar a mensagem.");
      }
    } catch (e) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      logger.warn("Erro ao reenviar mensagem:", e);
      toast.error("Erro ao reenviar mensagem. Tente novamente.");
    } finally {
      setReenviandoMensagem(false);
    }
  }, [selectedEvent, toast]);

  const handleConflitoUseServer = useCallback(() => {
    setConflictData(null);
    setShowModal(false);
    onReload();
  }, [onReload, setShowModal]);

  const closeConflictModal = useCallback(() => setConflictData(null), []);

  const handleConflitoUseLocal = useCallback(async () => {
    if (!conflictData) return;
    setConflictResolving(true);
    try {
      const res = await clinicaBelezaFetch(`/agenda/${conflictData.appointmentId}/update/`, {
        method: "PATCH",
        body: JSON.stringify({ ...conflictData.payloadForResolve, resolve_use_local: true }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.error || "Erro ao aplicar sua versão");
      }
      setConflictData(null);
      setShowModal(false);
      onReload();
    } catch (e) {
      logger.warn("Erro ao resolver conflito:", e);
      toast.error(e instanceof Error ? e.message : "Erro ao aplicar sua versão.");
    } finally {
      setConflictResolving(false);
    }
  }, [conflictData, onReload, setShowModal, toast]);

  return {
    updatingStatus,
    reenviandoMensagem,
    salvandoDetalhe,
    conflictData,
    conflictResolving,
    moverEvento,
    moverAgendamentoGrade,
    redimensionarEvento,
    redimensionarAgendamentoGrade,
    deletarEvento,
    atualizarStatusAgendamento,
    atualizarDetalheAgendamento,
    reenviarMensagemWhatsApp,
    handleConflitoUseServer,
    handleConflitoUseLocal,
    closeConflictModal,
  };
}
