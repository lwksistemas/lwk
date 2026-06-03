"use client";

/**
 * Consultas — Clínica da Beleza
 * Lista simplificada; consulta selecionada ocupa a página inteira com preview antes de editar.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  ClipboardList,
  History,
  FileText,
  Activity,
  FolderOpen,
  ChevronRight,
  CheckCircle2,
  Play,
  Pill,
  FlaskConical,
  Plus,
  Trash2,
  Settings,
} from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { CLINICA_CONSULTA_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { logger } from "@/lib/logger";
import {
  type Consulta,
  type Protocolo,
  type Anamnese,
  type Evolucao,
  type TabId,
  EMPTY_ANAMNESE,
  ConsultaAtendimentoTab,
  ConsultaAnamneseTab,
  ConsultaEvolucaoTab,
  ConsultaHistoricoTab,
  ConsultaDocumentosTab,
  ConsultaFinalizarModal,
  NovaConsultaModal,
  UsarTemplateModal,
  DigitarManualModal,
  LocaisAtendimentoModal,
  MemedPrescricao,
  type MemedPrescricaoHandle,
} from "./components";
import type { DocumentoTipo } from "./components/ConsultaDocumentosTab";

export default function ConsultasPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);
  const [selected, setSelected] = useState<Consulta | null>(null);
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
  const [showNovaConsulta, setShowNovaConsulta] = useState(false);
  const [showLocaisModal, setShowLocaisModal] = useState(false);
  const [templateModalTipo, setTemplateModalTipo] = useState<DocumentoTipo | null>(null);
  const [manualModalTipo, setManualModalTipo] = useState<DocumentoTipo | null>(null);
  const [savingManualDoc, setSavingManualDoc] = useState(false);
  const [finalizando, setFinalizando] = useState(false);
  const [iniciando, setIniciando] = useState(false);
  const memedRef = useRef<MemedPrescricaoHandle>(null);
  const [memedBusy, setMemedBusy] = useState(false);
  const [finalizarForm, setFinalizarForm] = useState({
    payment_method: "CASH",
    mark_as_paid: false,
    amount: "",
  });

  const [evolucaoForm, setEvolucaoForm] = useState({
    descricao: "",
    procedimento_realizado: "",
    produtos_utilizados: "",
    orientacoes: "",
    satisfacao: "",
  });

  const loadConsultas = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.consultas.list();
      setConsultas(Array.isArray(data) ? data : []);
    } catch (e) {
      logger.warn("Erro ao carregar consultas:", e);
      setConsultas([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConsultas();
  }, [loadConsultas]);

  const loadDetalhes = useCallback(async (consulta: Consulta) => {
    setLoadingDetalhe(true);
    setSelected(consulta);
    setTab("atendimento");
    setEditAtendimento(false);
    setEditAnamnese(false);
    setEditEvolucao(false);
    setProtocoloPreview(null);
    setProtocoloPendingId(null);
    const obs = consulta.observacoes_gerais || consulta.protocolo_notas || "";
    setObservacoes(obs);
    setObservacoesDraft(obs);
    router.replace(`/loja/${slug}/clinica-beleza/consultas?id=${consulta.id}`, { scroll: false });

    try {
      const [anam, evol, hist, prots, presc] = await Promise.all([
        ClinicaBelezaAPI.anamnese.get(consulta.patient),
        ClinicaBelezaAPI.consultas.evolucoes.list(consulta.id),
        ClinicaBelezaAPI.consultas.historicoCliente(consulta.patient),
        ClinicaBelezaAPI.get("/protocolos/", { procedure: consulta.procedure }),
        ClinicaBelezaAPI.memed.listarPrescricoesPaciente(consulta.patient).catch(() => []),
      ]);
      const anamMerged = { ...EMPTY_ANAMNESE, ...anam };
      setAnamnese(anamMerged);
      setAnamneseDraft(anamMerged);
      setEvolucoes(Array.isArray(evol) ? evol : []);
      setHistorico(Array.isArray(hist) ? hist : []);
      setProtocolos(Array.isArray(prots) ? prots : []);
      setPrescricoes(Array.isArray(presc) ? presc : []);
    } catch (e) {
      logger.warn("Erro ao carregar detalhes da consulta:", e);
    } finally {
      setLoadingDetalhe(false);
    }
  }, [router, slug]);

  useEffect(() => {
    const idParam = searchParams.get("id");
    if (!idParam || consultas.length === 0) return;
    const found = consultas.find((c) => String(c.id) === idParam);
    if (found && found.id !== selected?.id) {
      loadDetalhes(found);
    }
  }, [searchParams, consultas, selected?.id, loadDetalhes]);

  const onConsultaCriada = async (consulta: Consulta) => {
    setShowNovaConsulta(false);
    setConsultas((prev) => [consulta, ...prev]);
  };

  const voltarLista = () => {
    setSelected(null);
    setEditAtendimento(false);
    setEditAnamnese(false);
    setEditEvolucao(false);
    router.replace(`/loja/${slug}/clinica-beleza/consultas`, { scroll: false });
  };

  const salvarObservacoes = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.update(selected.id, { observacoes_gerais: observacoesDraft });
      setSelected({ ...selected, ...updated });
      setObservacoes(observacoesDraft);
      setEditAtendimento(false);
      await loadConsultas();
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
    if (!selected || !protocoloPendingId) return;
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.aplicarProtocolo(selected.id, protocoloPendingId);
      const notas = updated.protocolo_notas || observacoes;
      setSelected({ ...selected, ...updated });
      setObservacoes(notas);
      setObservacoesDraft(notas);
      setProtocoloPreview(null);
      setProtocoloPendingId(null);
      await loadConsultas();
    } catch {
      alert("Erro ao aplicar protocolo.");
    } finally {
      setSaving(false);
    }
  };

  const salvarAnamnese = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await ClinicaBelezaAPI.anamnese.save(selected.patient, anamneseDraft);
      setAnamnese(anamneseDraft);
      setEditAnamnese(false);
    } catch {
      alert("Erro ao salvar anamnese.");
    } finally {
      setSaving(false);
    }
  };

  const salvarEvolucao = async () => {
    if (!selected) return;
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

  const iniciarConsulta = async () => {
    if (!selected) return;
    if (!confirm("Iniciar atendimento? A agenda será marcada como Em atendimento.")) return;
    setIniciando(true);
    try {
      const data = await ClinicaBelezaAPI.consultas.iniciar(selected.id);
      setSelected({ ...selected, ...data });
      await loadConsultas();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao iniciar consulta.");
    } finally {
      setIniciando(false);
    }
  };

  const abrirFinalizarModal = () => {
    if (!selected) return;
    setFinalizarForm({
      payment_method: "CASH",
      mark_as_paid: false,
      amount: String(selected.valor_consulta ?? ""),
    });
    setShowFinalizarModal(true);
  };

  const finalizarConsulta = async () => {
    if (!selected) return;
    setFinalizando(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.finalizar(selected.id, {
        payment_method: finalizarForm.payment_method,
        mark_as_paid: finalizarForm.mark_as_paid,
        amount: finalizarForm.amount || selected.valor_consulta,
      });
      setSelected({ ...selected, ...updated });
      setShowFinalizarModal(false);
      await loadConsultas();
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
    if (!selected) return;
    try {
      const presc = await ClinicaBelezaAPI.memed.listarPrescricoesPaciente(selected.patient);
      setPrescricoes(Array.isArray(presc) ? presc : []);
    } catch (e) {
      logger.warn("Erro ao recarregar prescrições:", e);
    }
  }, [selected]);

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

  const podeIniciar = selected?.status === "SCHEDULED";
  const podeFinalizar = selected?.status === "IN_PROGRESS";
  const podeExcluir = selected?.status !== "COMPLETED";
  // Consulta ativa = em atendimento. Só aí pode editar/prescrever.
  const consultaAtiva = selected?.status === "IN_PROGRESS";
  // Consulta finalizada = somente leitura.
  const consultaFinalizada = selected?.status === "COMPLETED";

  const excluirConsulta = async () => {
    if (!selected) return;
    if (!confirm("Excluir esta consulta? O agendamento vinculado será cancelado.")) return;
    try {
      await ClinicaBelezaAPI.consultas.excluir(selected.id);
      setSelected(null);
      await loadConsultas();
      router.replace(`/loja/${slug}/clinica-beleza/consultas`, { scroll: false });
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao excluir consulta.");
    }
  };

  const tabs: { id: TabId; label: string; icon: typeof FileText }[] = [
    { id: "atendimento", label: "Atendimento", icon: ClipboardList },
    { id: "documentos", label: "Documentos", icon: FolderOpen },
    { id: "anamnese", label: "Anamnese", icon: FileText },
    { id: "evolucao", label: "Evolução", icon: Activity },
    { id: "historico", label: "Histórico", icon: History },
  ];

  const formatData = (d?: string | null) =>
    d ? formatClinicaDateTime(new Date(d)) : "—";

  const resetTabEdits = () => {
    setEditAtendimento(false);
    setEditAnamnese(false);
    setEditEvolucao(false);
    setProtocoloPreview(null);
  };

  if (selected) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={selected.patient_name}
          subtitle={`${selected.procedure_name} · ${selected.professional_name}`}
        />
        <div className="min-h-full bg-[#f8f9fa] dark:bg-gray-950 flex flex-col">
          <div className="px-4 md:px-6 pt-2 pb-4 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
            <button
              type="button"
              onClick={voltarLista}
              className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-3"
            >
              <ArrowLeft size={16} />
              Voltar à lista
            </button>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-600 dark:text-gray-400">
              <span>Agendado: {formatData(selected.appointment_date)}</span>
              <span>Início: {formatData(selected.data_inicio)}</span>
              <span>Fim: {formatData(selected.data_fim)}</span>
              <span>{formatCurrency(Number(selected.valor_consulta))}</span>
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300">
                {CLINICA_CONSULTA_STATUS_LABEL[selected.status] || selected.status}
              </span>
              {selected.protocol_name && (
                <span>Protocolo: <strong className="text-gray-800 dark:text-gray-200">{selected.protocol_name}</strong></span>
              )}
              {selected.local_atendimento_name && (
                <span>Local: <strong className="text-gray-800 dark:text-gray-200">{selected.local_atendimento_name}</strong></span>
              )}
              <div className="ml-auto flex flex-wrap gap-2">
                {podeIniciar && (
                  <button
                    type="button"
                    onClick={iniciarConsulta}
                    disabled={iniciando}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium disabled:opacity-50"
                    style={{ backgroundColor: "#2563eb" }}
                  >
                    <Play size={16} />
                    {iniciando ? "Iniciando…" : "Iniciar consulta"}
                  </button>
                )}
                {podeFinalizar && (
                  <button
                    type="button"
                    onClick={abrirFinalizarModal}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium"
                    style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                  >
                    <CheckCircle2 size={16} />
                    Finalizar consulta
                  </button>
                )}
                {podeExcluir && (
                  <button
                    type="button"
                    onClick={excluirConsulta}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <Trash2 size={16} />
                    Excluir
                  </button>
                )}
              </div>
            </div>
            <div className="flex flex-wrap gap-2 mt-4">
              {tabs.map(({ id, label, icon: Icon }) => {
                // Antes de iniciar: só Histórico acessível
                // Em atendimento ou finalizada: todos acessíveis (finalizada = leitura)
                const disabled = !consultaAtiva && !consultaFinalizada && id !== "historico";
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => { if (!disabled) { setTab(id); resetTabEdits(); } }}
                    disabled={disabled}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
                      tab === id ? "text-white" : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300"
                    }`}
                    style={tab === id ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
                  >
                    <Icon size={16} />
                    {label}
                  </button>
                );
              })}
              {consultaAtiva && (
                <>
                  <button
                    type="button"
                    onClick={abrirMemed}
                    disabled={memedBusy}
                    title="Abrir receituário digital na Memed"
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
                  >
                    <Pill size={16} />
                    {memedBusy ? "Carregando..." : "Receituário"}
                  </button>
                  <button
                    type="button"
                    onClick={abrirMemed}
                    disabled={memedBusy}
                    title="Solicitar exames na Memed"
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
                  >
                    <FlaskConical size={16} />
                    {memedBusy ? "Carregando..." : "Exames"}
                  </button>
                </>
              )}
            </div>
          </div>
          <MemedPrescricao
            ref={memedRef}
            consultaId={selected.id}
            professionalId={selected.professional ?? null}
            patientId={selected.patient}
            patientName={selected.patient_name}
            onPrescricaoRegistrada={recarregarPrescricoes}
          />

          <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
            {loadingDetalhe ? (
              <div className="text-center py-16 text-gray-500">Carregando consulta...</div>
            ) : !consultaAtiva && !consultaFinalizada ? (
              <div className="text-center py-16">
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  Consulta aguardando início. O profissional deve clicar em <strong>"Iniciar consulta"</strong> para habilitar o atendimento.
                </p>
              </div>
            ) : (
              <>
                {tab === "atendimento" && (
                  <ConsultaAtendimentoTab
                    protocolos={consultaFinalizada ? [] : protocolos}
                    protocoloPreview={protocoloPreview}
                    editAtendimento={consultaFinalizada ? false : editAtendimento}
                    observacoes={observacoes}
                    observacoesDraft={observacoesDraft}
                    saving={saving}
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
                    onStartEdit={consultaFinalizada ? () => {} : () => setEditEvolucao(true)}
                    onCancelEdit={() => {
                      setEditEvolucao(false);
                      setEvolucaoForm({ descricao: "", procedimento_realizado: "", produtos_utilizados: "", orientacoes: "", satisfacao: "" });
                    }}
                    onChangeForm={setEvolucaoForm}
                    onSave={salvarEvolucao}
                  />
                )}
                {tab === "historico" && (
                  <ConsultaHistoricoTab
                    historico={historico}
                    selectedId={selected.id}
                    prescricoes={prescricoes}
                    formatData={formatData}
                    onSelect={loadDetalhes}
                  />
                )}
                {tab === "documentos" && (
                  <ConsultaDocumentosTab
                    consultaId={selected.id}
                    consultaAtiva={consultaAtiva}
                    onUsarMemed={abrirMemed}
                    onUsarTemplate={(tipo) => setTemplateModalTipo(tipo)}
                    onDigitarManual={(tipo) => setManualModalTipo(tipo)}
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
          onClose={() => setShowFinalizarModal(false)}
          onChange={setFinalizarForm}
          onConfirm={finalizarConsulta}
        />

        {selected && templateModalTipo && (
          <UsarTemplateModal
            open={!!templateModalTipo}
            tipo={templateModalTipo}
            consultaId={selected.id}
            onClose={() => setTemplateModalTipo(null)}
            onSuccess={() => {
              // Documento criado com sucesso — pode recarregar dados se necessário
              setTemplateModalTipo(null);
            }}
          />
        )}

        {selected && manualModalTipo && (
          <DigitarManualModal
            open={!!manualModalTipo}
            tipo={manualModalTipo}
            saving={savingManualDoc}
            onClose={() => setManualModalTipo(null)}
            onSave={async (data) => {
              setSavingManualDoc(true);
              try {
                await ClinicaBelezaAPI.documentos.create(selected.id, {
                  tipo: data.tipo,
                  conteudo: data.conteudo,
                  titulo: data.titulo || undefined,
                });
                setManualModalTipo(null);
              } catch (e) {
                logger.warn("Erro ao salvar documento manual:", e);
                alert("Erro ao salvar documento. Tente novamente.");
              } finally {
                setSavingManualDoc(false);
              }
            }}
          />
        )}
      </>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Consultas"
        subtitle="Confirme na Agenda · inicie e finalize aqui"
        onNew={() => setShowNovaConsulta(true)}
        newLabel="Nova consulta"
        extraActions={
          <button
            type="button"
            onClick={() => setShowLocaisModal(true)}
            className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Configurar locais de atendimento"
            title="Locais de atendimento"
          >
            <Settings className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600 dark:text-gray-300" />
          </button>
        }
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        ) : consultas.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            Nenhuma consulta ainda. Confirme um agendamento na Agenda ou clique em <strong>Nova consulta</strong> para
            abrir um atendimento direto pelo cadastro do cliente.
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-neutral-900/80 text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700">
                  <tr>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Cliente</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Procedimento</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold hidden sm:table-cell">Data</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold hidden md:table-cell">Profissional</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold hidden lg:table-cell">Status</th>
                    <th className="w-12" />
                  </tr>
                </thead>
                <tbody>
                  {consultas.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => loadDetalhes(c)}
                      className="border-t border-gray-100 dark:border-neutral-700/80 hover:bg-[#F5E6EA]/40 dark:hover:bg-neutral-700/30 transition-colors cursor-pointer"
                    >
                      <td className="px-4 md:px-6 py-4 font-medium text-gray-900 dark:text-gray-100">{c.patient_name}</td>
                      <td className="px-4 md:px-6 py-4 text-gray-700 dark:text-gray-300">{c.procedure_name}</td>
                      <td className="px-4 md:px-6 py-4 hidden sm:table-cell text-gray-600 dark:text-gray-400 text-xs">
                        {formatData(c.data_inicio || c.appointment_date)}
                      </td>
                      <td className="px-4 md:px-6 py-4 hidden md:table-cell text-gray-600 dark:text-gray-400">{c.professional_name || "—"}</td>
                      <td className="px-4 md:px-6 py-4 hidden lg:table-cell">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-neutral-800 text-gray-600 dark:text-gray-400">
                          {CLINICA_CONSULTA_STATUS_LABEL[c.status] || c.status}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-gray-400"><ChevronRight size={18} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ClinicaBelezaPanel>
        )}
      </ClinicaBelezaPageContent>
      <NovaConsultaModal
        open={showNovaConsulta}
        onClose={() => setShowNovaConsulta(false)}
        onCreated={onConsultaCriada}
      />
      <LocaisAtendimentoModal
        open={showLocaisModal}
        onClose={() => setShowLocaisModal(false)}
      />
    </>
  );
}
