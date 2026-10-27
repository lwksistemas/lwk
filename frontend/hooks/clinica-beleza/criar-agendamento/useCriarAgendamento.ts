"use client";

import { useEffect, useMemo, useState } from "react";
import { useNovaConsultaForm } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import {
  clinicaBelezaFetch,
  parseClinicaBelezaListResponse,
  parseClinicaBelezaResponseBody,
  type RetornoVerificacaoResult,
} from "@/lib/clinica-beleza-api";
import { dividirValorProtocolo, precoDaPromocao } from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
import { procedurePrice } from "@/lib/clinica-beleza-entities";
import { normalizarTipoAgendaNome } from "@/lib/clinica-beleza-tipo-agenda";
import { precoProcedimento } from "@/lib/convenio-precos";
import { type HorarioTrabalho } from "@/lib/clinica-beleza-work-hours";
import {
  computeCriarAgendamentoPricing,
  getCriarAgendamentoModalLabels,
  type ProtocoloAgendaResumo,
  type ProtocoloFormaCobranca,
} from "./criar-agendamento-builders";
import type { UseCriarAgendamentoOptions } from "./criar-agendamento-types";
import { useCriarAgendamentoEffects } from "./useCriarAgendamentoEffects";
import type { ProtocoloClientePendente } from "./criar-agendamento-submit-types";
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
  const [protocolosDaCliente, setProtocolosDaCliente] = useState<ProtocoloClientePendente[]>([]);
  const [protocolosClienteCarregando, setProtocolosClienteCarregando] = useState(false);
  const [protocoloClienteId, setProtocoloClienteId] = useState<number | "">("");
  const [protocoloModeloId, setProtocoloModeloId] = useState<number | "">("");

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

  useEffect(() => {
    if (!open || !novaConsulta.patientId) {
      setProtocolosDaCliente([]);
      setProtocoloClienteId("");
      setProtocoloModeloId("");
      setProtocolosClienteCarregando(false);
      return;
    }
    let ativo = true;
    setProtocolosDaCliente([]);
    setProtocoloClienteId("");
    setProtocolosClienteCarregando(true);
    setProtocoloModeloId("");
    void (async () => {
      try {
        const res = await clinicaBelezaFetch(
          `/protocolos/personalizados/pendentes/?patient=${novaConsulta.patientId}`,
        );
        const dados = await parseClinicaBelezaResponseBody(res);
        if (!ativo) return;
        const lista = Array.isArray(dados) ? (dados as ProtocoloClientePendente[]) : [];
        setProtocolosDaCliente(lista);
        setProtocoloClienteId((atual) => (lista.some((item) => item.id === atual) ? atual : ""));
      } catch {
        if (ativo) setProtocolosDaCliente([]);
      } finally {
        if (ativo) setProtocolosClienteCarregando(false);
      }
    })();
    return () => {
      ativo = false;
    };
  }, [open, novaConsulta.patientId]);

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
    protocoloClienteId,
    protocoloModeloId,
    protocolosDaCliente,
    setProtocoloClienteId,
    setCreateLoading,
    setCreateError,
    setTime,
    setDateInput,
    setNotes,
    setNomeAgendaId,
    setLocalAtendimentoId,
  });

  const agendaEhProtocolo =
    normalizarTipoAgendaNome(nomesAgenda.find((item) => item.id === nomeAgendaId)?.nome || "") === "PROTOCOLO";
  const protocoloCliente =
    protocolosDaCliente.find((item) => item.id === protocoloClienteId) ?? null;
  const protocoloSelecionado =
    agendaEhProtocolo && protocolosDaCliente.length === 0 && !protocolosClienteCarregando
      ? protocolos.find((item) => item.id === protocoloModeloId) ?? null
      : null;

  const valorProtocolo = useMemo(() => {
    if (!protocoloSelecionado) return 0;
    const itens = protocoloSelecionado.procedimentos || [];
    if (itens.length > 0) {
      const conta = precoDaPromocao(
        itens.map((item) => {
          const procedimento = procedures.find((atual) => atual.id === item.procedure);
          const particular = procedimento
            ? Number(procedurePrice(procedimento)) || Number(item.preco) || 0
            : Number(item.preco) || 0;
          return {
            preco: precoProcedimento(item.procedure, particular, novaConsulta.convenioId, novaConsulta.precosMap),
            desconto_tipo: item.desconto_tipo,
            desconto_valor: Number(item.desconto_valor) || 0,
          };
        }),
        protocoloSelecionado.desconto_escopo || "total",
        protocoloSelecionado.desconto_tipo || "percentual",
        Number(protocoloSelecionado.desconto_valor) || 0,
      );
      return conta.liquido;
    }
    const procedimento = procedures.find((item) => item.id === protocoloSelecionado.procedure);
    const particular = procedimento ? Number(procedurePrice(procedimento)) || 0 : 0;
    return precoProcedimento(
      protocoloSelecionado.procedure,
      particular,
      novaConsulta.convenioId,
      novaConsulta.precosMap,
    );
  }, [protocoloSelecionado, procedures, novaConsulta.convenioId, novaConsulta.precosMap]);

  const pricing = useMemo(() => {
    const pacoteCliente = protocoloCliente
      ? {
          sessoes: Number(protocoloCliente.sessoes) || 1,
          valor: Number(protocoloCliente.valor_total) || 0,
        }
      : null;
    const pacote = protocoloSelecionado
      ? { sessoes: protocoloSelecionado.sessoes || 1, valor: valorProtocolo }
      : pacoteCliente;
    const base = computeCriarAgendamentoPricing(
      localAtendimentoId,
      locaisAtendimento,
      pacote ? null : retornoInfo,
      novaConsulta.resumo.valor,
    );
    if (!pacote) return base;
    const partes = dividirValorProtocolo(pacote.valor, pacote.sessoes, formaCobranca);
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
    protocoloCliente,
    formaCobranca,
    valorProtocolo,
  ]);

  useEffect(() => {
    if (!agendaEhProtocolo) {
      if (protocoloClienteId) setProtocoloClienteId("");
      if (protocoloModeloId) setProtocoloModeloId("");
      return;
    }
    if (protocolosClienteCarregando || protocolosCarregando) return;
    if (protocolosDaCliente.length > 0) {
      if (protocoloModeloId) setProtocoloModeloId("");
      if (protocolosDaCliente.length === 1 && protocoloClienteId !== protocolosDaCliente[0].id) {
        setProtocoloClienteId(protocolosDaCliente[0].id);
      }
      return;
    }
    if (protocolos.length === 1 && protocoloModeloId !== protocolos[0].id) {
      setProtocoloModeloId(protocolos[0].id);
    }
  }, [
    agendaEhProtocolo,
    protocoloClienteId,
    protocoloModeloId,
    protocolosDaCliente,
    protocolos,
    protocolosClienteCarregando,
    protocolosCarregando,
  ]);

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
    valorProtocolo,
    agendaEhProtocolo,
    formaCobranca,
    setFormaCobranca,
    protocolos,
    protocolosCarregando,
    protocolosClienteCarregando,
    protocolosDaCliente,
    protocoloClienteId,
    setProtocoloClienteId,
    protocoloModeloId,
    setProtocoloModeloId,
    protocoloCliente,
    handleCreatePatient,
    onPatientsChange,
  };
}

export type UseCriarAgendamentoReturn = ReturnType<typeof useCriarAgendamento>;
