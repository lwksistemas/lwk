"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatClinicaDataCurta } from "@/lib/clinica-beleza-datetime";
import { imprimirConsultaPdf, type ConsultaPrintMeta } from "@/lib/consulta-print";
import { ConsultaPrintButton } from "./ConsultaPrintButton";

export interface ConsultaProdutoItem {
  id: number;
  produto: number;
  produto_nome: string;
  quantidade: number | string;
  lote: string;
  validade: string | null;
  unidade_medida?: string;
  quantidade_disponivel?: number | string;
  estoque_baixado?: boolean;
}

interface ProdutoEstoque {
  id: number;
  nome: string;
  lote?: string;
  validade?: string | null;
  quantidade_atual: number | string;
  unidade_medida?: string;
}

const inputClass =
  "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";

export function ConsultaProdutosTab({
  consultaId,
  somenteLeitura,
  printMeta,
  onItensChanged,
}: {
  consultaId: number;
  somenteLeitura: boolean;
  printMeta: ConsultaPrintMeta;
  onItensChanged?: () => void;
}) {
  const [itens, setItens] = useState<ConsultaProdutoItem[]>([]);
  const [produtos, setProdutos] = useState<ProdutoEstoque[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [produtoId, setProdutoId] = useState<number | "">("");
  const [quantidade, setQuantidade] = useState<string>("1");
  const [lote, setLote] = useState("");
  const [validade, setValidade] = useState("");
  const [erro, setErro] = useState("");
  const [erroEstoque, setErroEstoque] = useState("");

  const extractApiError = (err: unknown, fallback: string) => {
    if (err && typeof err === "object" && "error" in err) {
      return String((err as { error: string }).error);
    }
    if (err && typeof err === "object" && "detail" in err) {
      return String((err as { detail: string }).detail);
    }
    return fallback;
  };

  const carregar = useCallback(async () => {
    setLoading(true);
    setErroEstoque("");

    const listaPromise = ClinicaBelezaAPI.consultas.produtos
      .list(consultaId)
      .then((lista) => {
        setItens(Array.isArray(lista) ? lista : []);
      })
      .catch(() => {
        setItens([]);
      });

    const estoquePromise = ClinicaBelezaAPI.estoque
      .list()
      .then((estoque) => {
        setProdutos(Array.isArray(estoque) ? (estoque as ProdutoEstoque[]) : []);
      })
      .catch((err: unknown) => {
        setProdutos([]);
        setErroEstoque(extractApiError(err, "Não foi possível carregar os produtos do estoque."));
      });

    await Promise.all([listaPromise, estoquePromise]);
    setLoading(false);
  }, [consultaId]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const onProdutoChange = (id: number | "") => {
    setProdutoId(id);
    if (!id) {
      setLote("");
      setValidade("");
      return;
    }
    const p = produtos.find((x) => x.id === id);
    if (p) {
      setLote(p.lote || "");
      setValidade(p.validade ? String(p.validade).slice(0, 10) : "");
    }
  };

  const adicionar = async () => {
    if (!produtoId) {
      setErro("Selecione um produto.");
      return;
    }
    const qtd = Number(quantidade);
    if (!qtd || qtd <= 0) {
      setErro("Informe a quantidade utilizada.");
      return;
    }
    setSaving(true);
    setErro("");
    try {
      const res = await ClinicaBelezaAPI.consultas.produtos.add(consultaId, {
        produto: Number(produtoId),
        quantidade: qtd,
        lote: lote.trim() || undefined,
        validade: validade || undefined,
      }) as { error?: string };
      if (res?.error) throw res;
      setProdutoId("");
      setQuantidade("1");
      setLote("");
      setValidade("");
      await carregar();
      onItensChanged?.();
    } catch (e: unknown) {
      setErro(extractApiError(e, "Erro ao registrar produto."));
    } finally {
      setSaving(false);
    }
  };

  const remover = async (item: ConsultaProdutoItem) => {
    if (!confirm(`Remover ${item.produto_nome} da consulta?`)) return;
    setSaving(true);
    try {
      await ClinicaBelezaAPI.consultas.produtos.remove(consultaId, item.id);
      await carregar();
      onItensChanged?.();
    } catch {
      alert("Não foi possível remover o produto.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-gray-500 text-sm">Carregando produtos...</div>;
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Registre os produtos utilizados no atendimento. Ao <strong>finalizar a consulta</strong>, a quantidade será
        baixada automaticamente do estoque.
      </p>

      {!somenteLeitura && (
        <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 space-y-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Adicionar produto</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Produto *</label>
              {erroEstoque && (
                <p className="text-sm text-red-600 dark:text-red-400 mb-2">{erroEstoque}</p>
              )}
              <select
                value={produtoId}
                onChange={(e) => onProdutoChange(e.target.value ? Number(e.target.value) : "")}
                className={inputClass}
                disabled={!!erroEstoque || produtos.length === 0}
              >
                <option value="">
                  {erroEstoque
                    ? "Estoque indisponível"
                    : produtos.length === 0
                      ? "Nenhum produto cadastrado no estoque"
                      : "Selecione..."}
                </option>
                {produtos.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome} — disp. {Number(p.quantidade_atual)} {p.unidade_medida || "un"}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Quantidade usada *</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={quantidade}
                onChange={(e) => setQuantidade(e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Nº do lote</label>
              <input type="text" value={lote} onChange={(e) => setLote(e.target.value)} className={inputClass} placeholder="Lote do produto" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Validade</label>
              <input type="date" value={validade} onChange={(e) => setValidade(e.target.value)} className={inputClass} />
            </div>
          </div>
          {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
          <button
            type="button"
            onClick={adicionar}
            disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            <Plus size={16} />
            {saving ? "Salvando..." : "Adicionar"}
          </button>
        </div>
      )}

      {itens.length === 0 ? (
        <div className="text-center py-10 text-gray-500 text-sm rounded-xl border border-dashed border-gray-200 dark:border-neutral-700">
          Nenhum produto registrado nesta consulta.
        </div>
      ) : (
        <div className="rounded-xl border border-gray-200 dark:border-neutral-700 overflow-hidden">
          <div className="flex justify-end p-3 border-b border-gray-100 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-800/50">
            <ConsultaPrintButton
              label="Imprimir lista"
              onPrint={() => imprimirConsultaPdf(printMeta.consultaId, "produtos")}
            />
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-neutral-800 text-gray-600 dark:text-gray-300">
              <tr>
                <th className="text-left p-3">Produto</th>
                <th className="text-left p-3">Qtd</th>
                <th className="text-left p-3 hidden sm:table-cell">Lote</th>
                <th className="text-left p-3 hidden md:table-cell">Validade</th>
                {!somenteLeitura && <th className="w-12 p-3" />}
              </tr>
            </thead>
            <tbody>
              {itens.map((item) => (
                <tr key={item.id} className="border-t border-gray-100 dark:border-neutral-700">
                  <td className="p-3 font-medium text-gray-800 dark:text-gray-200">{item.produto_nome}</td>
                  <td className="p-3 text-gray-700 dark:text-gray-300">
                    {Number(item.quantidade)} {item.unidade_medida || ""}
                  </td>
                  <td className="p-3 hidden sm:table-cell text-gray-600 dark:text-gray-400">{item.lote || "—"}</td>
                  <td className="p-3 hidden md:table-cell text-gray-600 dark:text-gray-400">
                    {item.validade
                      ? formatClinicaDataCurta(new Date(String(item.validade).slice(0, 10) + "T00:00:00"))
                      : "—"}
                  </td>
                  {!somenteLeitura && (
                    <td className="p-3">
                      <button
                        type="button"
                        onClick={() => remover(item)}
                        disabled={saving || item.estoque_baixado}
                        className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-40"
                        title="Remover"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
