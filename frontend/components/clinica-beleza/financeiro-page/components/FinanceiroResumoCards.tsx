"use client";

import { Calendar, DollarSign, TrendingUp, Wallet } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { FinanceiroResumo } from "../types";

interface FinanceiroResumoCardsProps {
  resumo: FinanceiroResumo | null;
}

export function FinanceiroResumoCards({ resumo }: FinanceiroResumoCardsProps) {
  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-green-100 dark:border-green-900/50">
        <div className="flex items-center gap-2 text-green-700 dark:text-green-400 mb-1">
          <Wallet size={20} />
          <span className="text-sm font-medium">Caixa hoje</span>
        </div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {formatCurrency(resumo?.caixa_diario ?? 0)}
        </p>
      </div>
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-purple-100 dark:border-purple-900/50">
        <div className="flex items-center gap-2 text-purple-700 dark:text-purple-400 mb-1">
          <DollarSign size={20} />
          <span className="text-sm font-medium">Receita mês</span>
        </div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {formatCurrency(resumo?.total_mes ?? 0)}
        </p>
      </div>
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-amber-100 dark:border-amber-900/50">
        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 mb-1">
          <Calendar size={20} />
          <span className="text-sm font-medium">A receber</span>
        </div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {formatCurrency(resumo?.contas_a_receber ?? 0)}
        </p>
        {(resumo?.despesas_pendentes ?? 0) > 0 && (
          <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
            A pagar: {formatCurrency(resumo?.despesas_pendentes ?? 0)}
          </p>
        )}
      </div>
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-4 border border-blue-100 dark:border-blue-900/50">
        <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400 mb-1">
          <TrendingUp size={20} />
          <span className="text-sm font-medium">Despesas mês</span>
        </div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {formatCurrency(resumo?.despesas ?? 0)}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Comissões {formatCurrency(resumo?.comissao_mes ?? 0)}
          {(resumo?.despesas_operacionais ?? 0) > 0 && (
            <> · Operacionais {formatCurrency(resumo?.despesas_operacionais ?? 0)}</>
          )}
        </p>
        <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400 mt-1">
          Lucro: {formatCurrency(resumo?.lucro ?? 0)}
        </p>
      </div>
    </section>
  );
}
