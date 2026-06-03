"use client";

/**
 * Nova Consulta — Página dedicada (full page)
 * Substitui o modal anterior para melhor experiência com formulários grandes.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Search, Trash2, ArrowLeft } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";

interface Option {
  id: number;
  nome: string;
  duracao_minutos?: number;
  preco?: number;
}

export default function NovaConsultaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [patients, setPatients] = useState<Option[]>([]);
  const [professionals, setProfessionals] = useState<Option[]>([]);
  const [procedures, setProcedures] = useState<Option[]>([]);
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  const [busca, setBusca] = useState("");
  const [patientId, setPatientId] = useState<number | "">("");
  const [professionalId, setProfessionalId] = useState<number | "">("");
  const [selectedProcedures, setSelectedProcedures] = useState<number[]>([]);
  const [localAtendimentoId, setLocalAtendimentoId] = useState<number | "">("");
  const [valorConsulta, setValorConsulta] = useState<string>("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const voltar = useCallback(() => {
    router.push(`/loja/${slug}/clinica-beleza/consultas`);
  }, [router, slug]);

  useEffect(() => {
    (async () => {
      try {
        const [pac, prof, proc, locaisRes] = await Promise.all([
          ClinicaBelezaAPI.get<Option[]>("/patients/"),
          ClinicaBelezaAPI.get<Option[]>("/professionals/"),
          ClinicaBelezaAPI.get<Option[]>("/procedures/"),
          ClinicaBelezaAPI.locaisAtendimento.list(),
        ]);
        const ativos = (arr: unknown) => (Array.isArray(arr) ? (arr as Option[]) : []);
        setPatients(ativos(pac));
        const profList = ativos(prof);
        setProfessionals(profList);
        setProcedures(ativos(proc));
        setLocais(Array.isArray(locaisRes) ? locaisRes : []);
        if (profList.length === 1) setProfessionalId(profList[0].id);
      } catch (e) {
        logger.warn("Erro ao carregar dados para nova consulta:", e);
        setErro("Não foi possível carregar os cadastros. Tente novamente.");
      } finally {
        setLoadingData(false);
      }
    })();
  }, []);

  const pacientesFiltrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    if (!q) return [];
    return patients.filter((p) => (p.nome || "").toLowerCase().includes(q)).slice(0, 50);
  }, [busca, patients]);

  useEffect(() => {
    if (pacientesFiltrados.length === 1) {
      setPatientId(pacientesFiltrados[0].id);
    }
  }, [pacientesFiltrados]);

  const clienteSelecionado = useMemo(
    () => patients.find((p) => p.id === patientId) || null,
    [patients, patientId],
  );

  const procedimentosDisponiveis = useMemo(
    () => procedures.filter((p) => !selectedProcedures.includes(p.id)),
    [procedures, selectedProcedures],
  );

  const adicionarProcedimento = (id: number) => {
    if (id && !selectedProcedures.includes(id)) {
      setSelectedProcedures((prev) => [...prev, id]);
    }
  };

  const removerProcedimento = (id: number) => {
    setSelectedProcedures((prev) => prev.filter((p) => p !== id));
  };

  const resumo = useMemo(() => {
    let duracao = 0;
    let valor = 0;
    for (const id of selectedProcedures) {
      const proc = procedures.find((p) => p.id === id);
      if (proc) {
        duracao += Number(proc.duracao_minutos) || 0;
        valor += Number(proc.preco) || 0;
      }
    }
    return { duracao, valor };
  }, [selectedProcedures, procedures]);

  const handleLocalChange = (id: number | "") => {
    setLocalAtendimentoId(id);
    if (id) {
      const local = locais.find((l) => l.id === id);
      if (local) {
        setValorConsulta(String(Number(local.valor_consulta)));
      }
    } else {
      setValorConsulta("");
    }
  };

  const criar = async () => {
    if (!patientId || !professionalId || selectedProcedures.length === 0) {
      setErro("Selecione o cliente, o profissional e pelo menos um procedimento.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const payload: {
        patient: number;
        professional: number;
        procedures_ids: number[];
        local_atendimento?: number;
        valor_consulta?: number | string;
      } = {
        patient: Number(patientId),
        professional: Number(professionalId),
        procedures_ids: selectedProcedures,
      };
      if (localAtendimentoId) {
        payload.local_atendimento = Number(localAtendimentoId);
      }
      if (valorConsulta) {
        payload.valor_consulta = valorConsulta;
      }
      await ClinicaBelezaAPI.consultas.criar(payload);
      router.push(`/loja/${slug}/clinica-beleza/consultas`);
    } catch (e: unknown) {
      logger.warn("Erro ao abrir consulta avulsa:", e);
      setErro(e instanceof Error ? e.message : "Erro ao abrir a consulta.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Nova consulta"
        subtitle="Abra um atendimento direto pelo cadastro do cliente"
        backHref={`/loja/${slug}/clinica-beleza/consultas`}
      />
      <ClinicaBelezaPageContent>
        <ClinicaBelezaPanel className="p-6 md:p-8">
            {loadingData ? (
              <div className="text-center py-16 text-gray-500 text-sm">Carregando cadastros...</div>
            ) : (
              <div className="space-y-6">
                {/* Cliente */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Cliente *
                  </label>
                  <div className="relative mb-2">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={busca}
                      onChange={(e) => setBusca(e.target.value)}
                      placeholder="Buscar pelo nome..."
                      className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
                    />
                  </div>
                  {busca.trim() && pacientesFiltrados.length > 0 && (
                    <div className="border border-gray-200 dark:border-neutral-600 rounded-lg overflow-hidden mb-2 max-h-48 overflow-y-auto">
                      {pacientesFiltrados.map((p) => (
                        <button
                          key={p.id}
                          type="button"
                          onClick={() => { setPatientId(p.id); setBusca(""); }}
                          className={`w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors border-b last:border-b-0 border-gray-100 dark:border-neutral-700 ${
                            patientId === p.id ? "bg-pink-50 dark:bg-pink-900/20 font-medium" : ""
                          }`}
                        >
                          {p.nome}
                        </button>
                      ))}
                    </div>
                  )}
                  {busca.trim() && pacientesFiltrados.length === 0 && (
                    <p className="text-xs text-gray-400 mb-2">Nenhum cliente encontrado</p>
                  )}
                  {clienteSelecionado && (
                    <div className="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <span className="text-sm text-green-700 dark:text-green-400">
                        Selecionado: <strong>{clienteSelecionado.nome}</strong>
                      </span>
                      <button
                        type="button"
                        onClick={() => setPatientId("")}
                        className="ml-auto text-xs text-gray-400 hover:text-red-500"
                      >
                        Trocar
                      </button>
                    </div>
                  )}
                </div>

                {/* Profissional */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Profissional *
                  </label>
                  <select
                    value={professionalId}
                    onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
                    className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
                  >
                    <option value="">Selecione...</option>
                    {professionals.map((p) => (
                      <option key={p.id} value={p.id}>{p.nome}</option>
                    ))}
                  </select>
                </div>

                {/* Local de Atendimento */}
                {locais.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Local de Atendimento
                    </label>
                    <select
                      value={localAtendimentoId}
                      onChange={(e) => handleLocalChange(e.target.value ? Number(e.target.value) : "")}
                      className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
                    >
                      <option value="">Selecione o local...</option>
                      {locais.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.nome} — R$ {Number(l.valor_consulta).toFixed(2)}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Valor da Consulta */}
                {locais.length > 0 && localAtendimentoId && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Valor da Consulta (R$)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={valorConsulta}
                      onChange={(e) => setValorConsulta(e.target.value)}
                      className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
                      placeholder="0.00"
                    />
                    <p className="text-xs text-gray-400 mt-1.5">
                      Preenchido pelo local selecionado. Pode ser alterado manualmente.
                    </p>
                  </div>
                )}

                {/* Procedimentos */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Procedimentos * <span className="font-normal text-gray-400">(pode adicionar vários)</span>
                  </label>
                  <select
                    className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
                    defaultValue=""
                    onChange={(e) => {
                      const id = Number(e.target.value);
                      if (id) adicionarProcedimento(id);
                      e.target.value = "";
                    }}
                  >
                    <option value="">Adicionar procedimento...</option>
                    {procedimentosDisponiveis.map((p) => (
                      <option key={p.id} value={p.id}>{p.nome}</option>
                    ))}
                  </select>

                  {selectedProcedures.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {selectedProcedures.map((id) => {
                        const proc = procedures.find((p) => p.id === id);
                        if (!proc) return null;
                        return (
                          <div key={id} className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-neutral-700/50 rounded-lg">
                            <div className="text-sm">
                              <span className="font-medium text-gray-800 dark:text-gray-200">{proc.nome}</span>
                              <span className="text-gray-500 dark:text-gray-400 ml-2 text-xs">
                                {Number(proc.duracao_minutos) || 0}min
                                {Number(proc.preco) ? ` · R$ ${Number(proc.preco).toFixed(2)}` : ""}
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() => removerProcedimento(id)}
                              className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        );
                      })}
                      <div className="flex items-center justify-between px-4 py-2 text-sm text-gray-600 dark:text-gray-400 border-t dark:border-neutral-600 mt-2 pt-3">
                        <span>Duração total: <strong>{resumo.duracao} min</strong></span>
                        {resumo.valor > 0 && <span>Valor: <strong>R$ {resumo.valor.toFixed(2)}</strong></span>}
                      </div>
                    </div>
                  )}
                </div>

                {/* Erro */}
                {erro && (
                  <div className="px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>
                  </div>
                )}

                {/* Botões */}
                <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-neutral-700">
                  <button
                    type="button"
                    onClick={voltar}
                    className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
                  >
                    <ArrowLeft size={16} />
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={criar}
                    disabled={salvando}
                    className="flex-1 py-3 rounded-lg text-white text-sm font-medium disabled:opacity-50 hover:opacity-90 transition-opacity"
                    style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                  >
                    {salvando ? "Abrindo consulta..." : "Abrir consulta"}
                  </button>
                </div>
              </div>
            )}
          </ClinicaBelezaPanel>
      </ClinicaBelezaPageContent>
    </>
  );
}
