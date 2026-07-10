"use client";

import { useMemo, type ReactNode } from "react";
import { AlertTriangle, ArrowDown, ArrowUp, X } from "lucide-react";
import {
  estoqueCategoriaLabel,
  type EstoqueProduto,
  type EstoqueResumo,
} from "@/components/clinica-beleza/estoque/estoque-types";
import { DEFAULT_COLUNAS_ESTOQUE } from "@/lib/clinica-estoque-colunas-config";
import { formatClinicaDataCurta } from "@/lib/clinica-beleza-datetime";
import { formatCurrency } from "@/lib/financeiro-helpers";

function StatusBadge({ produto }: { produto: EstoqueProduto }) {
  const baixo = produto.quantidade_atual <= produto.quantidade_minima;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
        baixo
          ? "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300"
          : "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
      }`}
    >
      {baixo && <AlertTriangle size={12} />}
      {baixo ? "Estoque baixo" : "OK"}
    </span>
  );
}

type ColumnDef = {
  key: string;
  header: string;
  thClassName?: string;
  tdClassName?: string;
  render: (p: EstoqueProduto) => ReactNode;
};

interface Props {
  produtos: EstoqueProduto[];
  resumo: EstoqueResumo | null;
  onHistorico: (produto: EstoqueProduto) => void;
  onEditar: (produto: EstoqueProduto) => void;
  onEntrada: (produto: EstoqueProduto) => void;
  onSaida: (produto: EstoqueProduto) => void;
  onExcluir: (id: number, nome: string) => void;
  colunasVisiveis?: string[];
}

const TH_BASE = "py-3 px-4 font-semibold text-gray-700 dark:text-gray-300";
const TD_BASE = "py-3 px-4";

function buildColumnRegistry(): Record<string, ColumnDef> {
  return {
    nome: {
      key: "nome",
      header: "Nome",
      thClassName: `text-left ${TH_BASE}`,
      tdClassName: `${TD_BASE} font-medium text-gray-900 dark:text-gray-100`,
      render: (p) => p.nome,
    },
    marca: {
      key: "marca",
      header: "Fornecedor",
      thClassName: `text-left ${TH_BASE} hidden md:table-cell`,
      tdClassName: `${TD_BASE} text-gray-600 dark:text-gray-300 hidden md:table-cell`,
      render: (p) => p.marca || "—",
    },
    categoria: {
      key: "categoria",
      header: "Categoria",
      thClassName: `text-left ${TH_BASE}`,
      tdClassName: `${TD_BASE} text-gray-600 dark:text-gray-300`,
      render: (p) => estoqueCategoriaLabel(p.categoria),
    },
    quantidade_atual: {
      key: "quantidade_atual",
      header: "Qtd",
      thClassName: `text-right ${TH_BASE}`,
      tdClassName: `${TD_BASE} text-right font-medium text-gray-900 dark:text-gray-100`,
      render: (p) => p.quantidade_atual,
    },
    quantidade_minima: {
      key: "quantidade_minima",
      header: "Mínimo",
      thClassName: `text-right ${TH_BASE} hidden sm:table-cell`,
      tdClassName: `${TD_BASE} text-right text-gray-600 dark:text-gray-300 hidden sm:table-cell`,
      render: (p) => p.quantidade_minima,
    },
    preco_custo: {
      key: "preco_custo",
      header: "Preço Custo",
      thClassName: `text-right ${TH_BASE}`,
      tdClassName: `${TD_BASE} text-right text-gray-600 dark:text-gray-300`,
      render: (p) => formatCurrency(p.preco_custo),
    },
    lote: {
      key: "lote",
      header: "Lote",
      thClassName: `text-left ${TH_BASE} hidden lg:table-cell`,
      tdClassName: `${TD_BASE} text-gray-600 dark:text-gray-300 hidden lg:table-cell`,
      render: (p) => p.lote || "—",
    },
    numero_nota: {
      key: "numero_nota",
      header: "Nota",
      thClassName: `text-left ${TH_BASE} hidden xl:table-cell`,
      tdClassName: `${TD_BASE} text-gray-600 dark:text-gray-300 hidden xl:table-cell`,
      render: (p) => p.numero_nota || "—",
    },
    validade: {
      key: "validade",
      header: "Validade",
      thClassName: `text-left ${TH_BASE} hidden lg:table-cell`,
      tdClassName: `${TD_BASE} text-gray-600 dark:text-gray-300 hidden lg:table-cell`,
      render: (p) =>
        p.validade ? formatClinicaDataCurta(new Date(p.validade + "T00:00:00")) : "—",
    },
    status: {
      key: "status",
      header: "Status",
      thClassName: `text-left ${TH_BASE}`,
      tdClassName: TD_BASE,
      render: (p) => <StatusBadge produto={p} />,
    },
  };
}

export function EstoqueProdutosTable({
  produtos,
  resumo,
  onHistorico,
  onEditar,
  onEntrada,
  onSaida,
  onExcluir,
  colunasVisiveis,
}: Props) {
  const columns = useMemo(() => {
    const registry = buildColumnRegistry();
    const keys =
      colunasVisiveis && colunasVisiveis.length > 0
        ? colunasVisiveis
        : DEFAULT_COLUNAS_ESTOQUE;
    return keys.map((key) => registry[key]).filter(Boolean);
  }, [colunasVisiveis]);

  const colSpan = columns.length + 1;

  return (
    <section className="bg-white dark:bg-neutral-800 rounded-xl shadow-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-neutral-700 border-b border-gray-200 dark:border-neutral-600">
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={col.thClassName}>
                  {col.header}
                </th>
              ))}
              <th className={`text-right ${TH_BASE}`}>Ações</th>
            </tr>
          </thead>
          <tbody>
            {produtos.length === 0 ? (
              <tr>
                <td colSpan={colSpan} className="py-8 text-center text-gray-500 dark:text-gray-400">
                  Nenhum produto encontrado
                </td>
              </tr>
            ) : (
              produtos.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-gray-100 dark:border-neutral-700 hover:bg-gray-50/50 dark:hover:bg-neutral-700/50"
                >
                  {columns.map((col) => (
                    <td key={col.key} className={col.tdClassName}>
                      {col.render(p)}
                    </td>
                  ))}
                  <td className={`${TD_BASE} text-right`}>
                    <div className="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => onHistorico(p)}
                        className="px-2 py-1 text-xs font-medium text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
                        title="Ver histórico de movimentações"
                      >
                        Histórico
                      </button>
                      <button
                        type="button"
                        onClick={() => onEditar(p)}
                        className="px-2 py-1 text-xs font-medium text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded"
                        title="Editar produto"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => onEntrada(p)}
                        className="p-1 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                        title="Entrada de estoque"
                      >
                        <ArrowDown size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => onSaida(p)}
                        className="p-1 text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                        title="Saída de estoque"
                      >
                        <ArrowUp size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => onExcluir(p.id, p.nome)}
                        className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                        title="Excluir produto"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {produtos.length > 0 && (
        <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-neutral-700">
          {produtos.length} produto{produtos.length !== 1 ? "s" : ""} exibido
          {produtos.length !== 1 ? "s" : ""}
          {resumo?.total_produtos != null && resumo.total_produtos !== produtos.length
            ? ` de ${resumo.total_produtos}`
            : ""}
        </div>
      )}
    </section>
  );
}
