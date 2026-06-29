import { X } from "lucide-react";
import type { EstoqueMovimentacaoHistorico, EstoqueProduto } from "@/components/clinica-beleza/estoque/estoque-types";

interface Props {
  produto: EstoqueProduto;
  historico: EstoqueMovimentacaoHistorico[];
  onClose: () => void;
}

export function EstoqueHistoricoModal({ produto, historico, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Histórico de Movimentações</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{produto.nome}</p>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800">
            <X size={20} className="text-gray-500" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {historico.length === 0 ? (
            <p className="text-center text-gray-500 py-8 text-sm">Nenhuma movimentação registrada.</p>
          ) : (
            <div className="space-y-2">
              {historico.map((mov, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-lg border text-sm ${
                    mov.tipo === "entrada"
                      ? "border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10"
                      : mov.tipo === "saida"
                        ? "border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-900/10"
                        : "border-gray-200 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-800"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`font-medium ${
                        mov.tipo === "entrada"
                          ? "text-green-700 dark:text-green-300"
                          : mov.tipo === "saida"
                            ? "text-red-700 dark:text-red-300"
                            : "text-gray-700 dark:text-gray-300"
                      }`}
                    >
                      {mov.tipo === "entrada" ? "↓ Entrada" : mov.tipo === "saida" ? "↑ Saída" : "⇄ Ajuste"}{" "}
                      {mov.tipo === "entrada" ? "+" : mov.tipo === "saida" ? "-" : ""}
                      {mov.quantidade}
                    </span>
                    <span className="text-xs text-gray-500">
                      {mov.created_at ? new Date(mov.created_at).toLocaleDateString("pt-BR") : ""}
                    </span>
                  </div>
                  {mov.motivo && <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{mov.motivo}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="px-6 py-3 border-t border-gray-200 dark:border-neutral-700 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="ml-auto block px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 rounded-lg"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
