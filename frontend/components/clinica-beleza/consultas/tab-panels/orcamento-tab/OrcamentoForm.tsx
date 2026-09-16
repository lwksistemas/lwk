"use client";

import { Trash2 } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { toUpperCase } from "@/lib/format-br";
import {
  procedureCategoriaLabel,
  procedureItemCategoriaSlug,
  procedureSelectLabel,
} from "@/lib/clinica-beleza-categories";
import {
  ProcedimentoCategoriaChips,
  useProcedimentoCategoriaFiltro,
} from "../../procedimentos-consulta/procedimento-categoria-filtro";
import type { ItemForm, Procedure } from "./types";

interface OrcamentoFormProps {
  procedures: Procedure[];
  itensForm: ItemForm[];
  observacoes: string;
  selectedProc: string;
  valorCustom: string;
  quantidade: string;
  showProcSelector: boolean;
  criando: boolean;
  onSelectedProc: (value: string) => void;
  onValorCustom: (value: string) => void;
  onQuantidade: (value: string) => void;
  onAdicionar: () => void;
  onRemover: (idx: number) => void;
  onObservacoes: (value: string) => void;
  onShowProcSelector: (show: boolean) => void;
  onCancelar: () => void;
  onCriar: () => void;
}

export function OrcamentoForm({
  procedures,
  itensForm,
  observacoes,
  selectedProc,
  valorCustom,
  quantidade,
  showProcSelector,
  criando,
  onSelectedProc,
  onValorCustom,
  onQuantidade,
  onAdicionar,
  onRemover,
  onObservacoes,
  onShowProcSelector,
  onCancelar,
  onCriar,
}: OrcamentoFormProps) {
  const { categoriaAtiva, setCategoriaAtiva, categoriasDisponiveis, filtrados } =
    useProcedimentoCategoriaFiltro(procedures);
  const totalForm = itensForm.reduce((acc, it) => acc + Number(it.valor) * it.qtd, 0);

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-4">
      <h4 className="font-medium text-gray-900 dark:text-white">Novo Orçamento</h4>

      {itensForm.length === 0 || showProcSelector ? (
        <div className="space-y-2">
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
            Incluir procedimento
          </label>
          <ProcedimentoCategoriaChips
            categoriasDisponiveis={categoriasDisponiveis}
            categoriaAtiva={categoriaAtiva}
            onChange={(slug) => {
              setCategoriaAtiva(slug);
              onSelectedProc("");
              onValorCustom("");
            }}
          />
          <div className="flex flex-wrap gap-2 items-end">
            <div className="flex-1 min-w-[200px]">
              <select
                value={selectedProc}
                onChange={(e) => {
                  onSelectedProc(e.target.value);
                  const p = procedures.find((pr) => pr.id === Number(e.target.value));
                  if (p) onValorCustom(p.preco);
                }}
                className="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-600"
              >
                <option value="">
                  {categoriaAtiva
                    ? `Selecione de ${procedureCategoriaLabel(categoriaAtiva)}...`
                    : "Selecione..."}
                </option>
                {filtrados.map((p) => (
                  <option key={p.id} value={p.id}>
                    {procedureSelectLabel(toUpperCase(p.nome), procedureItemCategoriaSlug(p), {
                      includeCategorySuffix: !categoriaAtiva,
                    })}{" "}
                    — R$ {Number(p.preco).toFixed(2)}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-28">
              <label className="block text-xs text-gray-500 mb-1">Valor (R$)</label>
              <input
                type="number"
                step="0.01"
                value={valorCustom}
                onChange={(e) => onValorCustom(e.target.value)}
                className="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-600"
              />
            </div>
            <div className="w-16">
              <label className="block text-xs text-gray-500 mb-1">Qtd</label>
              <input
                type="number"
                min="1"
                value={quantidade}
                onChange={(e) => onQuantidade(e.target.value)}
                className="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-600"
              />
            </div>
            <button
              type="button"
              onClick={() => {
                onAdicionar();
                onShowProcSelector(false);
              }}
              disabled={!selectedProc}
              className="px-3 py-2 text-sm bg-green-600 text-white rounded-lg disabled:opacity-50"
            >
              Adicionar
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => onShowProcSelector(true)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          + Adicionar mais procedimentos
        </button>
      )}

      {itensForm.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-3 py-2 text-left">Procedimento</th>
                <th className="px-3 py-2 text-right">Valor</th>
                <th className="px-3 py-2 text-center">Qtd</th>
                <th className="px-3 py-2 text-right">Subtotal</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {itensForm.map((it, idx) => (
                <tr key={idx} className="border-t">
                  <td className="px-3 py-2">{it.nome}</td>
                  <td className="px-3 py-2 text-right">{formatCurrency(it.valor)}</td>
                  <td className="px-3 py-2 text-center">{it.qtd}</td>
                  <td className="px-3 py-2 text-right font-medium">
                    {formatCurrency(Number(it.valor) * it.qtd)}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <button type="button" onClick={() => onRemover(idx)} className="text-red-500 hover:text-red-700">
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t bg-gray-50 dark:bg-gray-700">
                <td colSpan={3} className="px-3 py-2 font-bold text-right">TOTAL:</td>
                <td className="px-3 py-2 text-right font-bold">{formatCurrency(totalForm)}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      <div>
        <label className="block text-xs text-gray-500 mb-1">Observações (opcional)</label>
        <textarea
          value={observacoes}
          onChange={(e) => onObservacoes(e.target.value)}
          rows={5}
          className="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-600"
          placeholder="Condições de pagamento, validade especial... (aparecem no PDF; o WhatsApp envia só o resumo + anexo)"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={onCancelar}
          className="px-4 py-2 text-sm border rounded-lg"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={onCriar}
          disabled={criando || itensForm.length === 0}
          className="px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50"
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          {criando ? "Criando..." : "Criar Orçamento"}
        </button>
      </div>
    </div>
  );
}
