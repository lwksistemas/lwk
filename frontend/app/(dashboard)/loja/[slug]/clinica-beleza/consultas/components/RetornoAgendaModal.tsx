"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Plus, RefreshCw, Trash2, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  ClinicaBelezaAPI,
  type AgendaRetornoConfigItem,
  type RetornoProcedimentoRegraItem,
} from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";

interface RetornoAgendaModalProps {
  open: boolean;
  onClose: () => void;
}

function extractApiError(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const body = err as Record<string, unknown>;
  if (typeof body.error === "string") return body.error;
  if (typeof body.detail === "string") return body.detail;
  for (const val of Object.values(body)) {
    if (Array.isArray(val) && typeof val[0] === "string") return val[0];
    if (typeof val === "string") return val;
  }
  return fallback;
}

export function RetornoAgendaModal({ open, onClose }: RetornoAgendaModalProps) {
  const [config, setConfig] = useState<AgendaRetornoConfigItem | null>(null);
  const [regras, setRegras] = useState<RetornoProcedimentoRegraItem[]>([]);
  const [procedures, setProcedures] = useState<{ id: number; nome?: string; name?: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [novaRegraProc, setNovaRegraProc] = useState<number | "">("");
  const [novaRegraDias, setNovaRegraDias] = useState("30");

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [cfg, regs, procs] = await Promise.all([
        ClinicaBelezaAPI.retorno.getConfig(),
        ClinicaBelezaAPI.retorno.listRegras(),
        ClinicaBelezaAPI.procedures.list({ active: true, page_size: 500 }),
      ]);
      setConfig(cfg);
      setRegras(Array.isArray(regs) ? regs : []);
      setProcedures(Array.isArray(procs.results) ? procs.results : []);
    } catch {
      setErro("Erro ao carregar configuração de retorno.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadAll();
      setNovaRegraProc("");
      setNovaRegraDias("30");
      setErro("");
    }
  }, [open, loadAll]);

  const proceduresDisponiveis = useMemo(() => {
    const usados = new Set(regras.map((r) => r.procedure));
    return procedures.filter((p) => !usados.has(p.id));
  }, [procedures, regras]);

  const salvarConfig = async (patch: Partial<AgendaRetornoConfigItem>) => {
    if (!config) return;
    setSalvando(true);
    setErro("");
    try {
      const updated = await ClinicaBelezaAPI.retorno.updateConfig(patch);
      setConfig(updated);
    } catch (e: unknown) {
      setErro(extractApiError(e, "Erro ao salvar configuração."));
    } finally {
      setSalvando(false);
    }
  };

  const adicionarRegra = async () => {
    if (!novaRegraProc) {
      setErro("Selecione o procedimento.");
      return;
    }
    const dias = parseInt(novaRegraDias, 10);
    if (!dias || dias < 1) {
      setErro("Informe o prazo em dias (mínimo 1).");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.retorno.createRegra({ procedure: Number(novaRegraProc), dias_retorno: dias });
      setNovaRegraProc("");
      setNovaRegraDias("30");
      await loadAll();
    } catch (e: unknown) {
      setErro(extractApiError(e, "Erro ao adicionar regra."));
    } finally {
      setSalvando(false);
    }
  };

  const excluirRegra = async (id: number) => {
    if (!confirm("Remover esta regra de retorno por procedimento?")) return;
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.retorno.deleteRegra(id);
      await loadAll();
    } catch (e: unknown) {
      setErro(extractApiError(e, "Erro ao excluir regra."));
    } finally {
      setSalvando(false);
    }
  };

  if (!open) return null;

  const inputClass =
    "w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-800";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Retorno gratuito</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Isenta a taxa de consulta (local de atendimento) dentro do prazo configurado
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={salvando}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
          {erro && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
              {erro}
            </div>
          )}

          {loading ? (
            <div className="text-center py-10 text-gray-500">
              <Loader2 size={24} className="animate-spin mx-auto mb-2" />
              Carregando...
            </div>
          ) : config ? (
            <>
              <section className="space-y-3">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Retorno por consulta</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Paciente com consulta concluída retorna dentro do prazo → não paga taxa de consulta.
                </p>
                <label className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
                  <input
                    type="checkbox"
                    checked={config.retorno_consulta_ativo}
                    disabled={salvando}
                    onChange={(e) => salvarConfig({ retorno_consulta_ativo: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  Ativar retorno por consulta
                </label>
                {config.retorno_consulta_ativo && (
                  <div>
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                      Prazo (dias)
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={3650}
                      value={config.dias_retorno_consulta}
                      disabled={salvando}
                      onChange={(e) => {
                        const v = parseInt(e.target.value, 10);
                        if (v > 0) setConfig({ ...config, dias_retorno_consulta: v });
                      }}
                      onBlur={() => salvarConfig({ dias_retorno_consulta: config.dias_retorno_consulta })}
                      className={`${inputClass} max-w-[120px]`}
                    />
                  </div>
                )}
              </section>

              <section className="space-y-3 pt-2 border-t border-gray-100 dark:border-neutral-800">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Retorno por procedimento</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Após procedimento concluído, acompanhamento dentro do prazo → taxa de consulta isenta
                  (procedimentos cobram normalmente).
                </p>
                <label className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
                  <input
                    type="checkbox"
                    checked={config.retorno_procedimento_ativo}
                    disabled={salvando}
                    onChange={(e) => salvarConfig({ retorno_procedimento_ativo: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  Ativar retorno por procedimento
                </label>

                {config.retorno_procedimento_ativo && (
                  <div className="space-y-3">
                    <ul className="space-y-2">
                      {regras.length === 0 ? (
                        <li className="text-xs text-gray-500 py-2">Nenhuma regra cadastrada.</li>
                      ) : (
                        regras.map((r) => (
                          <li
                            key={r.id}
                            className="flex items-center justify-between gap-2 p-3 rounded-lg bg-gray-50 dark:bg-neutral-800"
                          >
                            <div className="min-w-0">
                              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {r.procedure_name}
                              </span>
                              <span className="block text-xs text-gray-500">{r.dias_retorno} dias</span>
                            </div>
                            <button
                              type="button"
                              onClick={() => excluirRegra(r.id)}
                              disabled={salvando}
                              className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 shrink-0"
                              title="Remover"
                            >
                              <Trash2 size={14} className="text-red-500" />
                            </button>
                          </li>
                        ))
                      )}
                    </ul>

                    {proceduresDisponiveis.length > 0 && (
                      <div className="p-3 rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/40 dark:bg-purple-900/10 space-y-2">
                        <p className="text-xs font-medium text-gray-700 dark:text-gray-300">Nova regra</p>
                        <select
                          value={novaRegraProc}
                          onChange={(e) => setNovaRegraProc(e.target.value ? Number(e.target.value) : "")}
                          className={inputClass}
                          disabled={salvando}
                        >
                          <option value="">Procedimento</option>
                          {proceduresDisponiveis.map((p) => (
                            <option key={p.id} value={p.id}>
                              {entityName(p)}
                            </option>
                          ))}
                        </select>
                        <div className="flex gap-2 items-end">
                          <div className="flex-1">
                            <label className="block text-xs text-gray-500 mb-1">Prazo (dias)</label>
                            <input
                              type="number"
                              min={1}
                              max={3650}
                              value={novaRegraDias}
                              onChange={(e) => setNovaRegraDias(e.target.value)}
                              className={inputClass}
                              disabled={salvando}
                            />
                          </div>
                          <button
                            type="button"
                            onClick={adicionarRegra}
                            disabled={salvando}
                            className="flex items-center gap-1 px-3 py-2 text-white rounded-lg text-sm font-medium disabled:opacity-50 shrink-0"
                            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                          >
                            {salvando ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
                            Adicionar
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </section>
            </>
          ) : null}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 dark:border-neutral-700 flex justify-between shrink-0">
          <button
            type="button"
            onClick={() => loadAll()}
            disabled={loading || salvando}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800"
          >
            <RefreshCw size={14} />
            Atualizar
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={salvando}
            className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
