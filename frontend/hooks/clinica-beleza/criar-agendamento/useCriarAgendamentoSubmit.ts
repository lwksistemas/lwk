import { useCallback } from "react";
import {
  resolveDefaultLocalId,
  resolveDefaultNomeAgendaId,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import { formatApiErrorBody } from "@/lib/api-errors";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { calcularDuracaoAgendamento } from "@/lib/clinica-beleza-duracao";
import { isBrowserOffline, isFetchNetworkError } from "@/lib/clinica-beleza-offline";
import { workHoursRejectionMessage, type HorarioTrabalho } from "@/lib/clinica-beleza-work-hours";
import { buildAppointmentDate, buildCriarAgendamentoPayload } from "./criar-agendamento-builders";
import {
  buildOfflineAgendaEvent,
  enqueueAgendamentoOffline,
  enqueueConsultaOffline,
} from "./criar-agendamento-offline";
import type { UseCriarAgendamentoOptions } from "./criar-agendamento-types";

export function useCriarAgendamentoSubmit(
  options: UseCriarAgendamentoOptions,
  ctx: {
    isConsulta: boolean;
    validateBase: () => string | null;
    resetForm: () => void;
    patientId: number | "";
    professionalId: number | "";
    convenioId: number | "";
    selectedProcedures: number[];
    resumo: { duracao: number; valor: number };
    dateInput: string;
    time: string;
    notes: string;
    nomeAgendaId: number | "";
    localAtendimentoId: number | "";
    retornoProcedureId: number | "";
    horariosProfissional: HorarioTrabalho[];
    createLoading: boolean;
    setCreateLoading: (v: boolean) => void;
    setCreateError: (v: string) => void;
    setTime: (v: string) => void;
    setDateInput: (v: string) => void;
    setNotes: (v: string) => void;
    setNomeAgendaId: (v: number | "") => void;
    setLocalAtendimentoId: (v: number | "") => void;
  },
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
    setTime("09:00");
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

  const handleCreatePatient = useCallback(async (data: { nome: string; telefone: string; cpf: string }) => {
    const body: Record<string, string> = { nome: data.nome };
    if (data.telefone) body.telefone = data.telefone.replace(/\D/g, "");
    if (data.cpf) body.cpf = data.cpf.replace(/\D/g, "");
    const res = await clinicaBelezaFetch("/patients/", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatApiErrorBody(err) || "Erro ao cadastrar paciente");
    }
    return res.json();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateBase();
    if (validationError) {
      setCreateError(validationError.replace("cliente", "paciente"));
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
        const consulta = await ClinicaBelezaAPI.consultas.criar(
          basePayload as {
            patient: number;
            professional: number;
            procedure?: number;
            procedures_ids?: number[];
            local_atendimento?: number;
            convenio?: number | null;
          },
        );
        resetAndClose();
        onSuccess();
        if (consulta?.id != null) onConsultaCreated?.(Number(consulta.id));
        return;
      }

      const payload = { ...basePayload, status: "SCHEDULED" };
      const res = await clinicaBelezaFetch("/agenda/create/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(formatApiErrorBody(data) || "Erro ao criar agendamento");
      }
      resetAndClose();
      onSuccess();
    } catch (err: unknown) {
      const apiMsg =
        err && typeof err === "object" && "error" in err && typeof (err as { error?: unknown }).error === "string"
          ? (err as { error: string }).error
          : null;
      const msg =
        apiMsg ||
        (err instanceof Error ? err.message : null) ||
        (isConsulta ? "Erro ao abrir consulta" : "Erro ao criar agendamento");

      if (isFetchNetworkError(msg)) {
        try {
          if (isConsulta) {
            await finishConsultaOffline();
            return;
          }
          await finishAgendamentoOffline();
          return;
        } catch {
          setCreateError("Sem conexão. Não foi possível salvar offline.");
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
