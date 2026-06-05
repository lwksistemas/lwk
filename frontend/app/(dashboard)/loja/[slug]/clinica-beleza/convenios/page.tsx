"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Plus, Save, Trash2 } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  ClinicaBelezaAPI,
  type ConvenioItem,
  type ConvenioPrecoItem,
  type ConvenioPrecoModo,
} from "@/lib/clinica-beleza-api";
import { calcularPrecoEfetivo } from "@/lib/convenio-precos";
import { logger } from "@/lib/logger";

interface ProcedureRow {
  id: number;
  nome: string;
  preco?: number | string;
}

interface PrecoLinha {
  modo: ConvenioPrecoModo;
  valor: string;
}

const EMPTY_LINHA: PrecoLinha = { modo: "fixo", valor: "" };

export default function ConveniosPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [procedures, setProcedures] = useState<ProcedureRow[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [linhas, setLinhas] = useState<Record<number, PrecoLinha>>({});
  const [novoNome, setNovoNome] = useState("");
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const [conv, proc] = await Promise.all([
        ClinicaBelezaAPI.convenios.list(),
        ClinicaBelezaAPI.get<ProcedureRow[]>("/procedures/"),
      ]);
      setConvenios(Array.isArray(conv) ? conv : []);
      setProcedures(Array.isArray(proc) ? proc : []);
    } catch (e) {
      logger.warn("Erro ao carregar convênios:", e);
      setErro("Não foi possível carregar os convênios.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  useEffect(() => {
    if (!selectedId) {
      setLinhas({});
      return;
    }
    (async () => {
      try {
        const rows = await ClinicaBelezaAPI.convenios.precos(Number(selectedId));
        const map: Record<number, PrecoLinha> = {};
        for (const r of rows as ConvenioPrecoItem[]) {
          map[r.procedure] = {
            modo: r.modo || "fixo",
            valor: String(Number(r.preco)),
          };
        }
        setLinhas(map);
      } catch (e) {
        logger.warn("Erro ao carregar preços do convênio:", e);
      }
    })();
  }, [selectedId]);

  const previewPorProc = useMemo(() => {
    const out: Record<number, number | null> = {};
    for (const p of procedures) {
      const linha = linhas[p.id];
      if (!linha?.valor.trim()) {
        out[p.id] = null;
        continue;
      }
      const particular = Number(p.preco) || 0;
      const valor = Number(linha.valor) || 0;
      out[p.id] = calcularPrecoEfetivo(particular, linha.modo, valor);
    }
    return out;
  }, [procedures, linhas]);

  const criarConvenio = async () => {
    if (!novoNome.trim()) return;
    setSalvando(true);
    setErro("");
    try {
      const created = await ClinicaBelezaAPI.convenios.create({ nome: novoNome.trim() });
      setNovoNome("");
      await carregar();
      setSelectedId(created.id);
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao criar convênio.");
    } finally {
      setSalvando(false);
    }
  };

  const salvarPrecos = async () => {
    if (!selectedId) return;
    setSalvando(true);
    setErro("");
    try {
      const payload = procedures.map((p) => {
        const linha = linhas[p.id];
        if (!linha?.valor.trim()) {
          return { procedure: p.id, preco: null };
        }
        return {
          procedure: p.id,
          modo: linha.modo,
          preco: linha.valor,
        };
      });
      await ClinicaBelezaAPI.convenios.savePrecos(Number(selectedId), payload);
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao salvar preços.");
    } finally {
      setSalvando(false);
    }
  };

  const excluirConvenio = async () => {
    if (!selectedId || !confirm("Desativar este convênio?")) return;
    setSalvando(true);
    try {
      await ClinicaBelezaAPI.convenios.delete(Number(selectedId));
      setSelectedId("");
      await carregar();
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao desativar convênio.");
    } finally {
      setSalvando(false);
    }
  };

  const updateLinha = (procId: number, patch: Partial<PrecoLinha>) => {
    setLinhas((prev) => ({
      ...prev,
      [procId]: { ...(prev[procId] || EMPTY_LINHA), ...patch },
    }));
  };

  const convenioSelecionado = convenios.find((c) => c.id === selectedId);

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Convênios"
        subtitle="Preço fixo (R$) ou percentual (%) sobre o valor particular"
        backHref={`/loja/${slug}/clinica-beleza/configuracoes`}
      />
      <ClinicaBelezaPageContent>
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <ClinicaBelezaPanel className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3">Planos</h3>
            {loading ? (
              <p className="text-sm text-gray-500">Carregando...</p>
            ) : (
              <ul className="space-y-1 mb-4">
                {convenios.map((c) => (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(c.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        selectedId === c.id
                          ? "bg-pink-50 dark:bg-pink-900/20 font-medium text-pink-900 dark:text-pink-200"
                          : "hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
                      }`}
                    >
                      {c.nome}
                    </button>
                  </li>
                ))}
                {convenios.length === 0 && (
                  <li className="text-sm text-gray-500">Nenhum convênio cadastrado.</li>
                )}
              </ul>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                value={novoNome}
                onChange={(e) => setNovoNome(e.target.value)}
                placeholder="Novo convênio..."
                className="flex-1 px-3 py-2 text-sm border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
              />
              <button
                type="button"
                onClick={criarConvenio}
                disabled={salvando || !novoNome.trim()}
                className="p-2 rounded-lg text-white disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                title="Adicionar"
              >
                <Plus size={18} />
              </button>
            </div>
          </ClinicaBelezaPanel>

          <ClinicaBelezaPanel className="p-5">
            {!selectedId ? (
              <p className="text-sm text-gray-500 py-8 text-center">
                Selecione um convênio para editar os preços dos procedimentos.
              </p>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
                  <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                    {convenioSelecionado?.nome}
                  </h3>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={excluirConvenio}
                      disabled={salvando}
                      className="flex items-center gap-1.5 px-3 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <Trash2 size={14} />
                      Desativar
                    </button>
                    <button
                      type="button"
                      onClick={salvarPrecos}
                      disabled={salvando}
                      className="flex items-center gap-1.5 px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50"
                      style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                    >
                      <Save size={14} />
                      {salvando ? "Salvando..." : "Salvar preços"}
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mb-4">
                  <strong>Fixo:</strong> valor em R$. <strong>%:</strong> percentual sobre o preço particular.
                  Deixe em branco para usar o preço particular.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[640px]">
                    <thead>
                      <tr className="border-b dark:border-neutral-600 text-left text-gray-500">
                        <th className="py-2 pr-3 font-medium">Procedimento</th>
                        <th className="py-2 pr-3 font-medium">Particular</th>
                        <th className="py-2 pr-3 font-medium w-28">Modo</th>
                        <th className="py-2 pr-3 font-medium w-28">Valor</th>
                        <th className="py-2 font-medium">Cobrado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {procedures.map((p) => {
                        const linha = linhas[p.id] || EMPTY_LINHA;
                        const preview = previewPorProc[p.id];
                        return (
                          <tr key={p.id} className="border-b last:border-0 dark:border-neutral-700">
                            <td className="py-2.5 pr-3 text-gray-800 dark:text-gray-200">{p.nome}</td>
                            <td className="py-2.5 pr-3 text-gray-500 whitespace-nowrap">
                              R$ {Number(p.preco || 0).toFixed(2)}
                            </td>
                            <td className="py-2.5 pr-3">
                              <select
                                value={linha.modo}
                                onChange={(e) =>
                                  updateLinha(p.id, { modo: e.target.value as ConvenioPrecoModo })
                                }
                                className="w-full px-2 py-1.5 text-xs border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                              >
                                <option value="fixo">Fixo R$</option>
                                <option value="percentual">%</option>
                              </select>
                            </td>
                            <td className="py-2.5 pr-3">
                              <input
                                type="number"
                                step={linha.modo === "percentual" ? "0.01" : "0.01"}
                                min="0"
                                max={linha.modo === "percentual" ? "100" : undefined}
                                value={linha.valor}
                                onChange={(e) => updateLinha(p.id, { valor: e.target.value })}
                                placeholder="—"
                                className="w-full px-2 py-1.5 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                              />
                            </td>
                            <td className="py-2.5 text-gray-700 dark:text-gray-300 whitespace-nowrap">
                              {preview != null ? (
                                <>
                                  R$ {preview.toFixed(2)}
                                  {linha.modo === "percentual" && linha.valor && (
                                    <span className="text-xs text-gray-400 ml-1">({linha.valor}%)</span>
                                  )}
                                </>
                              ) : (
                                <span className="text-gray-400">Particular</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            {erro && (
              <p className="mt-4 text-sm text-red-600 dark:text-red-400">{erro}</p>
            )}
          </ClinicaBelezaPanel>
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
