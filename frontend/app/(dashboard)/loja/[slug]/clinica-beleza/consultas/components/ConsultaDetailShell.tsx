"use client";

import dynamic from "next/dynamic";
import { Fragment, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import {
  ClipboardList,
  History,
  FileText,
  Activity,
  FolderOpen,
  CheckCircle2,
  Play,
  Trash2,
  Package,
  Camera,
} from "lucide-react";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, clinicaBelezaFetch, type LocalAtendimentoItem, type PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { toUpperCase } from "@/lib/format-br";
import { CLINICA_CONSULTA_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { fetchHistoricoPaciente } from "@/lib/clinica-beleza-cadastros-api";
import type { ConsultaPrintMeta } from "@/lib/consulta-print";
import { formatApiErrorBody } from "@/lib/api-errors";
import { logger } from "@/lib/logger";
import {
  type Consulta,
  consultaEstaConcluida,
  consultaProcedimentos,
  consultaProcedimentosNomes,
  type Protocolo,
  type Anamnese,
  type Evolucao,
  type TabId,
  EMPTY_ANAMNESE,
} from "./consultas-types";
import { ConsultaAtendimentoTab } from "./ConsultaAtendimentoTab";
import { ConsultaProdutosTab } from "./ConsultaProdutosTab";
import { ConsultaAnamneseTab } from "./ConsultaAnamneseTab";
import { ConsultaEvolucaoTab } from "./ConsultaEvolucaoTab";
import { ConsultaTermoConsentimentoButton } from "./ConsultaTermoConsentimentoButton";
import type { MemedPrescricaoHandle } from "./MemedPrescricao";

const ConsultaHistoricoTab = dynamic(
  () => import("./ConsultaHistoricoTab").then((m) => ({ default: m.ConsultaHistoricoTab })),
  { loading: () => <div className="text-center py-12 text-gray-500 text-sm">Carregando histórico...</div> },
);

const ConsultaDocumentosTab = dynamic(
  () => import("./ConsultaDocumentosTab").then((m) => ({ default: m.ConsultaDocumentosTab })),
  { loading: () => <div className="text-center py-12 text-gray-500 text-sm">Carregando documentos...</div> },
);

const ConsultaFotosTab = dynamic(
  () => import("./ConsultaFotosTab").then((m) => ({ default: m.ConsultaFotosTab })),
  { loading: () => <div className="text-center py-12 text-gray-500 text-sm">Carregando fotos...</div> },
);

const ConsultaFinalizarModal = dynamic(
  () => import("./ConsultaFinalizarModal").then((m) => ({ default: m.ConsultaFinalizarModal })),
);

const MemedPrescricao = dynamic(() => import("./MemedPrescricao"), { ssr: false });

interface Props {
  consulta: Consulta;
  /** true quando page.tsx já chamou consultas.get (evita GET duplicado). */
  detailPreloaded?: boolean;
  onBack: () => void;
  onSelectConsulta: (c: Consulta) => void;
  onListRefresh: () => void | Promise<void>;
}

export function ConsultaDetailShell({ consulta, detailPreloaded = false, onBack, onSelectConsulta, onListRefresh }: Props) {
  const [selected, setSelected] = useState(consulta);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);
  const [tab, setTab] = useState<TabId>("atendimento");
  const [protocolos, setProtocolos] = useState<Protocolo[]>([]);
  const [anamnese, setAnamnese] = useState<Anamnese>(EMPTY_ANAMNESE);
  const [anamneseDraft, setAnamneseDraft] = useState<Anamnese>(EMPTY_ANAMNESE);
  const [evolucoes, setEvolucoes] = useState<Evolucao[]>([]);
  const [historico, setHistorico] = useState<Consulta[]>([]);
  const [prescricoes, setPrescricoes] = useState<PrescricaoMemedItem[]>([]);
  const [observacoes, setObservacoes] = useState("");
  const [observacoesDraft, setObservacoesDraft] = useState("");
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
  const [profissionaisDisponiveis, setProfissionaisDisponiveis] = useState<{id: number; nome?: string; name?: string}[]>([]);
  const memedRef = useRef<MemedPrescricaoHandle>(null);
  const [memedBusy, setMemedBusy] = useState(false);
  const [locaisAtendimento, setLocaisAtendimento] = useState<LocalAtendimentoItem[]>([]);
  const [finalizarForm, setFinalizarForm] = useState({
    payment_method: "CASH",
    mark_as_paid: false,
    amount: "",
    local_atendimento: "" as number | "",
  });
  const [fotosToolbar, setFotosToolbar] = useState<ReactNode | null>(null);
  const [prescricoesRefresh, setPrescricoesRefresh] = useState(0);
  const [evolucaoForm, setEvolucaoForm] = useState({
    descricao: "",
    procedimento_realizado: "",
    produtos_utilizados: "",
    orientacoes: "",
    satisfacao: "",
  });

  const formatData = (d?: string | null) =>
    d ? formatClinicaDateTime(new Date(d)) : "—";

  const procedimentosRealizados = consultaProcedimentos(selected);

  const printMeta: ConsultaPrintMeta = {
    patientName: selected.patient_name,
    professionalName: selected.professional_name,
    procedureName: consultaProcedimentosNomes(selected),
    consultaId: selected.id,
    dataConsulta: formatData(selected.data_inicio),
  };

  const lastLoadedIdRef = useRef<number | null>(null);
  const loadingDetalheRef = useRef(false);
  const loadedTabsRef = useRef<Set<TabId>>(new Set());
  const [tabLoading, setTabLoading] = useState(false);

  const loadTabData = useCallback(async (tabId: TabId, c: Consulta, force = false) => {
    if (!force && loadedTabsRef.current.has(tabId)) return;

    if (tabId === "produtos" || tabId === "documentos" || tabId === "fotos") {
      loadedTabsRef.current.add(tabId);
      return;
    }

    setTabLoading(true);
    const patientId = c.patient;
    try {
      switch (tabId) {
        case "atendimento": {
          const prots = await ClinicaBelezaAPI.getList<Protocolo>("/protocolos/", {
            procedure: c.procedure,
          }).catch(() => []);
          setProtocolos(Array.isArray(prots) ? prots : []);
          break;
        }
        case "anamnese": {
          const anam = await ClinicaBelezaAPI.anamnese.get(patientId).catch(() => EMPTY_ANAMNESE);
          const anamMerged = { ...EMPTY_ANAMNESE, ...anam };
          setAnamnese(anamMerged);
          setAnamneseDraft(anamMerged);
          break;
        }
        case "evolucao": {
          const evol = await ClinicaBelezaAPI.consultas.evolucoes.list(c.id).catch(() => []);
          setEvolucoes(Array.isArray(evol) ? evol : []);
          break;
        }
        case "historico": {
          const histPromise =
            historico.length > 0 && !force
              ? Promise.resolve(historico)
              : fetchHistoricoPaciente(patientId);
          const [hist, anam, presc] = await Promise.all([
            histPromise,
            ClinicaBelezaAPI.anamnese.get(patientId).catch(() => EMPTY_ANAMNESE),
            ClinicaBelezaAPI.memed.listarPrescricoesPaciente(patientId).catch(() => []),
          ]);
          setHistorico(Array.isArray(hist) ? hist : []);
          const anamMerged = { ...EMPTY_ANAMNESE, ...anam };
          setAnamnese(anamMerged);
          setAnamneseDraft(anamMerged);
          setPrescricoes(Array.isArray(presc) ? presc : []);
          break;
        }
      }
      loadedTabsRef.current.add(tabId);
    } catch (e) {
      logger.warn(`Erro ao carregar aba ${tabId}:`, e);
    } finally {
      setTabLoading(false);
    }
  }, [historico]);

  const loadDetalhes = useCallback(async (c: Consulta, opts?: { detailPreloaded?: boolean }) => {
    if (loadingDetalheRef.current && lastLoadedIdRef.current === c.id) return;
    loadingDetalheRef.current = true;
    lastLoadedIdRef.current = c.id;
    loadedTabsRef.current = new Set();

    setLoadingDetalhe(true);
    setSelected(c);
    setEditAtendimento(false);
    setEditAnamnese(false);
    setEditEvolucao(false);
    setProtocoloPreview(null);
    setProtocoloPendingId(null);
    const obs = c.observacoes_gerais || c.protocolo_notas || "";
    setObservacoes(obs);
    setObservacoesDraft(obs);

    if (c.id !== consulta.id) {
      onSelectConsulta(c);
    }

    try {
      let consultaAtual = c;
      if (!opts?.detailPreloaded) {
        const fresh = await ClinicaBelezaAPI.consultas.get(c.id).catch(() => null);
        consultaAtual = fresh ? { ...c, ...fresh } : c;
        setSelected(consultaAtual);
      }

      const hist = await fetchHistoricoPaciente(consultaAtual.patient).catch(() => []);
      const histList = Array.isArray(hist) ? hist : [];
      setHistorico(histList);
      const temHistoricoAnterior = histList.length > 1;
      const initialTab: TabId =
        consultaAtual.status === "SCHEDULED" && temHistoricoAnterior ? "historico" : "atendimento";
      setTab(initialTab);

      if (initialTab === "historico") {
        loadedTabsRef.current.add("historico");
        const [anam, presc] = await Promise.all([
          ClinicaBelezaAPI.anamnese.get(consultaAtual.patient).catch(() => EMPTY_ANAMNESE),
          ClinicaBelezaAPI.memed.listarPrescricoesPaciente(consultaAtual.patient).catch(() => []),
        ]);
        const anamMerged = { ...EMPTY_ANAMNESE, ...anam };
        setAnamnese(anamMerged);
        setAnamneseDraft(anamMerged);
        setPrescricoes(Array.isArray(presc) ? presc : []);
      } else {
        await loadTabData(initialTab, consultaAtual, true);
      }
    } catch (e) {
      logger.warn("Erro ao carregar detalhes da consulta:", e);
    } finally {
      loadingDetalheRef.current = false;
      setLoadingDetalhe(false);
    }
  }, [onSelectConsulta, consulta.id, loadTabData]);

  const refreshConsulta = useCallback(async () => {
    try {
      const fresh = await ClinicaBelezaAPI.consultas.get(selected.id);
      setSelected((prev) => ({ ...prev, ...fresh }));
    } catch (e) {
      logger.warn("Erro ao atualizar consulta:", e);
    }
  }, [selected.id]);

  useEffect(() => {
    if (lastLoadedIdRef.current === consulta.id) return;
    loadDetalhes(consulta, { detailPreloaded });
  }, [consulta.id, detailPreloaded, loadDetalhes, consulta]);

  useEffect(() => {
    if (loadingDetalhe) return;
    void loadTabData(tab, selected);
  }, [tab, selected.id, loadingDetalhe, loadTabData, selected]);

  const salvarObservacoes = async () => {
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.update(selected.id, { observacoes_gerais: observacoesDraft });
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
      const updated = await ClinicaBelezaAPI.consultas.aplicarProtocolo(selected.id, protocoloPendingId);
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
      setEvolucaoForm({ descricao: "", procedimento_realizado: "", produtos_utilizados: "", orientacoes: "", satisfacao: "" });
      setEditEvolucao(false);
    } catch {
      alert("Erro ao registrar evolução.");
    } finally {
      setSaving(false);
    }
  };

  const iniciarConsulta = async (professionalId?: number) => {
    // Se consulta sem profissional e nenhum foi informado, pedir
    if (!selected.professional && !professionalId) {
      try {
        const res = await clinicaBelezaFetch('/professionals/');
        if (res.ok) {
          const json = await res.json();
          const profs = json.results || json;
          setProfissionaisDisponiveis(Array.isArray(profs) ? profs : []);
        }
      } catch { /* fallback empty */ }
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
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao iniciar consulta.");
    } finally {
      setIniciando(false);
    }
  };

  const valorPagamentoConsulta = (c: Consulta) => {
    const total = Number(c.valor_pagamento ?? 0);
    if (total > 0) return total;
    const taxa = Number(c.valor_consulta ?? 0);
    const procs = Number(c.valor_procedimentos ?? 0);
    return taxa + procs;
  };

  useEffect(() => {
    ClinicaBelezaAPI.locaisAtendimento.list()
      .then(setLocaisAtendimento)
      .catch((e) => logger.warn("Erro ao carregar locais de atendimento:", e));
  }, []);

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
      const updated = await ClinicaBelezaAPI.consultas.finalizar(selected.id, {
        payment_method: finalizarForm.payment_method,
        mark_as_paid: finalizarForm.mark_as_paid,
        amount: finalizarForm.amount || valorPagamentoConsulta(selected) || undefined,
        local_atendimento: finalizarForm.local_atendimento || undefined,
      }) as Consulta & { error?: string };
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
      alert(e instanceof Error ? e.message : "Erro ao finalizar consulta.");
    } finally {
      setFinalizando(false);
    }
  };

  const recarregarPrescricoes = useCallback(async () => {
    try {
      const presc = await ClinicaBelezaAPI.memed.listarPrescricoesPaciente(selected.patient);
      setPrescricoes(Array.isArray(presc) ? presc : []);
      setPrescricoesRefresh((n) => n + 1);
    } catch (e) {
      logger.warn("Erro ao recarregar prescrições:", e);
    }
  }, [selected.patient]);

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

  const podeIniciar = selected.status === "SCHEDULED";
  const podeFinalizar = selected.status === "IN_PROGRESS";
  const consultaConcluida = consultaEstaConcluida(selected);
  const podeExcluir = !consultaConcluida;
  const consultaAtiva = selected.status === "IN_PROGRESS";
  const consultaFinalizada = consultaConcluida;

  const tabs: { id: TabId; label: string; icon: typeof FileText }[] = [
    { id: "atendimento", label: "Atendimento", icon: ClipboardList },
    { id: "produtos", label: "Produtos", icon: Package },
    { id: "documentos", label: "Documentos", icon: FolderOpen },
    { id: "anamnese", label: "Anamnese", icon: FileText },
    { id: "evolucao", label: "Evolução", icon: Activity },
    { id: "fotos", label: "Fotos", icon: Camera },
    { id: "historico", label: "Histórico", icon: History },
  ];

  const tabsConsultaFinalizada: TabId[] = [
    "atendimento",
    "produtos",
    "documentos",
    "anamnese",
    "evolucao",
    "fotos",
  ];
  const temHistoricoAnterior = historico.length > 1;
  const visibleTabs = (consultaFinalizada
    ? tabs.filter((t) => tabsConsultaFinalizada.includes(t.id))
    : tabs
  ).filter((t) => t.id !== "historico" || temHistoricoAnterior);

  const resetTabEdits = () => {
    setEditAtendimento(false);
    setEditAnamnese(false);
    setEditEvolucao(false);
    setProtocoloPreview(null);
  };

  useEffect(() => {
    if (tab !== "fotos") setFotosToolbar(null);
  }, [tab]);

  useEffect(() => {
    if (tab === "historico" && !temHistoricoAnterior) {
      setTab("atendimento");
    }
  }, [tab, temHistoricoAnterior]);

  const headerExtraActions = consultaAtiva ? (
    <>
      <button
        type="button"
        onClick={abrirFinalizarModal}
        className="inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-lg text-white text-xs sm:text-sm font-medium"
        style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
      >
        <CheckCircle2 size={15} />
        <span className="hidden sm:inline">Finalizar consulta</span>
        <span className="sm:hidden">Finalizar</span>
      </button>
      {podeExcluir && (
        <button
          type="button"
          onClick={excluirConsulta}
          className="inline-flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
        >
          <Trash2 size={15} />
          <span className="hidden sm:inline">Excluir</span>
        </button>
      )}
    </>
  ) : null;

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={toUpperCase(selected.patient_name)}
        subtitle={`${consultaProcedimentosNomes(selected)} · ${toUpperCase(selected.professional_name)}`}
        onBack={onBack}
        toolbarActions={tab === "fotos" ? fotosToolbar : undefined}
        extraActions={headerExtraActions}
      />
      <div className="min-h-full bg-[#f7f2f4] dark:bg-gray-950 flex flex-col">
        <div className="px-4 md:px-6 pt-2 pb-4 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
          {!consultaAtiva && (
            <>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-600 dark:text-gray-400">
                <span>Agendado: {formatData(selected.appointment_date)}</span>
                <span>Início: {formatData(selected.data_inicio)}</span>
                <span>Fim: {formatData(selected.data_fim)}</span>
                <span>Total: {formatCurrency(valorPagamentoConsulta(selected))}</span>
                {procedimentosRealizados.length > 0 && (
                  <span>
                    Procedimentos:{" "}
                    <strong className="text-gray-800 dark:text-gray-200 uppercase">
                      {procedimentosRealizados
                        .map((p) => `${toUpperCase(p.nome)} (${formatCurrency(p.valor)})`)
                        .join(" · ")}
                    </strong>
                  </span>
                )}
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 uppercase">
                  {CLINICA_CONSULTA_STATUS_LABEL[selected.status] || toUpperCase(selected.status)}
                </span>
                {selected.protocol_name && (
                  <span>Protocolo: <strong className="text-gray-800 dark:text-gray-200 uppercase">{toUpperCase(selected.protocol_name)}</strong></span>
                )}
                {selected.local_atendimento_name && (
                  <span>Local: <strong className="text-gray-800 dark:text-gray-200 uppercase">{toUpperCase(selected.local_atendimento_name)}</strong></span>
                )}
                <span>
                  Convênio: <strong className="text-gray-800 dark:text-gray-200 uppercase">{toUpperCase(selected.convenio_name || "Particular")}</strong>
                </span>
                <div className="ml-auto flex flex-wrap gap-2">
                  {podeIniciar && (
                    <button type="button" onClick={iniciarConsulta} disabled={iniciando} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium disabled:opacity-50" style={{ backgroundColor: "#2563eb" }}>
                      <Play size={16} />
                      {iniciando ? "Iniciando…" : "Iniciar consulta"}
                    </button>
                  )}
                  {podeFinalizar && (
                    <button type="button" onClick={abrirFinalizarModal} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium" style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}>
                      <CheckCircle2 size={16} />
                      Finalizar consulta
                    </button>
                  )}
                  {podeExcluir && (
                    <button type="button" onClick={excluirConsulta} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20">
                      <Trash2 size={16} />
                      Excluir
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
          <div className={`flex flex-wrap gap-2 ${consultaAtiva ? "mt-0" : "mt-4"}`}>
            {visibleTabs.map(({ id, label, icon: Icon }) => {
              const disabled = !consultaAtiva && !consultaFinalizada && id !== "historico";
              return (
                <Fragment key={id}>
                  <button
                    type="button"
                    onClick={() => { if (!disabled) { setTab(id); resetTabEdits(); } }}
                    disabled={disabled}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${tab === id ? "text-white" : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300"}`}
                    style={tab === id ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
                  >
                    <Icon size={16} />
                    {label}
                  </button>
                  {id === "evolucao" && consultaAtiva && selected.exige_termo_consentimento && (
                    <ConsultaTermoConsentimentoButton
                      consultaId={selected.id}
                      exigeTermo={selected.exige_termo_consentimento}
                      onUpdated={refreshConsulta}
                    />
                  )}
                </Fragment>
              );
            })}
          </div>
        </div>
        {consultaAtiva && (
          <MemedPrescricao
            ref={memedRef}
            consultaId={selected.id}
            professionalId={selected.professional ?? null}
            patientId={selected.patient}
            patientName={selected.patient_name}
            onPrescricaoRegistrada={recarregarPrescricoes}
          />
        )}
        <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
          {loadingDetalhe || tabLoading ? (
            <div className="text-center py-16 text-gray-500">
              {loadingDetalhe ? "Carregando consulta..." : "Carregando aba..."}
            </div>
          ) : !consultaAtiva && !consultaFinalizada && tab !== "historico" ? (
            <div className="text-center py-16">
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                Consulta aguardando início. O profissional deve clicar em <strong>&quot;Iniciar consulta&quot;</strong> para habilitar o atendimento.
              </p>
            </div>
          ) : (
            <>
              {tab === "produtos" && (
                <ConsultaProdutosTab
                  consultaId={selected.id}
                  somenteLeitura={consultaFinalizada}
                  printMeta={printMeta}
                  onItensChanged={refreshConsulta}
                />
              )}
              {tab === "atendimento" && (
                <ConsultaAtendimentoTab
                  protocolos={consultaFinalizada ? [] : protocolos}
                  protocoloPreview={protocoloPreview}
                  editAtendimento={consultaFinalizada ? false : editAtendimento}
                  observacoes={observacoes}
                  observacoesDraft={observacoesDraft}
                  saving={saving}
                  printMeta={printMeta}
                  protocolName={selected.protocol_name}
                  procedimentosRealizados={procedimentosRealizados}
                  consultaFinalizada={consultaFinalizada}
                  onSelectProtocolo={consultaFinalizada ? () => {} : selecionarProtocolo}
                  onConfirmProtocolo={confirmarProtocolo}
                  onCancelProtocolo={() => { setProtocoloPreview(null); setProtocoloPendingId(null); }}
                  onStartEdit={consultaFinalizada ? () => {} : () => { setObservacoesDraft(observacoes); setEditAtendimento(true); }}
                  onCancelEdit={() => { setObservacoesDraft(observacoes); setEditAtendimento(false); }}
                  onChangeDraft={setObservacoesDraft}
                  onSave={salvarObservacoes}
                />
              )}
              {tab === "anamnese" && (
                <ConsultaAnamneseTab
                  anamnese={anamnese}
                  anamneseDraft={anamneseDraft}
                  editAnamnese={consultaFinalizada ? false : editAnamnese}
                  saving={saving}
                  printMeta={printMeta}
                  onStartEdit={consultaFinalizada ? () => {} : () => { setAnamneseDraft(anamnese); setEditAnamnese(true); }}
                  onCancelEdit={() => { setAnamneseDraft(anamnese); setEditAnamnese(false); }}
                  onChangeDraft={setAnamneseDraft}
                  onSave={salvarAnamnese}
                />
              )}
              {tab === "evolucao" && (
                <ConsultaEvolucaoTab
                  evolucoes={evolucoes}
                  editEvolucao={consultaFinalizada ? false : editEvolucao}
                  evolucaoForm={evolucaoForm}
                  saving={saving}
                  formatData={formatData}
                  printMeta={printMeta}
                  onStartEdit={consultaFinalizada ? () => {} : () => setEditEvolucao(true)}
                  onCancelEdit={() => {
                    setEditEvolucao(false);
                    setEvolucaoForm({ descricao: "", procedimento_realizado: "", produtos_utilizados: "", orientacoes: "", satisfacao: "" });
                  }}
                  onChangeForm={setEvolucaoForm}
                  onSave={salvarEvolucao}
                />
              )}
              {tab === "fotos" && (
                <ConsultaFotosTab
                  consultaId={selected.id}
                  permiteEnviar={consultaAtiva}
                  ativa={tab === "fotos" && consultaAtiva}
                  onToolbarChange={setFotosToolbar}
                />
              )}
              {tab === "historico" && (
                <ConsultaHistoricoTab
                  historico={historico}
                  selectedId={selected.id}
                  consultaId={selected.id}
                  anamnese={anamnese}
                  prescricoes={prescricoes}
                  observacoesAtual={observacoes}
                  protocoloNotasAtual={selected.protocolo_notas}
                  formatData={formatData}
                  printMeta={printMeta}
                  onSelect={loadDetalhes}
                />
              )}
              {tab === "documentos" && (
                <ConsultaDocumentosTab
                  consultaId={selected.id}
                  consultaAtiva={consultaAtiva}
                  professionalId={selected.professional}
                  onUsarMemed={abrirMemed}
                  refreshPrescricoes={prescricoesRefresh}
                />
              )}
            </>
          )}
        </div>
      </div>

      <ConsultaFinalizarModal
        open={showFinalizarModal}
        finalizando={finalizando}
        form={finalizarForm}
        valorConsulta={selected.valor_consulta}
        valorProcedimentos={selected.valor_procedimentos}
        locais={locaisAtendimento}
        onClose={() => setShowFinalizarModal(false)}
        onChange={setFinalizarForm}
        onConfirm={finalizarConsulta}
      />

      {showProfessionalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-sm">
            <div className="px-5 py-4 border-b border-gray-200 dark:border-neutral-700">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                Selecione o Profissional
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Este agendamento não possui profissional. Informe quem realizará o atendimento.
              </p>
            </div>
            <div className="p-4 max-h-60 overflow-y-auto space-y-2">
              {profissionaisDisponiveis.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    setShowProfessionalModal(false);
                    iniciarConsulta(p.id);
                  }}
                  className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
                >
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {p.nome || p.name}
                  </span>
                </button>
              ))}
              {profissionaisDisponiveis.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">Nenhum profissional cadastrado.</p>
              )}
            </div>
            <div className="px-5 py-3 border-t border-gray-200 dark:border-neutral-700">
              <button
                type="button"
                onClick={() => setShowProfessionalModal(false)}
                className="w-full px-4 py-2 text-sm text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

    </>
  );
}
