"use client";

import { useState } from "react";
import { X } from "lucide-react";
import {
  ESTOQUE_CATEGORIAS,
  ESTOQUE_INPUT_CLASS,
  ESTOQUE_UNIDADES_MEDIDA,
  type EstoqueCategoria,
  type EstoqueProduto,
} from "@/components/clinica-beleza/estoque/estoque-types";
import { toUpperCase } from "@/lib/format-br";
import { EstoqueProdutoCompras } from "./EstoqueProdutoCompras";

interface Props {
  produto: EstoqueProduto | null;
  categorias?: EstoqueCategoria[];
  defaultCategoriaSlug?: string;
  saving: boolean;
  saveError: string | null;
  onClose: () => void;
  onSave: (payload: Record<string, unknown>) => Promise<void>;
}

function resolveInitialCategoriaId(
  produto: EstoqueProduto | null,
  categorias: EstoqueCategoria[] | undefined,
  defaultSlug?: string,
): number | "" {
  if (produto?.categoria != null) return produto.categoria;
  if (produto?.categoria_slug && categorias?.length) {
    const found = categorias.find((c) => c.slug === produto.categoria_slug);
    if (found) return found.id;
  }
  if (defaultSlug && categorias?.length) {
    const found = categorias.find((c) => c.slug === defaultSlug);
    if (found) return found.id;
  }
  if (categorias?.length) {
    const outro = categorias.find((c) => c.slug === "outro");
    return outro?.id ?? categorias[0].id;
  }
  return "";
}

