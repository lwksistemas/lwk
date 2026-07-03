import { AlertTriangle, Trash2 } from "lucide-react";
import { formatClinicaDataCurta } from "@/lib/clinica-beleza-datetime";
import { imprimirConsultaPdf, type ConsultaPrintMeta } from "@/lib/consulta-print";
import { ConsultaPrintButton } from "../ConsultaPrintButton";
import type { ConsultaProdutoItem, ProdutoEstoque } from "./produtos-types";

export function ProdutosListaTable({
  itens,
  produtos,
  totaisConsulta,
  somenteLeitura,
  saving,
  printMeta,
  onRemover,
}: {
  itens: ConsultaProdutoItem[];
  produtos: ProdutoEstoque[];
  totaisConsulta: Map<number, number>;
  somenteLeitura: boolean;
  saving: boolean;
  printMeta: ConsultaPrintMeta;
  onRemover: (item: ConsultaProdutoItem) => void;
}) {
  if (!itens.length) {
    return (
      <div className="text-center py-10 text-gray-500 text-sm rounded-xl border border-dashed border-gray-200 dark:border-neutral-700">
        Nenhum produto registrado nesta consulta.
      </div>
    );
  }

  return (
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
          {itens.map((item) => {
            const totalProduto = totaisConsulta.get(item.produto) || Number(item.quantidade);
            const disponivel = Number(
              item.quantidade_disponivel ?? produtos.find((p) => p.id === item.produto)?.quantidade_atual ?? 0,
            );
            const estoqueInsuficiente = !item.estoque_baixado && totalProduto > disponivel;
            return (
              <tr key={item.id} className="border-t border-gray-100 dark:border-neutral-700">
                <td className="p-3 font-medium text-gray-800 dark:text-gray-200">
                  <span className="inline-flex items-center gap-1.5">
                    {item.produto_nome}
                    {estoqueInsuficiente && (
                      <span title="Estoque insuficiente para finalizar">
                        <AlertTriangle size={14} className="text-amber-600 dark:text-amber-400" />
                      </span>
                    )}
                  </span>
                </td>
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
                      onClick={() => onRemover(item)}
                      disabled={saving || item.estoque_baixado}
                      className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-40"
                      title="Remover"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
