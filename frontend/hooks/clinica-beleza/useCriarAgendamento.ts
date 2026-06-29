"use client";

import { useEffect, useState } from "react";
import type { PatientQuickOption } from "@/components/clinica-beleza/PatientQuickRegisterField";
import {
  formatDateInputValue,
  formatTimeFromDate,
  resolveDefaultLocalId,
  resolveDefaultNomeAgendaId,
  type CriarAgendamentoProfessional,
  type ModalCriarAgendamentoMode,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import { useNovaConsultaForm, type ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import { formatApiErrorBody } from "@/lib/api-errors";
import { ClinicaBelezaAPI, clinicaBelezaFetch, type LocalAtendimentoItem, type NomeAgendaItem, type RetornoVerificacaoResult } from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";
import { calcularDuracaoAgendamento } from "@/lib/clinica-beleza-duracao";
import { isBrowserOffline, isFetchNetworkError } from "@/lib/clinica-beleza-offline";
import { type HorarioTrabalho, workHoursRejectionMessage } from "@/lib/clinica-beleza-work-hours";
import { adicionarNaFilaSync } from "@/lib/offline-db";
import { notificarFilaAtualizada } from "@/hooks/useSyncPending";

export interface UseCriarAgendamentoOptions {
  open: boolean;
  mode?: ModalCriarAgendamentoMode;
  selectedDate: Date | null;
  defaultProfessionalId?: string;
  professionals: CriarAgendamentoProfessional[];
  patients: PatientQuickOption[];
  procedures: ConsultaFormProcedure[];
  nomesAgenda: NomeAgendaItem[];
  locaisAtendimento: LocalAtendimentoItem[];
  onClose: () => void;
  onSuccess: () => void;
  onPatientsChange: (patients: PatientQuickOption[]) => void;
  onConsultaCreated?: (consultaId: number) => void;
  onOfflineEventCreated?: (event: unknown) => void;
}

export function useCriarAgendamento({
  open,
  mode = "agenda",
  selectedDate,
  defaultProfessionalId = "",
  professionals,
  patients,
  procedures,
  nomesAgenda,
  locaisAtendimento,
  onClose,
  onSuccess,
  onPatientsChange,
  onConsultaCreated,
  onOfflineEventCreated,
}: UseCriarAgendamentoOptions) {
  const isConsulta = mode === "consulta";

  const [time, setTime] = useState("09:00");
  const [dateInput, setDateInput] = useState("");
  const [notes, setNotes] = useState("");
  const [nomeAgendaId, setNomeAgendaId] = useState<number | "">("");
  const [localAtendimentoId, setLocalAtendimentoId] = useState<number | "">("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [horariosProfissional, setHorariosProfissional] = useState<HorarioTrabalho[]>([]);
  const [retornoInfo, setRetornoInfo] = useState<RetornoVerificacaoResult | null>(null);
  const [retornoProcedureId, setRetornoProcedureId] = useState<number | "">("");
  const [verificandoRetorno, setVerificandoRetorno] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [mounted, setMounted] = useState(false);

  const nomeAgendaUnico = nomesAgenda.length === 1 ? nomesAgenda[0] : null;
  const localUnico = locaisAtendimento.length === 1 ? locaisAtendimento[0] : null;

  const {
    patientId,
    setPatientId,
    professionalId,
    setProfessionalId,
    convenioId,
    setConvenioId,
    selectedProcedures,
    convenios,
    precosMap,
    adicionarProcedimento,
    removerProcedimento,
    resumo,
    resetForm,
    validateBase,
  } = useNovaConsultaForm({ patients, procedures, enabled: open, requireProcedure: false });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    resetForm();
    setConvenioId("");
    setProfessionalId(defaultProfessionalId ? Number(defaultProfessionalId) : "");
    setNomeAgendaId(resolveDefaultNomeAgendaId(nomesAgenda));
    setLocalAtendimentoId(resolveDefaultLocalId(locaisAtendimento));
    const base = selectedDate ?? new Date();
    setDateInput(formatDateInputValue(base));
    setTime(formatTimeFromDate(base));
    setNotes("");
    setCreateError("");
    setRetornoInfo(null);
    setRetornoProcedureId("");
    setShowAdvanced(false);
  }, [open, selectedDate, defaultProfessionalId, resetForm, setConvenioId, setProfessionalId, nomesAgenda, locaisAtendimento]);

  useEffect(() => {
    if (!open || nomesAgenda.length === 0) return;
    setNomeAgendaId((current) => current || resolveDefaultNomeAgendaId(nomesAgenda));
  }, [open, nomesAgenda]);

  useEffect(() => {
    if (!open || locaisAtendimento.length === 0) return;
    setLocalAtendimentoId((current) => current || resolveDefaultLocalId(locaisAtendimento));
  }, [open, locaisAtendimento]);

  useEffect(() => {
    if (!open || !patientId) {
      setRetornoInfo(null);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      setVerificandoRetorno(true);
      try {
        const procedureIds = [...selectedProcedures];
        if (retornoProcedureId && !procedureIds.includes(Number(retornoProcedureId))) {
          procedureIds.push(Number(retornoProcedureId));
        }
        const result = await ClinicaBelezaAPI.retorno.verificar({
          patient_id: Number(patientId),
          procedure_ids: procedureIds.length ? procedureIds : undefined,
          retorno_procedure_id: retornoProcedureId ? Number(retornoProcedureId) : undefined,
        });
        if (!cancelled) setRetornoInfo(result);
      } catch {
        if (!cancelled) setRetornoInfo(null);
      } finally {
        if (!cancelled) setVerificandoRetorno(false);
      }
    }, 350);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [open, patientId, selectedProcedures, retornoProcedureId]);

  useEffect(() => {
    if (!open || !professionalId) {
      setHorariosProfissional([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await clinicaBelezaFetch(`/professionals/${professionalId}/horarios-trabalho/`);
        if (!res.ok || cancelled) return;
        const data = await res.json();
        setHorariosProfissional(Array.isArray(data) ? data : []);
      } catch {
        if (!cancelled) setHorariosProfissional([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, professionalId]);

  const handleCreatePatient = async (data: { nome: string; telefone: string; cpf: string }) => {
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
  };

  const buildAppointmentDate = (): Date | null => {
    const dateSource = dateInput ? new Date(`${dateInput}T12:00:00`) : selectedDate;
    if (!dateSource) return null;
    const [h, m] = time.split(":").map(Number);
    const date = new Date(dateSource);
    date.setHours(h, m, 0, 0);
    return date;
  };

  const resetAndClose = () => {
    resetForm();
    setTime("09:00");
    setDateInput("");
    setNotes("");
    setNomeAgendaId("");
    setLocalAtendimentoId("");
    setCreateError("");
    setCreateLoading(false);
    onClose();
  };

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
    const date = buildAppointmentDate();
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

    const basePayload: Record<string, unknown> = {
      patient: Number(patientId),
      nome_agenda: Number(agendaId),
      notes: notes.trim() || null,
      date: date.toISOString(),
    };
    if (professionalId) basePayload.professional = Number(professionalId);
    if (localId) basePayload.local_atendimento = Number(localId);
    if (convenioId) basePayload.convenio = Number(convenioId);
    if (selectedProcedures.length === 1) {
      basePayload.procedure = selectedProcedures[0];
    } else if (selectedProcedures.length > 1) {
      basePayload.procedures_ids = selectedProcedures;
      basePayload.procedure = selectedProcedures[0];
    }
    if (retornoProcedureId) {
      basePayload.retorno_procedure = Number(retornoProcedureId);
    }

    const enqueueConsultaOffline = async () => {
      await adicionarNaFilaSync({ tipo: "consulta", payload: basePayload });
      notificarFilaAtualizada();
      resetAndClose();
      onSuccess();
    };

    const enqueueAgendamentoOffline = async () => {
      await adicionarNaFilaSync({ tipo: "agendamento", payload: { ...basePayload, status: "SCHEDULED" } });
      notificarFilaAtualizada();
      const patient = patients.find((p) => p.id === patientId);
      const professional = professionals.find((p) => p.id === professionalId);
      const procNames = selectedProcedures
        .map((id) => entityName(procedures.find((p) => p.id === id) || {}))
        .filter(Boolean)
        .join(", ");
      const nomeAgenda = nomesAgenda.find((a) => a.id === agendaId)?.nome;
      const titulo =
        [entityName(patient || {}), procNames || nomeAgenda || "Atendimento"].filter(Boolean).join(" • ") ||
        "Agendamento (offline)";
      const tempId = `offline-${Date.now()}`;
      const endDate = new Date(date);
      endDate.setMinutes(endDate.getMinutes() + duracaoChecagem);

      if (onOfflineEventCreated) {
        onOfflineEventCreated({
          id: tempId,
          title: titulo,
          start: date.toISOString(),
          end: endDate.toISOString(),
          backgroundColor: "#a855f7",
          borderColor: "#9333ea",
          textColor: "#fff",
          extendedProps: {
            dbId: tempId,
            status: "SCHEDULED",
            patient_name: entityName(patient || {}),
            patient_phone: "",
            professional_name: entityName(professional || {}),
            procedure_name: procNames,
            procedure_duration: resumo.duracao,
            procedure_price: resumo.valor,
            notes: notes.trim() || "",
          },
        });
      }
      resetAndClose();
    };

    try {
      if (isBrowserOffline()) {
        if (isConsulta) {
          await enqueueConsultaOffline();
          return;
        }
        await enqueueAgendamentoOffline();
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
            await enqueueConsultaOffline();
            return;
          }
          await enqueueAgendamentoOffline();
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

  const localSel = localAtendimentoId
    ? locaisAtendimento.find((l) => l.id === localAtendimentoId)
    : undefined;
  const taxaConsultaBase = localSel ? Number(localSel.valor_consulta) || 0 : 0;
  const taxaConsulta = retornoInfo?.elegivel ? 0 : taxaConsultaBase;
  const totalEstimado = taxaConsulta + resumo.valor;
  const regrasRetornoProc = retornoInfo?.regras_procedimento ?? [];
  const retornoProcAtivo = retornoInfo?.config?.retorno_procedimento_ativo ?? false;

  const modalTitle = isConsulta ? "Nova consulta" : "Novo agendamento";
  const modalSubtitle = isConsulta ? "Abrir consulta na clínica" : "Agendar atendimento na clínica";
  const submitLabel = isConsulta
    ? createLoading
      ? "Abrindo..."
      : "Abrir consulta"
    : createLoading
      ? "Agendando..."
      : "Agendar";

  return {
    mounted,
    isConsulta,
    modalTitle,
    modalSubtitle,
    submitLabel,
    createLoading,
    createError,
    resetAndClose,
    handleSubmit,
    patientId,
    setPatientId,
    professionalId,
    setProfessionalId,
    convenioId,
    setConvenioId,
    selectedProcedures,
    convenios,
    precosMap,
    adicionarProcedimento,
    removerProcedimento,
    resumo,
    dateInput,
    setDateInput,
    time,
    setTime,
    notes,
    setNotes,
    nomeAgendaId,
    setNomeAgendaId,
    localAtendimentoId,
    setLocalAtendimentoId,
    nomeAgendaUnico,
    localUnico,
    nomesAgenda,
    locaisAtendimento,
    professionals,
    patients,
    procedures,
    retornoInfo,
    retornoProcedureId,
    setRetornoProcedureId,
    verificandoRetorno,
    showAdvanced,
    setShowAdvanced,
    regrasRetornoProc,
    retornoProcAtivo,
    taxaConsultaBase,
    totalEstimado,
    handleCreatePatient,
    onPatientsChange,
  };
}

export type UseCriarAgendamentoReturn = ReturnType<typeof useCriarAgendamento>;
