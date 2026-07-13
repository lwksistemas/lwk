"use client";

import { useCallback, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { arredondarDuracaoAgendaMin } from "@/lib/clinica-beleza-datetime";
import type { AgendaConflictPayload, AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { ConflitoAgendaData } from "@/components/clinica-beleza/ModalConflitoAgenda";
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
  selectedEvent: AgendaEventData | null;
  setSelectedEvent: React.Dispatch<React.SetStateAction<AgendaEventData | null>>;
  setShowModal: (open: boolean) => void;
}

export function useAgendaMutations({
  onReload,
  selectedEvent,
  setSelectedEvent,
  setShowModal,
}: UseAgendaMutationsOptions) {
  const toast = useToast();
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [reenviandoMensagem, setReenviandoMensagem] = useState(false);
  const [conflictData, setConflictData] = useState<ConflictState>(null);
  const [conflictResolving, setConflictResolving] = useState(false);

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
  ): Promise<boolean> => {
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
    return true;
  }, []);

  const moverEvento = useCallback(async (info: EventDropArg) => {
    if (!info.event.start) {
      info.revert();
      return;
    }
    if (info.event.extendedProps?.isIntervalo) return;
    if (info.event.extendedProps?.isBloqueio) {
      await atualizarBloqueioHorario(info as Parameters<typeof atualizarBloqueioHorario>[0]);
      return;
    }
    const { version, updated_at } = info.event.extendedProps || {};
    const body: Record<string, unknown> = { date: info.event.start.toISOString() };
    if (version != null) body.version = version;
    if (updated_at) body.updated_at = updated_at;
    try {
      const ok = await patchAgendamento(info.event.id, body, info.revert);
      if (ok) onReload();
    } catch (error) {
      logger.warn("Erro ao mover evento:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao mover evento. Tente novamente.");
      info.revert();
    }
  }, [atualizarBloqueioHorario, onReload, patchAgendamento, toast]);

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
    const { version, updated_at } = info.event.extendedProps || {};
    const body: Record<string, unknown> = { duracao_minutos: duracaoMinutos };
    if (version != null) body.version = version;
    if (updated_at) body.updated_at = updated_at;
    try {
      const ok = await patchAgendamento(info.event.id, body, info.revert);
      if (ok) onReload();
    } catch (error) {
      logger.warn("Erro ao redimensionar evento:", error);
      toast.error(error instanceof Error ? error.message : "Erro ao ajustar duração. Tente novamente.");
      info.revert();
    }
  }, [atualizarBloqueioHorario, onReload, patchAgendamento, toast]);

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
    conflictData,
    conflictResolving,
    moverEvento,
    redimensionarEvento,
    deletarEvento,
    atualizarStatusAgendamento,
    reenviarMensagemWhatsApp,
    handleConflitoUseServer,
    handleConflitoUseLocal,
    closeConflictModal,
  };
}
