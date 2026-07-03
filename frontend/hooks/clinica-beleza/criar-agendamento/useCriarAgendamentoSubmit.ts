import { useCallback } from "react";
import {
  resolveDefaultLocalId,
  resolveDefaultNomeAgendaId,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import { calcularDuracaoAgendamento } from "@/lib/clinica-beleza-duracao";
import { isBrowserOffline, isFetchNetworkError } from "@/lib/clinica-beleza-offline";
import { workHoursRejectionMessage } from "@/lib/clinica-beleza-work-hours";
import { buildAppointmentDate, buildCriarAgendamentoPayload } from "./criar-agendamento-builders";
import {
  buildOfflineAgendaEvent,
  enqueueAgendamentoOffline,
  enqueueConsultaOffline,
} from "./criar-agendamento-offline";
import { createQuickPatient, submitAgendamentoOnline, submitConsultaOnline } from "./criar-agendamento-submit-api";
import type { CriarAgendamentoSubmitContext, CriarAgendamentoSubmitOptions } from "./criar-agendamento-submit-types";
import {
  CRIAR_AGENDAMENTO_DEFAULT_TIME,
  CRIAR_AGENDAMENTO_OFFLINE_SAVE_ERROR,
  extractCriarAgendamentoSubmitError,
  mapSubmitValidationError,
} from "./criar-agendamento-submit-utils";

export function useCriarAgendamentoSubmit(
  options: CriarAgendamentoSubmitOptions,
  ctx: CriarAgendamentoSubmitContext,
) {
  const {
    selectedDate,
    professionals,
    patients,
    procedures,
    nomesAgenda,
    locaisAtendimento,
    onClose,
    onSuccess,
    onConsultaCreated,
    onOfflineEventCreated,
  } = options;

  const {
    isConsulta,
    validateBase,
    resetForm,
    patientId,
    professionalId,
    convenioId,
    selectedProcedures,
    resumo,
    dateInput,
    time,
    notes,
    nomeAgendaId,
    localAtendimentoId,
    retornoProcedureId,
    horariosProfissional,
    setCreateLoading,
    setCreateError,
    setTime,
    setDateInput,
    setNotes,
    setNomeAgendaId,
    setLocalAtendimentoId,
  } = ctx;

  const resetAndClose = useCallback(() => {
    resetForm();
    setTime(CRIAR_AGENDAMENTO_DEFAULT_TIME);
    setDateInput("");
    setNotes("");
    setNomeAgendaId("");
    setLocalAtendimentoId("");
    setCreateError("");
    setCreateLoading(false);
    onClose();
  }, [
    onClose,
    resetForm,
    setCreateError,
    setCreateLoading,
    setDateInput,
    setLocalAtendimentoId,
    setNomeAgendaId,
    setNotes,
    setTime,
  ]);

  const handleCreatePatient = useCallback(
    async (data: { nome: string; telefone: string; cpf: string }) => createQuickPatient(data),
    [],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateBase();
    if (validationError) {
      setCreateError(mapSubmitValidationError(validationError));
      return;
    }
    const agendaId = nomeAgendaId || resolveDefaultNomeAgendaId(nomesAgenda);
    if (!agendaId) {
      setCreateError("Selecione o nome da agenda.");
      return;
    }
    const localId = localAtendimentoId || resolveDefaultLocalId(locaisAtendimento);
    const date = buildAppointmentDate(dateInput, time, selectedDate);
    if (!date) {
      setCreateError("Data não definida.");
      return;
    }

    const localSel = localId ? locaisAtendimento.find((l) => l.id === localId) : undefined;
    const profSel = professionalId ? professionals.find((p) => p.id === professionalId) : undefined;
    const duracaoChecagem = calcularDuracaoAgendamento(resumo.duracao, profSel, localSel);

    const horarioMsg = workHoursRejectionMessage(date, duracaoChecagem, horariosProfissional);
    if (horarioMsg) {
      setCreateError(horarioMsg);
      return;
    }

    setCreateLoading(true);
    setCreateError("");

    const basePayload = buildCriarAgendamentoPayload({
      patientId,
      agendaId: Number(agendaId),
      notes,
      date,
      professionalId,
      localId,
      convenioId,
      selectedProcedures,
      retornoProcedureId,
    });

    const finishConsultaOffline = async () => {
      await enqueueConsultaOffline(basePayload);
      resetAndClose();
      onSuccess();
    };

    const finishAgendamentoOffline = async () => {
      await enqueueAgendamentoOffline(basePayload);
      if (onOfflineEventCreated) {
        onOfflineEventCreated(
          buildOfflineAgendaEvent({
            date,
            duracaoMinutos: duracaoChecagem,
            patientId,
            professionalId,
            selectedProcedures,
            agendaId: Number(agendaId),
            notes,
            patients,
            professionals,
            procedures,
            nomesAgenda,
            resumoValor: resumo.valor,
            resumoDuracao: resumo.duracao,
          }),
        );
      }
      resetAndClose();
    };

    try {
      if (isBrowserOffline()) {
        if (isConsulta) {
          await finishConsultaOffline();
          return;
        }
        await finishAgendamentoOffline();
        return;
      }

      if (isConsulta) {
        const consulta = await submitConsultaOnline(basePayload);
        resetAndClose();
        onSuccess();
        if (consulta?.id != null) onConsultaCreated?.(Number(consulta.id));
        return;
      }

      await submitAgendamentoOnline(basePayload);
      resetAndClose();
      onSuccess();
    } catch (err: unknown) {
      const msg = extractCriarAgendamentoSubmitError(err, isConsulta);

      if (isFetchNetworkError(msg)) {
        try {
          if (isConsulta) {
            await finishConsultaOffline();
            return;
          }
          await finishAgendamentoOffline();
          return;
        } catch {
          setCreateError(CRIAR_AGENDAMENTO_OFFLINE_SAVE_ERROR);
          return;
        }
      }

      setCreateError(msg);
    } finally {
      setCreateLoading(false);
    }
  };

  return { resetAndClose, handleSubmit, handleCreatePatient };
}
