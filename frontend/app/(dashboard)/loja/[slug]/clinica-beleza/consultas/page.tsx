"use client";

/**
 * Consultas — Clínica da Beleza
 * Consultas são criadas automaticamente ao mudar o status na Agenda (Em Atendimento / Concluído).
 */

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ClipboardList, History, FileText, Activity, Save } from "lucide-react";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { logger } from "@/lib/logger";

const STATUS_LABEL: Record<string, string> = {
  IN_PROGRESS: "Em Atendimento",
  COMPLETED: "Concluída",
  CANCELLED: "Cancelada",
};

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

type TabId = "atendimento" | "anamnese" | "evolucao" | "historico";

export default function ConsultasPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  useClinicaBelezaDark();

  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [selected, setSelected] = useState<Consulta | null>(null);
  const [tab, setTab] = useState<TabId>("atendimento");
  const [protocolos, setProtocolos] = useState<Protocolo[]>([]);
  const [anamnese, setAnamnese] = useState<Anamnese>(EMPTY_ANAMNESE);
  const [evolucoes, setEvolucoes] = useState<Evolucao[]>([]);
  const [historico, setHistorico] = useState<Consulta[]>([]);
  const [observacoes, setObservacoes] = useState("");
  const [saving, setSaving] = useState(false);
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
      const data = await ClinicaBelezaAPI.consultas.list(
        statusFilter ? { status: statusFilter } : undefined
      );
      setConsultas(Array.isArray(data) ? data : []);
    } catch (e) {
      logger.warn("Erro ao carregar consultas:", e);
      setConsultas([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadConsultas();
  }, [loadConsultas]);

  useEffect(() => {
    const idParam = searchParams.get("id");
    if (idParam && consultas.length > 0) {
      const found = consultas.find((c) => String(c.id) === idParam);
      if (found) setSelected(found);
    }
  }, [searchParams, consultas]);

  const loadDetalhes = useCallback(async (consulta: Consulta) => {
    setSelected(consulta);
    setObservacoes(consulta.observacoes_gerais || "");
    router.replace(`/loja/${slug}/clinica-beleza/consultas?id=${consulta.id}`, { scroll: false });

    try {
      const [anam, evol, hist, prots] = await Promise.all([
        ClinicaBelezaAPI.anamnese.get(consulta.patient),
        ClinicaBelezaAPI.consultas.evolucoes.list(consulta.id),
        ClinicaBelezaAPI.consultas.historicoCliente(consulta.patient),
        ClinicaBelezaAPI.get("/protocolos/", { procedure: consulta.procedure }),
      ]);
      setAnamnese({ ...EMPTY_ANAMNESE, ...anam });
      setEvolucoes(Array.isArray(evol) ? evol : []);
      setHistorico(Array.isArray(hist) ? hist : []);
      setProtocolos(Array.isArray(prots) ? prots : []);
    } catch (e) {
      logger.warn("Erro ao carregar detalhes da consulta:", e);
    }
  }, [router, slug]);

  const salvarObservacoes = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.update(selected.id, { observacoes_gerais: observacoes });
      setSelected({ ...selected, ...updated });
      await loadConsultas();
    } catch {
      alert("Erro ao salvar observações.");
    } finally {
      setSaving(false);
    }
  };

  const aplicarProtocolo = async (protocolId: number) => {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await ClinicaBelezaAPI.consultas.aplicarProtocolo(selected.id, protocolId);
      setSelected({ ...selected, ...updated });
      setObservacoes(updated.protocolo_notas || observacoes);
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
      await ClinicaBelezaAPI.anamnese.save(selected.patient, anamnese);
      alert("Anamnese salva.");
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

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Consultas"
        subtitle="Criadas automaticamente ao alterar o status na Agenda"
      />
      <div className="min-h-full bg-[#f8f9fa] dark:bg-gray-950 p-4 md:p-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Lista */}
          <div className="lg:col-span-1 bg-white/80 dark:bg-neutral-800/80 rounded-xl shadow overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-neutral-700">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-sm"
              >
                <option value="">Todos os status</option>
                <option value="IN_PROGRESS">Em Atendimento</option>
                <option value="COMPLETED">Concluídas</option>
                <option value="CANCELLED">Canceladas</option>
              </select>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Para iniciar uma consulta, mude o agendamento para &quot;Em Atendimento&quot; na Agenda.
              </p>
            </div>
            {loading ? (
              <div className="p-6 text-center text-gray-500">Carregando...</div>
            ) : consultas.length === 0 ? (
              <div className="p-6 text-center text-gray-500 text-sm">
                Nenhuma consulta ainda. Altere o status de um agendamento na Agenda para criar.
              </div>
            ) : (
              <ul className="divide-y divide-gray-100 dark:divide-neutral-700 max-h-[70vh] overflow-y-auto">
                {consultas.map((c) => (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() => loadDetalhes(c)}
                      className={`w-full text-left p-4 hover:bg-gray-50 dark:hover:bg-neutral-700/50 transition-colors ${
                        selected?.id === c.id ? "bg-[#F5E6EA] dark:bg-neutral-700" : ""
                      }`}
                    >
                      <p className="font-semibold text-gray-900 dark:text-gray-100">{c.patient_name}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{c.procedure_name}</p>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-500">
                          {c.data_inicio ? new Date(c.data_inicio).toLocaleString("pt-BR") : "—"}
                        </span>
                        <span
                          className="text-xs px-2 py-0.5 rounded-full text-white"
                          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                        >
                          {STATUS_LABEL[c.status] || c.status}
                        </span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Detalhe */}
          <div className="lg:col-span-2 bg-white/80 dark:bg-neutral-800/80 rounded-xl shadow min-h-[480px]">
            {!selected ? (
              <div className="flex items-center justify-center h-full min-h-[480px] text-gray-500 p-8 text-center">
                Selecione uma consulta ou inicie o atendimento pela Agenda.
              </div>
            ) : (
              <>
                <div className="p-4 border-b border-gray-200 dark:border-neutral-700">
                  <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{selected.patient_name}</h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {selected.procedure_name} · {selected.professional_name} · {formatCurrency(Number(selected.valor_consulta))}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {tabs.map(({ id, label, icon: Icon }) => (
                      <button
                        key={id}
                        type="button"
                        onClick={() => setTab(id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                          tab === id
                            ? "text-white"
                            : "bg-gray-100 dark:bg-neutral-700 text-gray-700 dark:text-gray-300"
                        }`}
                        style={tab === id ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
                      >
                        <Icon size={16} />
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="p-4 md:p-6">
                  {tab === "atendimento" && (
                    <div className="space-y-4">
                      {protocolos.length > 0 && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Protocolo cadastrado
                          </label>
                          <select
                            className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                            value={selected.protocol ?? ""}
                            onChange={(e) => {
                              const pid = Number(e.target.value);
                              if (pid) aplicarProtocolo(pid);
                            }}
                            disabled={saving}
                          >
                            <option value="">Selecionar protocolo...</option>
                            {protocolos.map((p) => (
                              <option key={p.id} value={p.id}>{p.nome}</option>
                            ))}
                          </select>
                        </div>
                      )}
                      {selected.protocol_name && (
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Protocolo aplicado: <strong>{selected.protocol_name}</strong>
                        </p>
                      )}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Notas do atendimento / protocolo
                        </label>
                        <textarea
                          rows={10}
                          value={observacoes}
                          onChange={(e) => setObservacoes(e.target.value)}
                          className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 font-mono text-sm"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={salvarObservacoes}
                        disabled={saving}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-white disabled:opacity-50"
                        style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                      >
                        <Save size={18} />
                        {saving ? "Salvando..." : "Salvar atendimento"}
                      </button>
                    </div>
                  )}

                  {tab === "anamnese" && (
                    <div className="space-y-3">
                      {(
                        [
                          ["queixa_principal", "Queixa principal"],
                          ["historico_medico", "Histórico médico"],
                          ["medicamentos_uso", "Medicamentos em uso"],
                          ["alergias", "Alergias"],
                          ["condicoes_clinicas", "Condições clínicas"],
                          ["tipo_pele", "Tipo de pele"],
                          ["pressao_arterial", "Pressão arterial"],
                          ["observacoes", "Observações"],
                        ] as const
                      ).map(([field, label]) => (
                        <div key={field}>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
                          <textarea
                            rows={field === "queixa_principal" ? 3 : 2}
                            value={String(anamnese[field] ?? "")}
                            onChange={(e) => setAnamnese((prev) => ({ ...prev, [field]: e.target.value }))}
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
                            value={anamnese.peso ?? ""}
                            onChange={(e) => setAnamnese((prev) => ({ ...prev, peso: e.target.value }))}
                            className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">Altura (m)</label>
                          <input
                            type="number"
                            step="0.01"
                            value={anamnese.altura ?? ""}
                            onChange={(e) => setAnamnese((prev) => ({ ...prev, altura: e.target.value }))}
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
                    </div>
                  )}

                  {tab === "evolucao" && (
                    <div className="space-y-4">
                      <div className="grid gap-3">
                        <textarea
                          placeholder="Evolução / observações clínicas"
                          rows={3}
                          value={evolucaoForm.descricao}
                          onChange={(e) => setEvolucaoForm((f) => ({ ...f, descricao: e.target.value }))}
                          className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                        />
                        <textarea
                          placeholder="Procedimento realizado"
                          rows={2}
                          value={evolucaoForm.procedimento_realizado}
                          onChange={(e) => setEvolucaoForm((f) => ({ ...f, procedimento_realizado: e.target.value }))}
                          className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                        />
                        <textarea
                          placeholder="Produtos utilizados"
                          rows={2}
                          value={evolucaoForm.produtos_utilizados}
                          onChange={(e) => setEvolucaoForm((f) => ({ ...f, produtos_utilizados: e.target.value }))}
                          className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                        />
                        <textarea
                          placeholder="Orientações ao cliente"
                          rows={2}
                          value={evolucaoForm.orientacoes}
                          onChange={(e) => setEvolucaoForm((f) => ({ ...f, orientacoes: e.target.value }))}
                          className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                        />
                        <select
                          value={evolucaoForm.satisfacao}
                          onChange={(e) => setEvolucaoForm((f) => ({ ...f, satisfacao: e.target.value }))}
                          className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                        >
                          <option value="">Satisfação (opcional)</option>
                          {[1, 2, 3, 4, 5].map((n) => (
                            <option key={n} value={n}>{n} — {n === 5 ? "Excelente" : n === 1 ? "Ruim" : ""}</option>
                          ))}
                        </select>
                      </div>
                      <button
                        type="button"
                        onClick={salvarEvolucao}
                        disabled={saving}
                        className="px-4 py-2 rounded-lg text-white disabled:opacity-50"
                        style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                      >
                        Registrar evolução
                      </button>
                      {evolucoes.length > 0 && (
                        <div className="mt-6 space-y-3">
                          <h3 className="font-semibold text-gray-800 dark:text-gray-200">Registros desta consulta</h3>
                          {evolucoes.map((ev) => (
                            <div key={ev.id} className="p-3 rounded-lg bg-gray-50 dark:bg-neutral-700/50 text-sm">
                              <p className="text-xs text-gray-500 mb-1">
                                {new Date(ev.created_at).toLocaleString("pt-BR")}
                                {ev.professional_name ? ` · ${ev.professional_name}` : ""}
                              </p>
                              {ev.descricao && <p className="text-gray-800 dark:text-gray-200">{ev.descricao}</p>}
                              {ev.procedimento_realizado && (
                                <p className="text-gray-600 dark:text-gray-400 mt-1"><strong>Procedimento:</strong> {ev.procedimento_realizado}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {tab === "historico" && (
                    <div className="space-y-3">
                      {historico.length === 0 ? (
                        <p className="text-gray-500 text-sm">Nenhuma consulta anterior.</p>
                      ) : (
                        historico.map((h) => (
                          <div
                            key={h.id}
                            className={`p-3 rounded-lg border ${
                              h.id === selected.id
                                ? "border-[#8B3D52] bg-[#F5E6EA]/50 dark:bg-neutral-700"
                                : "border-gray-200 dark:border-neutral-600"
                            }`}
                          >
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="font-medium text-gray-900 dark:text-gray-100">{h.procedure_name}</p>
                                <p className="text-xs text-gray-500">
                                  {h.data_inicio ? new Date(h.data_inicio).toLocaleString("pt-BR") : "—"}
                                  {h.professional_name ? ` · ${h.professional_name}` : ""}
                                </p>
                              </div>
                              <span className="text-xs px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}>
                                {STATUS_LABEL[h.status] || h.status}
                              </span>
                            </div>
                            {h.total_evolucoes > 0 && (
                              <p className="text-xs text-gray-500 mt-1">{h.total_evolucoes} evolução(ões)</p>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
