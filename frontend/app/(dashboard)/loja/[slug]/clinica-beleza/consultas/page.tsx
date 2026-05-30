"use client";

/**
 * Consultas — Clínica da Beleza
 * Lista simplificada; consulta selecionada ocupa a página inteira com preview antes de editar.
 */

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  ClipboardList,
  History,
  FileText,
  Activity,
  Save,
  Pencil,
  X,
  ChevronRight,
} from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { logger } from "@/lib/logger";

interface Consulta {
  id: number;
  patient: number;
  procedure: number;
  patient_name: string;
  professional_name: string;
  procedure_name: string;
  protocol?: number | null;
  protocol_name?: string | null;
  status: string;
  data_inicio?: string | null;
  data_fim?: string | null;
  observacoes_gerais?: string;
  protocolo_notas?: string;
  valor_consulta: string | number;
  appointment_date?: string;
  total_evolucoes: number;
}

interface Protocolo {
  id: number;
  nome: string;
  procedure: number;
  descricao?: string;
  preparacao?: string;
  execucao?: string;
  pos_procedimento?: string;
  materiais_necessarios?: string;
}

interface Anamnese {
  queixa_principal: string;
  historico_medico: string;
  medicamentos_uso: string;
  alergias: string;
  condicoes_clinicas: string;
  tipo_pele: string;
  pressao_arterial: string;
  peso: string | number | null;
  altura: string | number | null;
  observacoes: string;
}

interface Evolucao {
  id: number;
  descricao: string;
  procedimento_realizado: string;
  produtos_utilizados: string;
  orientacoes: string;
  protocolo_snapshot: string;
  satisfacao?: number | null;
  created_at: string;
  professional_name?: string;
}

const EMPTY_ANAMNESE: Anamnese = {
  queixa_principal: "",
  historico_medico: "",
  medicamentos_uso: "",
  alergias: "",
  condicoes_clinicas: "",
  tipo_pele: "",
  pressao_arterial: "",
  peso: "",
  altura: "",
  observacoes: "",
};

const ANAMNESE_FIELDS = [
  ["queixa_principal", "Queixa principal"],
  ["historico_medico", "Histórico médico"],
  ["medicamentos_uso", "Medicamentos em uso"],
  ["alergias", "Alergias"],
  ["condicoes_clinicas", "Condições clínicas"],
  ["tipo_pele", "Tipo de pele"],
  ["pressao_arterial", "Pressão arterial"],
  ["observacoes", "Observações"],
] as const;

type TabId = "atendimento" | "anamnese" | "evolucao" | "historico";

function PreviewBlock({
  label,
  value,
  empty = "—",
  mono,
}: {
  label: string;
  value?: string | null;
  empty?: string;
  mono?: boolean;
}) {
  const text = (value ?? "").trim();
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <div
        className={`rounded-lg bg-gray-50 dark:bg-neutral-900/60 border border-gray-100 dark:border-neutral-700 px-3 py-2.5 text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap min-h-[2.5rem] ${
          mono ? "font-mono text-xs" : ""
        }`}
      >
        {text || empty}
      </div>
    </div>
  );
}