export function EstoqueProdutoModal({
  produto,
  categorias,
  defaultCategoriaSlug,
  saving,
  saveError,
  onClose,
  onSave,
}: Props) {
  const [form, setForm] = useState({
    nome: produto?.nome ?? "",
    marca: produto?.marca ?? "",
    categoria_id: resolveInitialCategoriaId(produto, categorias, defaultCategoriaSlug) as number | "",
    unidade_medida: (produto?.unidade_medida || "unidade").trim() || "unidade",
    quantidade_atual: produto?.quantidade_atual ?? 0,
    quantidade_minima: produto?.quantidade_minima ?? 0,
    preco_custo: produto ? Number(produto.preco_custo) : 0,
    preco_venda: produto ? Number(produto.preco_venda || 0) : 0,
    vende_ao_cliente: produto?.vende_ao_cliente ?? false,
    ncm: produto?.ncm ?? "",
    validade: produto?.validade ? String(produto.validade).slice(0, 10) : "",
    lote: produto?.lote ?? "",
    numero_nota: produto?.numero_nota ?? "",
    dias_alerta_validade: produto?.dias_alerta_validade ?? 90,
    exige_lote: produto?.exige_lote ?? false,
  });
  const unidadeAtual = form.unidade_medida.trim() || "unidade";

  const options =
    categorias && categorias.length > 0
      ? categorias.map((c) => ({ value: c.id, label: c.nome }))
      : ESTOQUE_CATEGORIAS.map((c, i) => ({ value: i + 1, label: c.label }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: Record<string, unknown> = {
      nome: form.nome,
      marca: form.marca,
      unidade_medida: unidadeAtual.slice(0, 30),
      quantidade_atual: form.quantidade_atual,
      quantidade_minima: form.quantidade_minima,
      preco_custo: Number(form.preco_custo),
      preco_venda: Number(form.preco_venda),
      vende_ao_cliente: form.vende_ao_cliente,
      ncm: form.ncm.replace(/\D/g, ""),
      validade: form.validade || null,
      lote: form.lote,
      numero_nota: form.numero_nota,
      dias_alerta_validade: form.dias_alerta_validade,
      exige_lote: form.exige_lote,
    };
    if (form.categoria_id !== "") {
      payload.categoria = form.categoria_id;
    }
    await onSave(payload);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-3 sm:p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 sm:px-6 py-3 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {produto ? "Editar Produto" : "Novo Produto"}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Mesmas informações da conferência do Importar XML: unidade de estoque, quantidade, lote,
              validade, custo e fator da nota.
            </p>
          </div>
          <button type="button" onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded">
            <X size={20} className="text-gray-500 dark:text-gray-400" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col min-h-0 flex-1">
          <div className="overflow-y-auto flex-1">
            <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-gray-200 dark:divide-neutral-700">
              <div className="p-4 sm:p-5 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  Identificação
                </p>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome</label>
                  <input
                    type="text"
                    required
                    value={form.nome}
                    onChange={(e) => setForm({ ...form, nome: toUpperCase(e.target.value) })}
                    className={ESTOQUE_INPUT_CLASS}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fornecedor</label>
                  <input
                    type="text"
                    value={form.marca}
                    onChange={(e) => setForm({ ...form, marca: toUpperCase(e.target.value) })}
                    className={ESTOQUE_INPUT_CLASS}
                    placeholder="Nome do fornecedor"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
                  <select
                    value={form.categoria_id === "" ? "" : String(form.categoria_id)}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        categoria_id: e.target.value ? Number(e.target.value) : "",
                      })
                    }
                    className={ESTOQUE_INPUT_CLASS}
                    required
                  >
                    <option value="" disabled>
                      Selecione
                    </option>
                    {options.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Preço custo (R$)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min={0}
                      value={form.preco_custo}
                      onChange={(e) => setForm({ ...form, preco_custo: Number(e.target.value) })}
                      className={ESTOQUE_INPUT_CLASS}
                    />
                    <p className="text-[11px] text-gray-500 mt-1">Custo unitário no estoque (como no XML).</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Preço de venda (R$)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min={0}
                      value={form.preco_venda}
                      onChange={(e) => setForm({ ...form, preco_venda: Number(e.target.value) })}
                      className={ESTOQUE_INPUT_CLASS}
                    />
                  </div>
                </div>
                <label className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={form.vende_ao_cliente}
                    onChange={(e) => setForm({ ...form, vende_ao_cliente: e.target.checked })}
                  />
                  <span>
                    Pode vender ao cliente
                    <span className="block text-xs text-gray-500">
                      A importação da nota atualiza o custo e não mexe neste preço.
                    </span>
                  </span>
                </label>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    NCM do cupom fiscal
                  </label>
                  <input
                    inputMode="numeric"
                    maxLength={8}
                    placeholder="8 dígitos, se este produto for vendido"
                    value={form.ncm}
                    onChange={(e) => setForm({ ...form, ncm: e.target.value.replace(/\D/g, "").slice(0, 8) })}
                    className={ESTOQUE_INPUT_CLASS}
                  />
                </div>
              </div>

              <div className="p-4 sm:p-5 space-y-3 bg-violet-50/40 dark:bg-violet-950/10">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  Entrada no estoque (igual ao XML)
                </p>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Unidade de medida (estoque)
                  </label>
                  <input
                    type="text"
                    list="estoque-unidades-medida"
                    value={form.unidade_medida}
                    onChange={(e) => setForm({ ...form, unidade_medida: e.target.value.toLowerCase() })}
                    className={ESTOQUE_INPUT_CLASS}
                    placeholder="unidade, ampola, frasco, dose, ml…"
                    maxLength={30}
                    required
                  />
                  <datalist id="estoque-unidades-medida">
                    {ESTOQUE_UNIDADES_MEDIDA.map((u) => (
                      <option key={u} value={u} />
                    ))}
                  </datalist>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Quantidade ({unidadeAtual})
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={form.quantidade_atual}
                      onChange={(e) => setForm({ ...form, quantidade_atual: Number(e.target.value) })}
                      className={ESTOQUE_INPUT_CLASS}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Mínimo ({unidadeAtual})
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={form.quantidade_minima}
                      onChange={(e) => setForm({ ...form, quantidade_minima: Number(e.target.value) })}
                      className={ESTOQUE_INPUT_CLASS}
                    />
                  </div>
                </div>
                <div className="rounded-lg border border-violet-200 dark:border-violet-900/50 bg-white/70 dark:bg-neutral-900/40 px-3 py-2 text-xs text-gray-600 dark:text-gray-300 space-y-1">
                  <p>
                    No <strong>Importar XML</strong>: quantidade da nota × <strong>fator</strong> = entrada em{" "}
                    <strong>{unidadeAtual}</strong>.
                  </p>
                  <p>
                    Ex.: nota em ml e uso em unidade → ajuste o fator na conferência do XML. Aqui você define a
                    unidade do saldo e das baixas no procedimento.
                  </p>
                  <p className="text-gray-500">
                    O fator por fornecedor aparece no histórico abaixo (lembrado da última NF-e).
                  </p>
                </div>
              </div>

              <div className="p-4 sm:p-5 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  Rastreabilidade
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Nº nota fiscal
                    </label>
                    <input
                      type="text"
                      value={form.numero_nota}
                      onChange={(e) => setForm({ ...form, numero_nota: e.target.value })}
                      className={ESTOQUE_INPUT_CLASS}
                      placeholder="Ex: 12345"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Nº do lote
                    </label>
                    <input
                      type="text"
                      value={form.lote}
                      onChange={(e) => setForm({ ...form, lote: e.target.value })}
                      className={ESTOQUE_INPUT_CLASS}
                      placeholder="Lote do produto"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Validade
                    </label>
                    <input
                      type="date"
                      value={form.validade}
                      onChange={(e) => setForm({ ...form, validade: e.target.value })}
                      className={ESTOQUE_INPUT_CLASS}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Dias alerta validade
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={365}
                      value={form.dias_alerta_validade}
                      onChange={(e) => setForm({ ...form, dias_alerta_validade: Number(e.target.value) })}
                      className={ESTOQUE_INPUT_CLASS}
                      placeholder="90"
                    />
                  </div>
                </div>
                <label className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={form.exige_lote}
                    onChange={(e) => setForm({ ...form, exige_lote: e.target.checked })}
                  />
                  <span>
                    Exigir lote e validade na entrada
                    <span className="block text-xs text-gray-500">
                      Na NF-e, igual à conferência do XML: sem lote/validade o item não confirma.
                    </span>
                  </span>
                </label>
              </div>
            </div>

            {produto?.id ? (
              <EstoqueProdutoCompras produtoId={produto.id} />
            ) : (
              <div className="px-5 py-3 border-t border-gray-200 dark:border-neutral-700">
                <p className="text-xs text-gray-500">
                  Ao importar XML, use o fator para converter a unidade da nota para{" "}
                  <span className="font-medium text-gray-700 dark:text-gray-200">{unidadeAtual}</span>.
                </p>
              </div>
            )}
          </div>

          <div className="shrink-0 border-t border-gray-200 dark:border-neutral-700 px-5 py-3 flex flex-wrap items-center justify-end gap-3 bg-white dark:bg-neutral-800">
            {saveError && (
              <p className="flex-1 text-sm text-red-600 dark:text-red-300 min-w-[12rem]">{saveError}</p>
            )}
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 text-white rounded-lg disabled:opacity-50 font-medium text-sm"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              {saving ? "Salvando..." : produto ? "Salvar Alterações" : "Criar Produto"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
