"use client";

import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { ClinicaBelezaAPI, clinicaBelezaFetch, type LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { fetchHistoricoPaciente } from "@/lib/clinica-beleza-cadastros-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { logger } from "@/lib/logger";
import type { ConsultaPrintMeta } from "@/lib/consulta-print";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import type { MemedPrescricaoHandle } from "@/components/clinica-beleza/consultas/MemedPrescricao";
import {
  type Anamnese,
  type Consulta,
  type Evolucao,
  consultaEstaConcluida,
  consultaProcedimentos,
  consultaProcedimentosNomes,
  type Protocolo,
  type TabId,
} from "@/components/clinica-beleza/consultas/consultas-types";

type LoaderSlice = {
  selected: Consulta;
  setSelected: (c: Consulta | ((prev: Consulta) => Consulta)) => void;
  setTab: (tab: TabId) => void;
  protocolos: Protocolo[];
  anamnese: Anamnese;
  setAnamnese: (a: Anamnese) => void;
  anamneseDraft: Anamnese;
  setAnamneseDraft: Dispatch<SetStateAction<Anamnese>>;
  evolucoes: Evolucao[];
  setEvolucoes: (e: Evolucao[]) => void;
  historico: Consulta[];
  setHistorico: (h: Consulta[]) => void;
  observacoes: string;
  setObservacoes: (v: string) => void;
  observacoesDraft: string;
  setObservacoesDraft: Dispatch<SetStateAction<string>>;
  loadDetalhes: (c: Consulta, opts?: { detailPreloaded?: boolean }) => Promise<void>;
  refreshConsulta: (patch?: Record<string, unknown>) => Promise<void>;
  recarregarPrescricoes: () => Promise<void>;
};

type UseConsultaDetailActionsArgs = LoaderSlice & {
  onBack: () => void;
  onListRefresh: () => void | Promise<void>;
};

export function useConsultaDetailActions(loader: UseConsultaDetailActionsArgs) {
  const {
    selected,
    setSelected,
    setTab,
    anamnese,
    setAnamnese,
    anamneseDraft,
    setAnamneseDraft,
    setEvolucoes,
    setHistorico,
    observacoes,
    setObservacoes,
    observacoesDraft,
    setObservacoesDraft,
    protocolos,
    historico,
    loadDetalhes,
    refreshConsulta,
    recarregarPrescricoes: recarregarPrescricoesBase,
    onBack,
    onListRefresh,
  } = loader;

  const [saving, setSaving] = useState(false);
  const [editAtendimento, setEditAtendimento] = useState(false);
  const [editAnamnese, setEditAnamnese] = useState(false);
  const [editEvolucao, setEditEvolucao] = useState(false);
  const [protocoloPreview, setProtocoloPreview] = useState<Protocolo | null>(null);
  const [protocoloPendingId, setProtocoloPendingId] = useState<number | null>(null);
  const [showFinalizarModal, setShowFinalizarModal] = useState(false);
  const [finalizando, setFinalizando] = useState(false);
  const [iniciando, setIniciando] = useState(false);
  const [showProfessionalModal, setShowProfessionalModal] = useState(false);
  const [profissionaisDisponiveis, setProfissionaisDisponiveis] = useState<
    { id: number; nome?: string; name?: string }[]
  >([]);
  const [memedBusy, setMemedBusy] = useState(false);
  const [locaisAtendimento, setLocaisAtendimento] = useState<LocalAtendimentoItem[]>([]);
  const [finalizarForm, setFinalizarForm] = useState({
    payment_method: "CASH",
    mark_as_paid: false,
    amount: "",
    local_atendimento: "" as number | "",
  });
  const [prescricoesRefresh, setPrescricoesRefresh] = useState(0);
  const [evolucaoForm, setEvolucaoForm] = useState({
    descricao: "",
    procedimento_realizado: "",
    produtos_utilizados: "",
    orientacoes: "",
    satisfacao: "",
  });

  const memedRef = useRef<MemedPrescricaoHandle>(null);

  const recarregarPrescricoes = useCallback(async () => {
    await recarregarPrescricoesBase();
    setPrescricoesRefresh((n) => n + 1);
  }, [recarregarPrescricoesBase]);

  const formatData = (d?: string | null) =>
    d ? formatClinicaDateTime(new Date(d)) : "—";

  const valorPagamentoConsulta = (c: Consulta) => {
    const total = Number(c.valor_pagamento ?? 0);
    if (total > 0) return total;
    const taxa = Number(c.valor_consulta ?? 0);
    const procs = Number(c.valor_procedimentos ?? 0);
    return taxa + procs;
  };

  const printMeta: ConsultaPrintMeta = {
    patientName: selected.patient_name,
    professionalName: selected.professional_name,
    procedureName: consultaProcedimentosNomes(selected),
    consultaId: selected.id,
    dataConsulta: formatData(selected.data_inicio),
  };

  const procedimentosRealizados = consultaProcedimentos(selected);

  useEffect(() => {
    ClinicaBelezaAPI.locaisAtendimento
      .list()
      .then(setLocaisAtendimento)
      .catch((e) => logger.warn("Erro ao carregar locais de atendimento:", e));
  }, []);

  const salvarObservacoes = async () => {
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.update(selected.id, {
        observacoes_gerais: observacoesDraft,
      });
      setSelected({ ...selected, ...updated });
      setObservacoes(observacoesDraft);
      setEditAtendimento(false);
      await onListRefresh();
    } catch {
      alert("Erro ao salvar atendimento.");
    } finally {
      setSaving(false);
    }
  };

  const selecionarProtocolo = (protocolId: number) => {
    const p = protocolos.find((x) => x.id === protocolId);
    if (!p) return;
    setProtocoloPendingId(protocolId);
    setProtocoloPreview(p);
  };

  const confirmarProtocolo = async () => {
    if (!protocoloPendingId) return;
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.aplicarProtocolo(
        selected.id,
        protocoloPendingId,
      );
      const notas = updated.protocolo_notas || observacoes;
      setSelected({ ...selected, ...updated });
      setObservacoes(notas);
      setObservacoesDraft(notas);
      setProtocoloPreview(null);
      setProtocoloPendingId(null);
      await onListRefresh();
    } catch {
      alert("Erro ao aplicar protocolo.");
    } finally {
      setSaving(false);
    }
  };

  const salvarAnamnese = async () => {
    setSaving(true);
    try {
      const payload: Record<string, unknown> = { ...anamneseDraft };
      for (const key of ["peso", "altura"] as const) {
        if (payload[key] === "" || payload[key] == null) payload[key] = null;
      }
      await ClinicaBelezaAPI.anamnese.save(selected.patient, payload);
      setAnamnese(anamneseDraft);
      setEditAnamnese(false);
    } catch {
      alert("Erro ao salvar anamnese.");
    } finally {
      setSaving(false);
    }
  };

  const salvarEvolucao = async () => {
    if (!evolucaoForm.descricao.trim() && !evolucaoForm.procedimento_realizado.trim()) {
      alert("Preencha a evolução ou o procedimento realizado.");
      return;
    }
    setSaving(true);
    try {
      const payload: Record<string, unknown> = { ...evolucaoForm };
      if (selected.protocolo_notas) payload.protocolo_snapshot = selected.protocolo_notas;
      if (evolucaoForm.satisfacao) payload.satisfacao = Number(evolucaoForm.satisfacao);
      await ClinicaBelezaAPI.consultas.evolucoes.create(selected.id, payload);
      const evol = await ClinicaBelezaAPI.consultas.evolucoes.list(selected.id);
      setEvolucoes(Array.isArray(evol) ? evol : []);
      setEvolucaoForm({
        descricao: "",
        procedimento_realizado: "",
        produtos_utilizados: "",
        orientacoes: "",
        satisfacao: "",
      });
      setEditEvolucao(false);
    } catch {
      alert("Erro ao registrar evolução.");
    } finally {
      setSaving(false);
    }
  };

  const iniciarConsulta = async (professionalId?: number) => {
    if (!selected.professional && !professionalId) {
      try {
        const res = await clinicaBelezaFetch("/professionals/");
        if (res.ok) {
          const json = await res.json();
          const profs = json.results || json;
          setProfissionaisDisponiveis(Array.isArray(profs) ? profs : []);
        }
      } catch {
        /* fallback empty */
      }
      setShowProfessionalModal(true);
      return;
    }

    if (!confirm("Iniciar atendimento? A agenda será marcada como Em atendimento.")) return;
    setIniciando(true);
    try {
      const body = professionalId ? { professional: professionalId } : undefined;
      const data = await ClinicaBelezaAPI.consultas.iniciar(selected.id, body);
      setSelected({ ...selected, ...data });
      await onListRefresh();
      const hist = await fetchHistoricoPaciente(selected.patient).catch(() => []);
      setHistorico(Array.isArray(hist) ? (hist as Consulta[]) : []);
    } catch (e: unknown) {
      alert(formatApiErrorBody(e) || "Erro ao iniciar consulta.");
    } finally {
      setIniciando(false);
    }
  };

  const abrirFinalizarModal = async () => {
    let consultaAtual = selected;
    try {
      const fresh = await ClinicaBelezaAPI.consultas.get(selected.id);
      consultaAtual = { ...selected, ...fresh };
      setSelected(consultaAtual);
    } catch (e) {
      logger.warn("Erro ao atualizar valor da consulta:", e);
    }
    const total = valorPagamentoConsulta(consultaAtual);
    setFinalizarForm({
      payment_method: "CASH",
      mark_as_paid: false,
      amount: total > 0 ? String(total) : "",
      local_atendimento: consultaAtual.local_atendimento ?? "",
    });
    setShowFinalizarModal(true);
  };

  const finalizarConsulta = async () => {
    setFinalizando(true);
    try {
      const updated = (await ClinicaBelezaAPI.consultas.finalizar(selected.id, {
        payment_method: finalizarForm.payment_method,
        mark_as_paid: finalizarForm.mark_as_paid,
        amount: finalizarForm.amount || valorPagamentoConsulta(selected) || undefined,
        local_atendimento: finalizarForm.local_atendimento || undefined,
      })) as Consulta & { error?: string };
      if (updated?.error) throw new Error(updated.error);
      const consultaAtualizada = { ...selected, ...updated };
      setSelected(consultaAtualizada);
      setShowFinalizarModal(false);
      setTab("atendimento");
      await loadDetalhes(consultaAtualizada);
      await onListRefresh();
      alert(
        finalizarForm.mark_as_paid
          ? "Consulta finalizada. Pagamento registrado no Financeiro."
          : "Consulta finalizada. Lançamento pendente criado no Financeiro e agenda atualizada.",
      );
    } catch (e: unknown) {
      alert(formatApiErrorBody(e) || "Erro ao finalizar consulta.");
    } finally {
      setFinalizando(false);
    }
  };

  const abrirMemed = async () => {
    if (!memedRef.current || memedBusy) return;
    setMemedBusy(true);
    try {
      await memedRef.current.abrir();
    } catch (e: unknown) {
      logger.warn("Erro ao abrir a Memed:", e);
      alert(e instanceof Error ? e.message : "Erro ao abrir a prescrição da Memed.");
    } finally {
      setMemedBusy(false);
    }
  };

  const excluirConsulta = async () => {
    if (consultaEstaConcluida(selected)) {
      alert("Consultas concluídas não podem ser excluídas.");
      return;
    }
    if (!confirm("Excluir esta consulta? O agendamento vinculado será cancelado.")) return;
    try {
      await ClinicaBelezaAPI.consultas.excluir(selected.id);
      await onListRefresh();
      onBack();
    } catch (e: unknown) {
      alert(formatApiErrorBody(e) || "Erro ao excluir consulta.");
    }
  };

  const outraConsultaEmAndamento = historico.find(
    (c) => c.id !== selected.id && c.status === "IN_PROGRESS",
  );
  const podeIniciar = selected.status === "SCHEDULED" && !outraConsultaEmAndamento;
  const podeFinalizar = selected.status === "IN_PROGRESS";
  const consultaConcluida = consultaEstaConcluida(selected);
  const podeExcluir = !consultaConcluida;
  const consultaAtiva = selected.status === "IN_PROGRESS";
  const consultaFinalizada = consultaConcluida;

  const resetEditsOnLoad = () => {
    setEditAtendimento(false);
    setEditAnamnese(false);
    setEditEvolucao(false);
    setProtocoloPreview(null);
    setProtocoloPendingId(null);
  };

  return {
    saving,
    editAtendimento,
    setEditAtendimento,
    editAnamnese,
    setEditAnamnese,
    editEvolucao,
    setEditEvolucao,
    protocoloPreview,
    setProtocoloPreview,
    protocoloPendingId,
    setProtocoloPendingId,
    showFinalizarModal,
    setShowFinalizarModal,
    finalizando,
    iniciando,
    showProfessionalModal,
    setShowProfessionalModal,
    profissionaisDisponiveis,
    memedRef,
    memedBusy,
    locaisAtendimento,
    finalizarForm,
    setFinalizarForm,
    prescricoesRefresh,
    evolucaoForm,
    setEvolucaoForm,
    recarregarPrescricoes,
    formatData,
    printMeta,
    procedimentosRealizados,
    valorPagamentoConsulta,
    salvarObservacoes,
    selecionarProtocolo,
    confirmarProtocolo,
    salvarAnamnese,
    salvarEvolucao,
    iniciarConsulta,
    abrirFinalizarModal,
    finalizarConsulta,
    abrirMemed,
    excluirConsulta,
    outraConsultaEmAndamento,
    podeIniciar,
    podeFinalizar,
    podeExcluir,
    consultaAtiva,
    consultaFinalizada,
    resetEditsOnLoad,
    anamnese,
    anamneseDraft,
    setAnamneseDraft,
    observacoes,
    observacoesDraft,
    setObservacoesDraft,
  };
}
