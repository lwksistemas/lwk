"use client";

import { useEffect, useMemo, useState } from "react";
import { X, Search, Trash2 } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type ConvenioItem, LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { buildPrecosMap, CONVENIO_PARTICULAR_LABEL, precoProcedimento } from "@/lib/convenio-precos";
import { logger } from "@/lib/logger";
import type { Consulta } from "./consultas-types";

interface Option {
  id: number;
  nome: string;
  duracao_minutos?: number;
  preco?: number;
  convenio?: number | null;
}

export function NovaConsultaModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (consulta: Consulta) => void;
}) {
  const [patients, setPatients] = useState<Option[]>([]);
  const [professionals, setProfessionals] = useState<Option[]>([]);
  const [procedures, setProcedures] = useState<Option[]>([]);
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [precosMap, setPrecosMap] = useState<Record<number, number>>({});
  const [loadingData, setLoadingData] = useState(false);

  const [busca, setBusca] = useState("");
  const [patientId, setPatientId] = useState<number | "">("");
  const [professionalId, setProfessionalId] = useState<number | "">("");
  const [convenioId, setConvenioId] = useState<number | "">("");
  const [selectedProcedures, setSelectedProcedures] = useState<number[]>([]);
  const [localAtendimentoId, setLocalAtendimentoId] = useState<number | "">("");
  const [valorConsulta, setValorConsulta] = useState<string>("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  useEffect(() => {
    if (!open) return;
    setBusca("");
    setPatientId("");
    setProfessionalId("");
    setSelectedProcedures([]);
    setLocalAtendimentoId("");
    setValorConsulta("");
    setConvenioId("");
    setPrecosMap({});
    setErro("");
    setLoadingData(true);
    (async () => {
      try {
        const [pac, prof, proc, locaisRes, convRes] = await Promise.all([
          ClinicaBelezaAPI.get<Option[]>("/patients/"),
          ClinicaBelezaAPI.get<Option[]>("/professionals/"),
          ClinicaBelezaAPI.get<Option[]>("/procedures/"),
          ClinicaBelezaAPI.locaisAtendimento.list(),
          ClinicaBelezaAPI.convenios.list(),
        ]);
        const ativos = (arr: unknown) => (Array.isArray(arr) ? (arr as Option[]) : []);
        setPatients(ativos(pac));
        const profList = ativos(prof);
        setProfessionals(profList);
        setProcedures(ativos(proc));
        setLocais(Array.isArray(locaisRes) ? locaisRes : []);
        setConvenios(Array.isArray(convRes) ? convRes : []);
        if (profList.length === 1) setProfessionalId(profList[0].id);
      } catch (e) {
        logger.warn("Erro ao carregar dados para nova consulta:", e);
        setErro("Não foi possível carregar os cadastros. Tente novamente.");
      } finally {
        setLoadingData(false);
      }
    })();
  }, [open]);

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

  useEffect(() => {
    if (!patientId) return;
    const paciente = patients.find((p) => p.id === patientId);
    setConvenioId(paciente?.convenio ?? "");
  }, [patientId, patients]);

  useEffect(() => {
    if (!convenioId) {
      setPrecosMap({});
      return;
    }
    (async () => {
      try {
        const rows = await ClinicaBelezaAPI.convenios.precos(Number(convenioId));
        setPrecosMap(buildPrecosMap(rows));
      } catch {
        setPrecosMap({});
      }
    })();
  }, [convenioId]);

  const clienteSelecionado = useMemo(
    () => patients.find((p) => p.id === patientId) || null,
    [patients, patientId],
  );

  // Procedimentos disponíveis (exclui os já adicionados)
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

  // Resumo: duração total e valor total
  const resumo = useMemo(() => {
    let duracao = 0;
    let valor = 0;
    for (const id of selectedProcedures) {
      const proc = procedures.find((p) => p.id === id);
      if (proc) {
        duracao += Number(proc.duracao_minutos) || 0;
        valor += precoProcedimento(id, Number(proc.preco) || 0, convenioId, precosMap);
      }
    }
    return { duracao, valor };
  }, [selectedProcedures, procedures, convenioId, precosMap]);

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
        convenio?: number;
      } = {
        patient: Number(patientId),
        professional: Number(professionalId),
        procedures_ids: selectedProcedures,
      };
      if (convenioId) payload.convenio = Number(convenioId);
      if (localAtendimentoId) {
        payload.local_atendimento = Number(localAtendimentoId);
      }
      if (valorConsulta) {
        payload.valor_consulta = valorConsulta;
      }
      const consulta = await ClinicaBelezaAPI.consultas.criar(payload);
      onCreated(consulta as Consulta);
    } catch (e: unknown) {
      logger.warn("Erro ao abrir consulta avulsa:", e);
      setErro(e instanceof Error ? e.message : "Erro ao abrir a consulta.");
    } finally {
      setSalvando(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b dark:border-neutral-700 shrink-0">
          <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">Nova consulta</h2>
          <button type="button" onClick={onClose} className="p-1.5 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {loadingData ? (
            <div className="text-center py-8 text-gray-500 text-sm">Carregando cadastros...</div>
          ) : (
            <>
              {/* Cliente */}
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Cliente *</label>
                <div className="relative mb-2">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={busca}
                    onChange={(e) => setBusca(e.target.value)}
                    placeholder="Buscar pelo nome..."
                    className="w-full pl-8 pr-3 py-2 text-sm border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                  />
                </div>
                {busca.trim() && (
                  <select
                    value={patientId}
                    onChange={(e) => { setPatientId(e.target.value ? Number(e.target.value) : ""); setBusca(""); }}
                    size={Math.min(pacientesFiltrados.length || 1, 4)}
                    className="w-full px-3 py-1.5 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 text-sm mb-1"
                  >
                    {pacientesFiltrados.length === 0 ? (
                      <option value="" disabled>Nenhum cliente encontrado</option>
                    ) : (
                      pacientesFiltrados.map((p) => (
                        <option key={p.id} value={p.id}>{p.nome}</option>
                      ))
                    )}
                  </select>
                )}
                {clienteSelecionado && (
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    Selecionado: <strong>{clienteSelecionado.nome}</strong>
                  </p>
                )}
              </div>

              {/* Profissional */}
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Profissional *</label>
                <select
                  value={professionalId}
                  onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                >
                  <option value="">Selecione...</option>
                  {professionals.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome}</option>
                  ))}
                </select>
              </div>

              {/* Convênio */}
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Convênio</label>
                <select
                  value={convenioId}
                  onChange={(e) => setConvenioId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                >
                  <option value="">{CONVENIO_PARTICULAR_LABEL}</option>
                  {convenios.map((c) => (
                    <option key={c.id} value={c.id}>{c.nome}</option>
                  ))}
                </select>
              </div>

              {/* Local de Atendimento */}
              {locais.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">Local de Atendimento</label>
                  <select
                    value={localAtendimentoId}
                    onChange={(e) => handleLocalChange(e.target.value ? Number(e.target.value) : "")}
                    className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
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

              {/* Valor da Consulta (visível quando local selecionado) */}
              {locais.length > 0 && localAtendimentoId && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    Valor da Consulta (R$)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={valorConsulta}
                    onChange={(e) => setValorConsulta(e.target.value)}
                    className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                    placeholder="0.00"
                  />
                  <p className="text-xs text-gray-400 mt-1">Preenchido pelo local selecionado. Pode ser alterado manualmente.</p>
                </div>
              )}

              {/* Procedimentos (multi-select) */}
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  Procedimentos * <span className="font-normal text-gray-400">(pode adicionar vários)</span>
                </label>
                <div className="flex gap-2">
                  <select
                    id="proc-select"
                    className="flex-1 px-3 py-2 text-sm border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
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
                </div>

                {/* Lista de procedimentos selecionados */}
                {selectedProcedures.length > 0 && (
                  <div className="mt-2 space-y-1.5">
                    {selectedProcedures.map((id) => {
                      const proc = procedures.find((p) => p.id === id);
                      if (!proc) return null;
                      const valorProc = precoProcedimento(id, Number(proc.preco) || 0, convenioId, precosMap);
                      return (
                        <div key={id} className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-neutral-700/50 rounded-lg">
                          <div className="text-sm">
                            <span className="font-medium text-gray-800 dark:text-gray-200">{proc.nome}</span>
                            <span className="text-gray-500 dark:text-gray-400 ml-2 text-xs">
                              {Number(proc.duracao_minutos) || 0}min
                              {valorProc > 0 ? ` · R$ ${valorProc.toFixed(2)}` : ""}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => removerProcedimento(id)}
                            className="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      );
                    })}
                    {/* Resumo */}
                    <div className="flex items-center justify-between px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400 border-t dark:border-neutral-600 mt-1 pt-2">
                      <span>Duração total: <strong>{resumo.duracao} min</strong></span>
                      {resumo.valor > 0 && <span>Valor: <strong>R$ {resumo.valor.toFixed(2)}</strong></span>}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
        </div>
        <div className="flex gap-3 px-5 py-4 border-t dark:border-neutral-700 shrink-0">
          <button type="button" onClick={onClose} className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium">
            Cancelar
          </button>
          <button
            type="button"
            onClick={criar}
            disabled={salvando || loadingData}
            className="flex-1 py-2.5 rounded-lg text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            {salvando ? "Abrindo..." : "Abrir consulta"}
          </button>
        </div>
      </div>
    </div>
  );
}
