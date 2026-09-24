"use client";

import { useEffect, useMemo, useState } from "react";
import { useNovaConsultaForm } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import {
  clinicaBelezaFetch,
  parseClinicaBelezaListResponse,
  parseClinicaBelezaResponseBody,
  type RetornoVerificacaoResult,
} from "@/lib/clinica-beleza-api";
import { dividirValorProtocolo } from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
import { findNomeAgendaByTipo } from "@/lib/clinica-beleza-tipo-agenda";
import { type HorarioTrabalho } from "@/lib/clinica-beleza-work-hours";
import {
  classificarSelecaoProtocolo,
  computeCriarAgendamentoPricing,
  getCriarAgendamentoModalLabels,
  type ProtocoloAgendaResumo,
  type ProtocoloFormaCobranca,
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
  const [protocolos, setProtocolos] = useState<ProtocoloAgendaResumo[]>([]);
  const [protocolosCarregando, setProtocolosCarregando] = useState(false);
  const [formaCobranca, setFormaCobranca] = useState<ProtocoloFormaCobranca>("POR_CONSULTA");

  useEffect(() => {
    if (!open) {
      setFormaCobranca("POR_CONSULTA");
      setProtocolos([]);
      return;
    }
    let ativo = true;
    setProtocolosCarregando(true);
    void (async () => {
      try {
        const res = await clinicaBelezaFetch("/protocolos/?active=true&all=1");
        const dados = await parseClinicaBelezaResponseBody(res);
        if (!ativo) return;
        setProtocolos(parseClinicaBelezaListResponse<ProtocoloAgendaResumo>(dados));
      } catch {
        if (ativo) setProtocolos([]);
      } finally {
        if (ativo) setProtocolosCarregando(false);
      }
    })();
    return () => {
      ativo = false;
    };
  }, [open]);

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
    retornoInfo,
    professionalId: novaConsulta.professionalId,
    dateInput,
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
    protocolos,
    protocolosCarregando,
    formaCobranca,
    setCreateLoading,
    setCreateError,
    setTime,
    setDateInput,
    setNotes,
    setNomeAgendaId,
    setLocalAtendimentoId,
  });

  const selecaoProtocolo = useMemo(
    () => classificarSelecaoProtocolo(procedures, novaConsulta.selectedProcedures, protocolos),
    [procedures, novaConsulta.selectedProcedures, protocolos],
  );
  const protocoloSelecionado =
    !protocolosCarregando && selecaoProtocolo.tipo === "agendar" ? selecaoProtocolo.protocolo : null;
  const protocoloErro =
    !protocolosCarregando && selecaoProtocolo.tipo === "erro" ? selecaoProtocolo.mensagem : "";

  const pricing = useMemo(() => {
    const base = computeCriarAgendamentoPricing(
      localAtendimentoId,
      locaisAtendimento,
      protocoloSelecionado ? null : retornoInfo,
      novaConsulta.resumo.valor,
    );
    if (!protocoloSelecionado) return base;
    const partes = dividirValorProtocolo(
      novaConsulta.resumo.valor,
      protocoloSelecionado.sessoes || 1,
      formaCobranca,
    );
    const primeira = partes[0] ?? 0;
    return {
      ...base,
      taxaConsultaBase: 0,
      totalEstimado: primeira,
    };
  }, [
    localAtendimentoId,
    locaisAtendimento,
    retornoInfo,
    novaConsulta.resumo.valor,
    protocoloSelecionado,
    formaCobranca,
  ]);

  useEffect(() => {
    if (!open || !protocoloSelecionado || nomesAgenda.length === 0) return;
    const tipoProtocolo = findNomeAgendaByTipo(nomesAgenda, "PROTOCOLO");
    if (tipoProtocolo) setNomeAgendaId(tipoProtocolo.id);
  }, [open, protocoloSelecionado, nomesAgenda]);

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
    protocoloSelecionado,
    protocoloErro,
    formaCobranca,
    setFormaCobranca,
    handleCreatePatient,
    onPatientsChange,
  };
}

export type UseCriarAgendamentoReturn = ReturnType<typeof useCriarAgendamento>;
