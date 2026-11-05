"use client";

import { Plus } from "lucide-react";
import type { PeriodoFinanceiro } from "../periodo";
import type { FinanceiroTab } from "../types";

interface FinanceiroTabBarProps {
  tab: FinanceiroTab;
  onTabChange: (tab: FinanceiroTab) => void;
  onNovaDespesa: () => void;
  periodo: PeriodoFinanceiro;
  inicio: string;
  fim: string;
  onPeriodoChange: (periodo: PeriodoFinanceiro) => void;
  onInicioChange: (valor: string) => void;
  onFimChange: (valor: string) => void;
}

export function FinanceiroTabBar({
  tab,
  onTabChange,
  onNovaDespesa,
  periodo,
  inicio,
  fim,
  onPeriodoChange,
  onInicioChange,
  onFimChange,
}: FinanceiroTabBarProps) {
  const escolher = (proximo: PeriodoFinanceiro) => {
    onPeriodoChange(periodo === proximo ? "" : proximo);
  };
  const chip = (ativo: boolean) =>
    `px-3 py-2 rounded-lg text-sm font-medium border ${
      ativo
        ? "text-white border-transparent"
        : "bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-neutral-700"
    }`;

  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      <button
        type="button"
        onClick={() => onTabChange("receitas")}
        className={`px-4 py-2 rounded-lg text-sm font-medium ${
          tab === "receitas"
            ? "text-white"
            : "bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-neutral-700"
        }`}
        style={tab === "receitas" ? { backgroundColor: 'var(--cb-primary, #8B3D52)' } : undefined}
      >
        Receitas (atendimentos)
      </button>
      <button
        type="button"
        onClick={() => onTabChange("despesas")}
        className={`px-4 py-2 rounded-lg text-sm font-medium ${
          tab === "despesas"
            ? "text-white"
            : "bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-neutral-700"
        }`}
        style={tab === "despesas" ? { backgroundColor: 'var(--cb-primary, #8B3D52)' } : undefined}
      >
        Despesas
      </button>
      <button type="button" onClick={() => escolher("atual")} className={chip(periodo === "atual")} style={periodo === "atual" ? { backgroundColor: "var(--cb-primary, #8B3D52)" } : undefined}>
        Mês atual
      </button>
      <button type="button" onClick={() => escolher("passado")} className={chip(periodo === "passado")} style={periodo === "passado" ? { backgroundColor: "var(--cb-primary, #8B3D52)" } : undefined}>
        Mês passado
      </button>
      <button type="button" onClick={() => escolher("personalizado")} className={chip(periodo === "personalizado")} style={periodo === "personalizado" ? { backgroundColor: "var(--cb-primary, #8B3D52)" } : undefined}>
        Personalizado
      </button>
      {periodo === "personalizado" && (
        <>
          <input type="date" value={inicio} onChange={(e) => onInicioChange(e.target.value)} aria-label="De" className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-sm" />
          <input type="date" value={fim} onChange={(e) => onFimChange(e.target.value)} aria-label="Até" className="px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-sm" />
        </>
      )}
      {tab === "despesas" && (
        <button
          type="button"
          onClick={onNovaDespesa}
          className="ml-auto inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-white text-sm font-medium"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
        >
          <Plus size={16} />
          Nova despesa
        </button>
      )}
    </div>
  );
}
