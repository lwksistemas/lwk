"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, Loader2, Plus } from "lucide-react";
import type { CategoriaEstoque, ProdutoEstoque } from "./produtos-types";
import { PRODUTOS_INPUT_CLASS } from "./produtos-types";

function categoriaSlug(p: ProdutoEstoque): string {
  return p.categoria_slug || "outro";
}

function categoriaDisplay(p: ProdutoEstoque): string {
  return p.categoria_display || "Outros";
}

export function ProdutoAdicionarForm({
  produtos,
  produtosPorCategoria,
  produtoId,
  quantidade,
  lote,
  validade,
  erro,
  erroEstoque,
  avisoFormulario,
  saving,
  onProdutoChange,
  onQuantidadeChange,
  onLoteChange,
  onValidadeChange,
  onClose,
  onAdicionar,
}: {
  produtos: ProdutoEstoque[];
  produtosPorCategoria?: {
    comCategoria: { categoria: CategoriaEstoque; produtos: ProdutoEstoque[] }[];
    semCategoria: ProdutoEstoque[];
  };
  produtoId: number | "";
  quantidade: string;
  lote: string;
  validade: string;
  erro: string;
  erroEstoque: string;
  avisoFormulario: string;
  saving: boolean;
  onProdutoChange: (id: number | "") => void;
  onQuantidadeChange: (v: string) => void;
  onLoteChange: (v: string) => void;
  onValidadeChange: (v: string) => void;
  onClose: () => void;
  onAdicionar: () => void;
}) {
  const [categoriaAtiva, setCategoriaAtiva] = useState("");

  const categoriasDisponiveis = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of produtos) {
      const slug = categoriaSlug(p);
      counts.set(slug, (counts.get(slug) || 0) + 1);
    }

    const cards: { value: string; label: string; count: number }[] = [];

    if (produtosPorCategoria) {
      for (const { categoria, produtos: grupo } of produtosPorCategoria.comCategoria) {
        cards.push({ value: categoria.slug, label: categoria.nome, count: grupo.length });
      }
      if (produtosPorCategoria.semCategoria.length > 0) {
        cards.push({
          value: "outro",
          label: "Outros",
          count: produtosPorCategoria.semCategoria.length,
        });
      }
    } else {
      for (const [slug, count] of counts) {
        const exemplo = produtos.find((p) => categoriaSlug(p) === slug);
        cards.push({ value: slug, label: categoriaDisplay(exemplo || {} as ProdutoEstoque), count });
      }
    }

    return cards.sort((a, b) => a.label.localeCompare(b.label));
  }, [produtos, produtosPorCategoria]);

  const filtrados = useMemo(() => {
    if (!categoriaAtiva) return produtos;
    return produtos.filter((p) => categoriaSlug(p) === categoriaAtiva);
  }, [produtos, categoriaAtiva]);

  return (
    <div className="p-3 rounded-lg border border-gray-200 dark:border-neutral-700 bg-gray-50/80 dark:bg-neutral-800/40 space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
          Incluir produto
        </label>
        <button type="button" onClick={onClose} className="text-xs text-gray-500 hover:text-gray-700">
          Fechar
        </button>
      </div>

      {erroEstoque && (
        <p className="text-sm text-red-600 dark:text-red-400">{erroEstoque}</p>
      )}

      {categoriasDisponiveis.length > 1 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => {
              setCategoriaAtiva("");
              onProdutoChange("");
            }}
            className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              !categoriaAtiva
                ? "text-white border-transparent"
                : "border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-300"
            }`}
            style={!categoriaAtiva ? { backgroundColor: "var(--cb-primary, #8B3D52)" } : undefined}
          >
            Todas
          </button>
          {categoriasDisponiveis.map((cat) => (
            <button
              key={cat.value}
              type="button"
              onClick={() => {
                setCategoriaAtiva(cat.value);
                onProdutoChange("");
              }}
              className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                categoriaAtiva === cat.value
                  ? "text-white border-transparent"
                  : "border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-300"
              }`}
              style={
                categoriaAtiva === cat.value
                  ? { backgroundColor: "var(--cb-primary, #8B3D52)" }
                  : undefined
              }
            >
              {cat.label} ({cat.count})
            </button>
          ))}
        </div>
      )}

      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
          Produto *
        </label>
        <select
          value={produtoId}
          onChange={(e) => onProdutoChange(e.target.value ? Number(e.target.value) : "")}
          className={PRODUTOS_INPUT_CLASS}
          disabled={!!erroEstoque || produtos.length === 0}
        >
          <option value="">
            {erroEstoque
              ? "Estoque indisponível"
              : produtos.length === 0
                ? "Nenhum produto cadastrado no estoque"
                : categoriaAtiva
                  ? `Selecione de ${categoriasDisponiveis.find((c) => c.value === categoriaAtiva)?.label || "..."}...`
                  : "Selecione..."}
          </option>
          {filtrados.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nome} — disp. {Number(p.quantidade_atual)} {p.unidade_medida || "un"}
              {!categoriaAtiva && p.categoria_display ? ` · ${p.categoria_display}` : ""}
            </option>
          ))}
        </select>
      </div>

      {produtoId && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              Quantidade usada *
            </label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={quantidade}
              onChange={(e) => onQuantidadeChange(e.target.value)}
              className={PRODUTOS_INPUT_CLASS}
            />
            {avisoFormulario && (
              <p className="mt-1.5 text-xs text-amber-700 dark:text-amber-300 flex items-start gap-1">
                <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                {avisoFormulario} A finalização será bloqueada até regularizar o estoque.
              </p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Nº do lote</label>
            <input
              type="text"
              value={lote}
              onChange={(e) => onLoteChange(e.target.value)}
              className={PRODUTOS_INPUT_CLASS}
              placeholder="Lote do produto"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Validade</label>
            <input
              type="date"
              value={validade}
              onChange={(e) => onValidadeChange(e.target.value)}
              className={PRODUTOS_INPUT_CLASS}
            />
          </div>
        </div>
      )}

      {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onAdicionar}
          disabled={saving || !produtoId}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white disabled:opacity-50"
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
          {saving ? "Salvando..." : "Adicionar"}
        </button>
        <button
          type="button"
          onClick={onClose}
          disabled={saving}
          className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
