"use client";

import { Plus } from "lucide-react";
import type { FinanceiroTab } from "../types";

interface FinanceiroTabBarProps {
  tab: FinanceiroTab;
  onTabChange: (tab: FinanceiroTab) => void;
  onNovaDespesa: () => void;
}

export function FinanceiroTabBar({ tab, onTabChange, onNovaDespesa }: FinanceiroTabBarProps) {
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
