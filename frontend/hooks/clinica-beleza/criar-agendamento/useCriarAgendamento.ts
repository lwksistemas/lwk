"use client";

import { useMemo, useState } from "react";
import { useNovaConsultaForm } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import type { RetornoVerificacaoResult } from "@/lib/clinica-beleza-api";
import { type HorarioTrabalho } from "@/lib/clinica-beleza-work-hours";
import {
  computeCriarAgendamentoPricing,
  getCriarAgendamentoModalLabels,
} from "./criar-agendamento-builders";
import type { UseCriarAgendamentoOptions } from "./criar-agendamento-types";
import { useCriarAgendamentoEffects } from "./useCriarAgendamentoEffects";
import { useCriarAgendamentoSubmit } from "./useCriarAgendamentoSubmit";

export function useCriarAgendamento(options: UseCriarAgendamentoOptions) {
  const {
    open,
    mode = "agenda",
    nomesAgenda,
    locaisAtendimento,
    professionals,
    patients,
    procedures,
    onPatientsChange,
  } = options;

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

  const nomeAgendaUnico = nomesAgenda.length === 1 ? nomesAgenda[0] : null;
  const localUnico = locaisAtendimento.length === 1 ? locaisAtendimento[0] : null;

  const novaConsulta = useNovaConsultaForm({
    patients,
    procedures,
    enabled: open,
    requireProcedure: false,
  });

  const { mounted } = useCriarAgendamentoEffects(options, novaConsulta, {
    setDateInput,
    setTime,
    setNotes,
    setNomeAgendaId,
    setLocalAtendimentoId,
    setCreateError,
    setRetornoInfo,
    setRetornoProcedureId,
    setShowAdvanced,
    retornoProcedureId,
    professionalId: novaConsulta.professionalId,
    setHorariosProfissional,
    setVerificandoRetorno,
  });

  const { resetAndClose, handleSubmit, handleCreatePatient } = useCriarAgendamentoSubmit(options, {
    isConsulta,
    validateBase: novaConsulta.validateBase,
    resetForm: novaConsulta.resetForm,
    patientId: novaConsulta.patientId,
    professionalId: novaConsulta.professionalId,
    convenioId: novaConsulta.convenioId,
    selectedProcedures: novaConsulta.selectedProcedures,
    resumo: novaConsulta.resumo,
    dateInput,
    time,
    notes,
    nomeAgendaId,
    localAtendimentoId,
    retornoProcedureId,
    horariosProfissional,
    createLoading,
    setCreateLoading,
    setCreateError,
    setTime,
    setDateInput,
    setNotes,
    setNomeAgendaId,
    setLocalAtendimentoId,
  });

  const pricing = useMemo(
    () =>
      computeCriarAgendamentoPricing(
        localAtendimentoId,
        locaisAtendimento,
        retornoInfo,
        novaConsulta.resumo.valor,
      ),
    [localAtendimentoId, locaisAtendimento, retornoInfo, novaConsulta.resumo.valor],
  );

  const labels = getCriarAgendamentoModalLabels(isConsulta, createLoading);

  return {
    mounted,
    isConsulta,
    ...labels,
    createLoading,
    createError,
    resetAndClose,
    handleSubmit,
    ...novaConsulta,
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
    ...pricing,
    handleCreatePatient,
    onPatientsChange,
  };
}

export type UseCriarAgendamentoReturn = ReturnType<typeof useCriarAgendamento>;
