"use client";

import { useState } from "react";
import { X } from "lucide-react";
import {
  ESTOQUE_CATEGORIAS,
  ESTOQUE_INPUT_CLASS,
  normalizeEstoqueCategoria,
  type EstoqueProduto,
} from "@/components/clinica-beleza/estoque/estoque-types";
import { toUpperCase } from "@/lib/format-br";

interface Props {
  produto: EstoqueProduto | null;
  saving: boolean;
  saveError: string | null;
  onClose: () => void;
  onSave: (payload: Record<string, unknown>) => Promise<void>;
}

export function EstoqueProdutoModal({ produto, saving, saveError, onClose, onSave }: Props) {
  const [form, setForm] = useState({
    nome: produto?.nome ?? "",
    marca: produto?.marca ?? "",
    categoria: normalizeEstoqueCategoria(produto?.categoria),
    quantidade_atual: produto?.quantidade_atual ?? 0,
    quantidade_minima: produto?.quantidade_minima ?? 0,
    preco_custo: produto ? Number(produto.preco_custo) : 0,
    validade: produto?.validade ? String(produto.validade).slice(0, 10) : "",
    lote: produto?.lote ?? "",
    numero_nota: produto?.numero_nota ?? "",
    dias_alerta_validade: produto?.dias_alerta_validade ?? 90,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave({
      ...form,
      preco_custo: Number(form.preco_custo),
      validade: form.validade || null,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            {produto ? "Editar Produto" : "Novo Produto"}
          </h2>
          <button type="button" onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded">
            <X size={20} className="text-gray-500 dark:text-gray-400" />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-200 dark:divide-neutral-700">
            <div className="p-5 space-y-4">
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
                  value={form.categoria}
                  onChange={(e) => setForm({ ...form, categoria: e.target.value })}
                  className={ESTOQUE_INPUT_CLASS}
                >
                  {ESTOQUE_CATEGORIAS.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantidade</label>
                  <input
                    type="number"
                    min={0}
                    value={form.quantidade_atual}
                    onChange={(e) => setForm({ ...form, quantidade_atual: Number(e.target.value) })}
                    className={ESTOQUE_INPUT_CLASS}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mínimo</label>
                  <input
                    type="number"
                    min={0}
                    value={form.quantidade_minima}
                    onChange={(e) => setForm({ ...form, quantidade_minima: Number(e.target.value) })}
                    className={ESTOQUE_INPUT_CLASS}
                  />
                </div>
              </div>
            </div>
            <div className="p-5 space-y-4">
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nº do lote</label>
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
                    Preço Custo (R$)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min={0}
                    value={form.preco_custo}
                    onChange={(e) => setForm({ ...form, preco_custo: Number(e.target.value) })}
                    className={ESTOQUE_INPUT_CLASS}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Validade</label>
                  <input
                    type="date"
                    value={form.validade}
                    onChange={(e) => setForm({ ...form, validade: e.target.value })}
                    className={ESTOQUE_INPUT_CLASS}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Dias para alerta de validade
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
                <p className="text-xs text-gray-500 mt-1">Alerta quando faltar esse nº de dias para vencer</p>
              </div>
              {saveError && (
                <div className="px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
                  {saveError}
                </div>
              )}
              <button
                type="submit"
                disabled={saving}
                className="w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 font-medium text-sm mt-2"
              >
                {saving ? "Salvando..." : produto ? "Salvar Alterações" : "Criar Produto"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
