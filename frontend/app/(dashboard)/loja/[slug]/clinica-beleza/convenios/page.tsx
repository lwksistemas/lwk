"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, ChevronRight, FileText, Pencil, Save, Trash2 } from "lucide-react";
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
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/convenios`;

  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [procedures, setProcedures] = useState<ProcedureRow[]>([]);
  const [linhas, setLinhas] = useState<Record<number, PrecoLinha>>({});
  const [novoNome, setNovoNome] = useState("");
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const isNovo = searchParams.get("novo") === "1";
  const editIdParam = searchParams.get("id");
  const isFormView = isNovo || Boolean(editIdParam);
  const editId = editIdParam ? Number(editIdParam) : null;

  const carregarLista = useCallback(async () => {
    setLoading(true);
    try {
      const conv = await ClinicaBelezaAPI.convenios.list();
      setConvenios(Array.isArray(conv) ? conv : []);
    } catch (e) {
      logger.warn("Erro ao carregar convênios:", e);
      setErro("Não foi possível carregar os convênios.");
    } finally {
      setLoading(false);
    }
  }, []);

  const carregarProcedimentos = useCallback(async () => {
    try {
      const proc = await ClinicaBelezaAPI.get<ProcedureRow[]>("/procedures/");
      setProcedures(Array.isArray(proc) ? proc : []);
    } catch (e) {
      logger.warn("Erro ao carregar procedimentos:", e);
    }
  }, []);

  useEffect(() => {
    carregarLista();
  }, [carregarLista]);

  useEffect(() => {
    if (!isFormView) return;
    setErro("");
    if (isNovo) {
      setNovoNome("");
      return;
    }
    carregarProcedimentos();
  }, [isFormView, isNovo, carregarProcedimentos]);

  useEffect(() => {
    if (!editId || isNovo) {
      setLinhas({});
      return;
    }
    (async () => {
      try {
        const rows = await ClinicaBelezaAPI.convenios.precos(editId);
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
        setErro("Não foi possível carregar os preços deste convênio.");
      }
    })();
  }, [editId, isNovo]);

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

  const convenioEditando = useMemo(
    () => (editId ? convenios.find((c) => c.id === editId) : null),
    [convenios, editId],
  );

  const voltarLista = () => {
    setErro("");
    router.replace(basePath, { scroll: false });
  };

  const abrirNovo = () => {
    router.replace(`${basePath}?novo=1`, { scroll: false });
  };

  const abrirEditar = (c: ConvenioItem) => {
    router.replace(`${basePath}?id=${c.id}`, { scroll: false });
  };

  const criarConvenio = async () => {
    if (!novoNome.trim()) {
      setErro("Informe o nome do convênio.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const created = await ClinicaBelezaAPI.convenios.create({ nome: novoNome.trim() });
      await carregarLista();
      router.replace(`${basePath}?id=${created.id}`, { scroll: false });
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao criar convênio.");
    } finally {
      setSalvando(false);
    }
  };

  const salvarPrecos = async () => {
    if (!editId) return;
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
      await ClinicaBelezaAPI.convenios.savePrecos(editId, payload);
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao salvar preços.");
    } finally {
      setSalvando(false);
    }
  };

  const excluirConvenio = async (c: ConvenioItem) => {
    if (!confirm(`Excluir o convênio "${c.nome}"? Ele deixará de aparecer nas opções de atendimento.`)) {
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.convenios.delete(c.id);
      await carregarLista();
      if (editId === c.id) {
        voltarLista();
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Erro ao excluir convênio.";
      if (editId === c.id) {
        setErro(msg);
      } else {
        alert(msg);
      }
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

  /* ── Novo convênio ── */
  if (isNovo) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title="Novo convênio"
          subtitle="Cadastre um plano e depois defina os preços dos procedimentos"
          backHref={basePath}
          icon={FileText}
        />
        <ClinicaBelezaPageContent className="flex flex-col flex-1 !p-0">
          <div className="px-4 md:px-6 lg:px-8 pt-2 pb-3 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
            <button
              type="button"
              onClick={voltarLista}
              className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            >
              <ArrowLeft size={16} />
              Voltar à lista
            </button>
          </div>
          <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
            <ClinicaBelezaPanel className="p-5 md:p-8 max-w-lg">
              {erro && (
                <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                  {erro}
                </div>
              )}
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Nome do convênio *
              </label>
              <input
                type="text"
                value={novoNome}
                onChange={(e) => setNovoNome(e.target.value)}
                placeholder="Ex.: Unimed, Santa Casa..."
                autoFocus
                className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 mb-6"
              />
              <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4 border-t border-gray-100 dark:border-neutral-700">
                <button
                  type="button"
                  onClick={voltarLista}
                  className="flex-1 sm:flex-none py-2.5 px-6 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={criarConvenio}
                  disabled={salvando || !novoNome.trim()}
                  className="flex-1 sm:flex-none flex items-center justify-center gap-2 py-2.5 px-6 rounded-lg text-white text-sm font-medium disabled:opacity-50"
                  style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                >
                  <Save size={16} />
                  {salvando ? "Criando..." : "Criar e definir preços"}
                </button>
              </div>
            </ClinicaBelezaPanel>
          </div>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  /* ── Editar preços (tela cheia) ── */
  if (editIdParam) {
    if (!loading && convenios.length > 0 && !convenioEditando) {
      return (
        <>
          <ClinicaBelezaStandardPageHeader title="Convênio" backHref={basePath} />
          <ClinicaBelezaPageContent>
            <p className="text-center py-16 text-gray-500">Convênio não encontrado.</p>
          </ClinicaBelezaPageContent>
        </>
      );
    }

    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={convenioEditando?.nome || "Convênio"}
          subtitle="Preço fixo (R$) ou percentual (%) sobre o valor particular"
          backHref={basePath}
          icon={FileText}
        />
        <ClinicaBelezaPageContent className="flex flex-col flex-1 !p-0">
          <div className="px-4 md:px-6 lg:px-8 pt-2 pb-3 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80 flex flex-wrap items-center justify-between gap-3">
            <button
              type="button"
              onClick={voltarLista}
              className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            >
              <ArrowLeft size={16} />
              Voltar à lista
            </button>
            <div className="flex gap-2">
              {convenioEditando && (
                <button
                  type="button"
                  onClick={() => excluirConvenio(convenioEditando)}
                  disabled={salvando}
                  className="flex items-center gap-1.5 px-3 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <Trash2 size={14} />
                  Excluir
                </button>
              )}
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

          <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
            {erro && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                {erro}
              </div>
            )}
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
              <strong>Fixo:</strong> valor em R$. <strong>%:</strong> percentual sobre o preço particular.
              Deixe em branco para usar o preço particular.
            </p>
            <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm overflow-hidden w-full">
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[720px]">
                  <thead className="bg-gray-50 dark:bg-neutral-900/80 text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700">
                    <tr>
                      <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Procedimento</th>
                      <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Particular</th>
                      <th className="text-left px-4 md:px-6 py-3.5 font-semibold w-32">Modo</th>
                      <th className="text-left px-4 md:px-6 py-3.5 font-semibold w-32">Valor</th>
                      <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Cobrado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {procedures.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                          Carregando procedimentos...
                        </td>
                      </tr>
                    ) : (
                      procedures.map((p) => {
                        const linha = linhas[p.id] || EMPTY_LINHA;
                        const preview = previewPorProc[p.id];
                        return (
                          <tr
                            key={p.id}
                            className="border-t border-gray-100 dark:border-neutral-700/80 hover:bg-[#F5E6EA]/20 dark:hover:bg-neutral-700/20"
                          >
                            <td className="px-4 md:px-6 py-3.5 font-medium text-gray-900 dark:text-gray-100">
                              {p.nome}
                            </td>
                            <td className="px-4 md:px-6 py-3.5 text-gray-600 dark:text-gray-400 whitespace-nowrap">
                              R$ {Number(p.preco || 0).toFixed(2)}
                            </td>
                            <td className="px-4 md:px-6 py-3.5">
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
                            <td className="px-4 md:px-6 py-3.5">
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                max={linha.modo === "percentual" ? "100" : undefined}
                                value={linha.valor}
                                onChange={(e) => updateLinha(p.id, { valor: e.target.value })}
                                placeholder="—"
                                className="w-full max-w-[120px] px-2 py-1.5 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
                              />
                            </td>
                            <td className="px-4 md:px-6 py-3.5 text-gray-700 dark:text-gray-300 whitespace-nowrap">
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
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  /* ── Lista em tela cheia ── */
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Convênios"
        subtitle="Planos com preço fixo ou percentual sobre o valor particular"
        newLabel="Novo convênio"
        onNew={abrirNovo}
        icon={FileText}
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <div className="text-center py-20 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : convenios.length === 0 ? (
          <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 p-12 text-center text-gray-500 dark:text-gray-400 shadow-sm">
            Nenhum convênio cadastrado. Clique em &quot;Novo convênio&quot; para começar.
          </div>
        ) : (
          <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm overflow-hidden w-full">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-neutral-900/80 text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700">
                  <tr>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Nome</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold hidden sm:table-cell">Código</th>
                    <th className="text-right px-4 md:px-6 py-3.5 font-semibold w-40">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {convenios.map((c) => (
                    <tr
                      key={c.id}
                      className="border-t border-gray-100 dark:border-neutral-700/80 hover:bg-[#F5E6EA]/40 dark:hover:bg-neutral-700/30 transition-colors cursor-pointer"
                      onClick={() => abrirEditar(c)}
                    >
                      <td className="px-4 md:px-6 py-4 font-medium text-gray-900 dark:text-gray-100">
                        {c.nome}
                      </td>
                      <td className="px-4 md:px-6 py-4 text-gray-600 dark:text-gray-400 hidden sm:table-cell">
                        {c.codigo || "—"}
                      </td>
                      <td className="px-4 md:px-6 py-4">
                        <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            onClick={() => abrirEditar(c)}
                            className="p-2 rounded-lg hover:bg-[#F5E6EA] dark:hover:bg-neutral-600 transition-colors"
                            style={{ color: CLINICA_BELEZA_PRIMARY }}
                            title="Editar preços"
                          >
                            <Pencil size={18} />
                          </button>
                          <button
                            type="button"
                            onClick={() => excluirConvenio(c)}
                            disabled={salvando}
                            className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            title="Excluir convênio"
                          >
                            <Trash2 size={18} />
                          </button>
                          <ChevronRight size={18} className="text-gray-400 ml-1 hidden md:inline self-center" />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {erro && (
          <p className="mt-4 text-sm text-red-600 dark:text-red-400">{erro}</p>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