export default function ConsultasPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  useClinicaBelezaDark();

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
  const [observacoes, setObservacoes] = useState("");
  const [observacoesDraft, setObservacoesDraft] = useState("");
  const [saving, setSaving] = useState(false);

  const [editAtendimento, setEditAtendimento] = useState(false);
  const [editAnamnese, setEditAnamnese] = useState(false);
  const [editEvolucao, setEditEvolucao] = useState(false);
  const [protocoloPreview, setProtocoloPreview] = useState<Protocolo | null>(null);
  const [protocoloPendingId, setProtocoloPendingId] = useState<number | null>(null);

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
      const [anam, evol, hist, prots] = await Promise.all([
        ClinicaBelezaAPI.anamnese.get(consulta.patient),
        ClinicaBelezaAPI.consultas.evolucoes.list(consulta.id),
        ClinicaBelezaAPI.consultas.historicoCliente(consulta.patient),
        ClinicaBelezaAPI.get("/protocolos/", { procedure: consulta.procedure }),
      ]);
      const anamMerged = { ...EMPTY_ANAMNESE, ...anam };
      setAnamnese(anamMerged);
      setAnamneseDraft(anamMerged);
      setEvolucoes(Array.isArray(evol) ? evol : []);
      setHistorico(Array.isArray(hist) ? hist : []);
      setProtocolos(Array.isArray(prots) ? prots : []);
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

  const tabs: { id: TabId; label: string; icon: typeof FileText }[] = [
    { id: "atendimento", label: "Atendimento", icon: ClipboardList },
    { id: "anamnese", label: "Anamnese", icon: FileText },
    { id: "evolucao", label: "Evolução", icon: Activity },
    { id: "historico", label: "Histórico", icon: History },
  ];

  const formatData = (d?: string | null) =>
    d ? new Date(d).toLocaleString("pt-BR") : "—";

  /* ── Consulta em tela cheia ── */
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
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-600 dark:text-gray-400">
              <span>{formatData(selected.data_inicio || selected.appointment_date)}</span>
              <span>{formatCurrency(Number(selected.valor_consulta))}</span>
              {selected.protocol_name && (
                <span>Protocolo: <strong className="text-gray-800 dark:text-gray-200">{selected.protocol_name}</strong></span>
              )}
            </div>
            <div className="flex flex-wrap gap-2 mt-4">
              {tabs.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => {
                    setTab(id);
                    setEditAtendimento(false);
                    setEditAnamnese(false);
                    setEditEvolucao(false);
                    setProtocoloPreview(null);
                  }}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    tab === id ? "text-white" : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300"
                  }`}
                  style={tab === id ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
                >
                  <Icon size={16} />
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
            {loadingDetalhe ? (
              <div className="text-center py-16 text-gray-500">Carregando consulta...</div>
            ) : (
              <>
                {tab === "atendimento" && (
                  <div className="space-y-5">
                    {protocolos.length > 0 && !editAtendimento && (
                      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4">
                        <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Protocolo cadastrado</p>
                        {!protocoloPreview ? (
                          <select
                            className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 text-sm"
                            value=""
                            onChange={(e) => {
                              const pid = Number(e.target.value);
                              if (pid) selecionarProtocolo(pid);
                            }}
                            disabled={saving}
                          >
                            <option value="">Selecionar para ver preview...</option>
                            {protocolos.map((p) => (
                              <option key={p.id} value={p.id}>{p.nome}</option>
                            ))}
                          </select>
                        ) : (
                          <div className="space-y-3">
                            <p className="font-semibold text-gray-900 dark:text-gray-100">{protocoloPreview.nome}</p>
                            {protocoloPreview.preparacao && <PreviewBlock label="Preparação" value={protocoloPreview.preparacao} />}
                            {protocoloPreview.execucao && <PreviewBlock label="Execução" value={protocoloPreview.execucao} mono />}
                            {protocoloPreview.pos_procedimento && <PreviewBlock label="Pós-procedimento" value={protocoloPreview.pos_procedimento} />}
                            {protocoloPreview.materiais_necessarios && <PreviewBlock label="Materiais" value={protocoloPreview.materiais_necessarios} />}
                            <div className="flex gap-2 pt-1">
                              <button
                                type="button"
                                onClick={confirmarProtocolo}
                                disabled={saving}
                                className="px-4 py-2 rounded-lg text-white text-sm disabled:opacity-50"
                                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                              >
                                Aplicar protocolo
                              </button>
                              <button
                                type="button"
                                onClick={() => { setProtocoloPreview(null); setProtocoloPendingId(null); }}
                                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm"
                              >
                                Cancelar
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">Notas do atendimento</h3>
                        {!editAtendimento ? (
                          <button
                            type="button"
                            onClick={() => { setObservacoesDraft(observacoes); setEditAtendimento(true); }}
                            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700"
                          >
                            <Pencil size={14} />
                            Editar
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => { setObservacoesDraft(observacoes); setEditAtendimento(false); }}
                            className="inline-flex items-center gap-1.5 text-sm text-gray-500"
                          >
                            <X size={14} />
                            Cancelar
                          </button>
                        )}
                      </div>
                      {!editAtendimento ? (
                        <PreviewBlock label="Conteúdo" value={observacoes} empty="Nenhuma anotação registrada." mono />
                      ) : (
                        <>
                          <textarea
                            rows={12}
                            value={observacoesDraft}
                            onChange={(e) => setObservacoesDraft(e.target.value)}
                            className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 font-mono text-sm"
                          />
                          <button
                            type="button"
                            onClick={salvarObservacoes}
                            disabled={saving}
                            className="mt-3 flex items-center gap-2 px-4 py-2 rounded-lg text-white disabled:opacity-50"
                            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                          >
                            <Save size={18} />
                            {saving ? "Salvando..." : "Salvar atendimento"}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {tab === "anamnese" && (
                  <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">Anamnese do cliente</h3>
                      {!editAnamnese ? (
                        <button
                          type="button"
                          onClick={() => { setAnamneseDraft(anamnese); setEditAnamnese(true); }}
                          className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700"
                        >
                          <Pencil size={14} />
                          Editar
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => { setAnamneseDraft(anamnese); setEditAnamnese(false); }}
                          className="inline-flex items-center gap-1.5 text-sm text-gray-500"
                        >
                          <X size={14} />
                          Cancelar
                        </button>
                      )}
                    </div>
                    {!editAnamnese ? (
                      <>
                        {ANAMNESE_FIELDS.map(([field, label]) => (
                          <PreviewBlock key={field} label={label} value={String(anamnese[field] ?? "")} />
                        ))}
                        <div className="grid grid-cols-2 gap-4">
                          <PreviewBlock label="Peso (kg)" value={anamnese.peso != null && anamnese.peso !== "" ? String(anamnese.peso) : ""} />
                          <PreviewBlock label="Altura (m)" value={anamnese.altura != null && anamnese.altura !== "" ? String(anamnese.altura) : ""} />
                        </div>
                      </>
                    ) : (
                      <>
                        {ANAMNESE_FIELDS.map(([field, label]) => (
                          <div key={field}>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
                            <textarea
                              rows={field === "queixa_principal" ? 3 : 2}
                              value={String(anamneseDraft[field] ?? "")}
                              onChange={(e) => setAnamneseDraft((prev) => ({ ...prev, [field]: e.target.value }))}
                              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 text-sm"
                            />
                          </div>
                        ))}
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-sm font-medium mb-1">Peso (kg)</label>
                            <input
                              type="number"
                              step="0.01"
                              value={anamneseDraft.peso ?? ""}
                              onChange={(e) => setAnamneseDraft((prev) => ({ ...prev, peso: e.target.value }))}
                              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Altura (m)</label>
                            <input
                              type="number"
                              step="0.01"
                              value={anamneseDraft.altura ?? ""}
                              onChange={(e) => setAnamneseDraft((prev) => ({ ...prev, altura: e.target.value }))}
                              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                            />
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={salvarAnamnese}
                          disabled={saving}
                          className="flex items-center gap-2 px-4 py-2 rounded-lg text-white disabled:opacity-50"
                          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                        >
                          <Save size={18} />
                          Salvar anamnese
                        </button>
                      </>
                    )}
                  </div>
                )}

                {tab === "evolucao" && (
                  <div className="space-y-5">
                    {evolucoes.length > 0 && (
                      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6 space-y-4">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">Registros desta consulta</h3>
                        {evolucoes.map((ev) => (
                          <div key={ev.id} className="rounded-lg border border-gray-100 dark:border-neutral-700 p-4 space-y-2">
                            <p className="text-xs text-gray-500">
                              {formatData(ev.created_at)}
                              {ev.professional_name ? ` · ${ev.professional_name}` : ""}
                            </p>
                            {ev.descricao && <PreviewBlock label="Evolução" value={ev.descricao} />}
                            {ev.procedimento_realizado && <PreviewBlock label="Procedimento" value={ev.procedimento_realizado} />}
                            {ev.produtos_utilizados && <PreviewBlock label="Produtos" value={ev.produtos_utilizados} />}
                            {ev.orientacoes && <PreviewBlock label="Orientações" value={ev.orientacoes} />}
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">Nova evolução</h3>
                        {!editEvolucao ? (
                          <button
                            type="button"
                            onClick={() => setEditEvolucao(true)}
                            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg text-white"
                            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                          >
                            <Pencil size={14} />
                            Registrar
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => {
                              setEditEvolucao(false);
                              setEvolucaoForm({ descricao: "", procedimento_realizado: "", produtos_utilizados: "", orientacoes: "", satisfacao: "" });
                            }}
                            className="inline-flex items-center gap-1.5 text-sm text-gray-500"
                          >
                            <X size={14} />
                            Cancelar
                          </button>
                        )}
                      </div>
                      {!editEvolucao ? (
                        <p className="text-sm text-gray-500">Clique em Registrar para adicionar uma evolução nesta consulta.</p>
                      ) : (
                        <div className="space-y-3">
                          <textarea placeholder="Evolução / observações clínicas" rows={3} value={evolucaoForm.descricao} onChange={(e) => setEvolucaoForm((f) => ({ ...f, descricao: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
                          <textarea placeholder="Procedimento realizado" rows={2} value={evolucaoForm.procedimento_realizado} onChange={(e) => setEvolucaoForm((f) => ({ ...f, procedimento_realizado: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
                          <textarea placeholder="Produtos utilizados" rows={2} value={evolucaoForm.produtos_utilizados} onChange={(e) => setEvolucaoForm((f) => ({ ...f, produtos_utilizados: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
                          <textarea placeholder="Orientações ao cliente" rows={2} value={evolucaoForm.orientacoes} onChange={(e) => setEvolucaoForm((f) => ({ ...f, orientacoes: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600" />
                          <select value={evolucaoForm.satisfacao} onChange={(e) => setEvolucaoForm((f) => ({ ...f, satisfacao: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600">
                            <option value="">Satisfação (opcional)</option>
                            {[1, 2, 3, 4, 5].map((n) => (
                              <option key={n} value={n}>{n}</option>
                            ))}
                          </select>
                          <button type="button" onClick={salvarEvolucao} disabled={saving} className="px-4 py-2 rounded-lg text-white disabled:opacity-50" style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}>
                            Confirmar evolução
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {tab === "historico" && (
                  <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6 space-y-3">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Consultas anteriores do cliente</h3>
                    {historico.length === 0 ? (
                      <p className="text-gray-500 text-sm">Nenhuma consulta anterior.</p>
                    ) : (
                      historico.map((h) => (
                        <button
                          key={h.id}
                          type="button"
                          onClick={() => h.id !== selected.id && loadDetalhes(h)}
                          disabled={h.id === selected.id}
                          className={`w-full text-left p-4 rounded-lg border transition-colors ${
                            h.id === selected.id
                              ? "border-[#8B3D52] bg-[#F5E6EA]/40 dark:bg-neutral-700 cursor-default"
                              : "border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700/50"
                          }`}
                        >
                          <div className="flex justify-between items-center gap-2">
                            <div>
                              <p className="font-medium text-gray-900 dark:text-gray-100">{h.procedure_name}</p>
                              <p className="text-xs text-gray-500 mt-0.5">
                                {formatData(h.data_inicio)}
                                {h.professional_name ? ` · ${h.professional_name}` : ""}
                              </p>
                            </div>
                            {h.id !== selected.id && <ChevronRight size={18} className="text-gray-400 shrink-0" />}
                          </div>
                          {h.total_evolucoes > 0 && (
                            <p className="text-xs text-gray-500 mt-1">{h.total_evolucoes} evolução(ões)</p>
                          )}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </>
    );
  }

  /* ── Lista (sem filtro de status) ── */
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Consultas"
        subtitle="Selecione uma consulta ou inicie pela Agenda"
      />
      <ClinicaBelezaPageContent>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
            As consultas são criadas ao alterar o status do agendamento na Agenda.
          </p>
          {loading ? (
            <div className="text-center py-16 text-gray-500">Carregando...</div>
          ) : consultas.length === 0 ? (
            <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
              Nenhuma consulta ainda. Altere o status de um agendamento na Agenda.
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
                        <td className="px-4 py-4 text-gray-400"><ChevronRight size={18} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ClinicaBelezaPanel>
          )}
      </ClinicaBelezaPageContent>
    </>
  );
}
