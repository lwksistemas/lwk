import { AlertTriangle, Package } from "lucide-react";
import type { EstoqueResumo } from "@/components/clinica-beleza/estoque/estoque-types";
import { formatCurrency } from "@/lib/financeiro-helpers";

export function EstoqueResumoCards({ resumo }: { resumo: EstoqueResumo | null }) {
  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-purple-100 dark:border-purple-900/50">
        <div className="flex items-center gap-2 text-purple-700 dark:text-purple-400 mb-1">
          <Package size={20} />
          <span className="text-sm font-medium">Total Produtos</span>
        </div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{resumo?.total_produtos ?? 0}</p>
      </div>
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-red-100 dark:border-red-900/50">
        <div className="flex items-center gap-2 text-red-700 dark:text-red-400 mb-1">
          <AlertTriangle size={20} />
          <span className="text-sm font-medium">Estoque Baixo</span>
        </div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{resumo?.estoque_baixo ?? 0}</p>
      </div>
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-amber-100 dark:border-amber-900/50">
        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 mb-1">
          <AlertTriangle size={20} />
          <span className="text-sm font-medium">Validade Próxima</span>
        </div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{resumo?.validade_proxima ?? 0}</p>
      </div>
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-green-100 dark:border-green-900/50">
        <div className="flex items-center gap-2 text-green-700 dark:text-green-400 mb-1">
          <Package size={20} />
          <span className="text-sm font-medium">Valor Total Estoque</span>
        </div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {formatCurrency(resumo?.valor_total_estoque ?? 0)}
        </p>
      </div>
    </section>
  );
}
