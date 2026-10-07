import { useCallback } from "react";
import {
  resolveDefaultLocalId,
  resolveDefaultNomeAgendaId,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import { calcularDuracaoAgendamento } from "@/lib/clinica-beleza-duracao";
import { normalizarTipoAgendaNome } from "@/lib/clinica-beleza-tipo-agenda";
import { isBrowserOffline, isFetchNetworkError } from "@/lib/clinica-beleza-offline";
import { workHoursRejectionMessage } from "@/lib/clinica-beleza-work-hours";
import { buildAppointmentDate, buildCriarAgendamentoPayload, classificarSelecaoProtocolo } from "./criar-agendamento-builders";
import {
  buildOfflineAgendaEvent,
  enqueueAgendamentoOffline,
  enqueueConsultaOffline,
} from "./criar-agendamento-offline";
import {
  createQuickPatient,
  submitAgendamentoOnline,
  submitConsultaOnline,
  submitProtocoloPersonalizado,
} from "./criar-agendamento-submit-api";
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
    protocolos,
    protocolosCarregando,
    formaCobranca,
    protocoloClienteId,
    protocolosDaCliente,
    setProtocoloClienteId,
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
    setProtocoloClienteId("");
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
    setProtocoloClienteId,
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
    if (!professionalId) {
      setCreateError("Selecione o profissional.");
      return;
    }
    const agendaId = nomeAgendaId || resolveDefaultNomeAgendaId(nomesAgenda);
    if (!agendaId) {
      setCreateError("Selecione o tipo de agenda.");
      return;
    }
    const localId = localAtendimentoId || resolveDefaultLocalId(locaisAtendimento);
    const date = buildAppointmentDate(dateInput, time, selectedDate);
    if (!date) {
      setCreateError("Data não definida.");
      return;
    }

    const protocoloDaCliente = protocolosDaCliente.find((item) => item.id === protocoloClienteId) ?? null;
    const tipoAgenda = nomesAgenda.find((item) => item.id === Number(agendaId))?.nome || "";
    if (
      normalizarTipoAgendaNome(tipoAgenda) === "PROTOCOLO" &&
      !protocoloDaCliente &&
      selectedProcedures.length === 0
    ) {
      setCreateError(
        protocolosDaCliente.length > 0
          ? "Escolha o protocolo."
          : "Esta cliente não tem protocolo personalizado para agendar.",
      );
      return;
    }
    if (protocoloDaCliente && selectedProcedures.length > 0) {
      setCreateError("O protocolo personalizado é agendado sozinho. Tire os outros procedimentos.");
      return;
    }
    if (protocoloDaCliente) {
      if (!localId) {
        setCreateError("Selecione o local de atendimento.");
        return;
      }
      const duracaoProtocolo = protocoloDaCliente.tempo_minutos || resumo.duracao;
      const localSelProtocolo = locaisAtendimento.find((l) => l.id === localId);
      const profSelProtocolo = professionals.find((p) => p.id === professionalId);
      const duracaoChecagemProtocolo = calcularDuracaoAgendamento(
        duracaoProtocolo,
        profSelProtocolo,
        localSelProtocolo,
      );
      const horarioProtocolo = workHoursRejectionMessage(date, duracaoChecagemProtocolo, horariosProfissional);
      if (horarioProtocolo) {
        setCreateError(horarioProtocolo);
        return;
      }
      if (isBrowserOffline()) {
        setCreateError("O protocolo personalizado precisa de conexão para criar as sessões.");
        return;
      }
      setCreateLoading(true);
      setCreateError("");
      try {
        await submitProtocoloPersonalizado({
          contratoId: protocoloDaCliente.id,
          professionalId: Number(professionalId),
          localId,
          date,
        });
        resetAndClose();
        onSuccess();
      } catch (err: unknown) {
        setCreateError(extractCriarAgendamentoSubmitError(err, false));
      } finally {
        setCreateLoading(false);
      }
      return;
    }

    if (protocolosCarregando && selectedProcedures.length > 0) {
      setCreateError("Carregando protocolos. Tente novamente.");
      return;
    }
    const selecao = classificarSelecaoProtocolo(procedures, selectedProcedures, protocolos);
    if (selecao.tipo === "erro") {
      setCreateError(selecao.mensagem);
      return;
    }
    const protocolo = selecao.tipo === "agendar" ? selecao.protocolo : null;

    const localSel = localId ? locaisAtendimento.find((l) => l.id === localId) : undefined;
    const profSel = professionalId ? professionals.find((p) => p.id === professionalId) : undefined;
    const duracaoBase = protocolo?.tempo_estimado || resumo.duracao;
    const duracaoChecagem = calcularDuracaoAgendamento(duracaoBase, profSel, localSel);

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
      retornoProcedureId: protocolo ? "" : retornoProcedureId,
      formaCobranca: protocolo ? formaCobranca : undefined,
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
