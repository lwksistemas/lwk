"use client";

import { Printer } from "lucide-react";
import { PRONTUARIO_TABS, type ProntuarioTabId } from "./prontuario-types";

interface ProntuarioTabBarProps {
  activeTab: ProntuarioTabId;
  onTabChange: (tabId: ProntuarioTabId) => void;
  onPrintSecao: () => void;
  onPrintCompleto: () => void;
}

export function ProntuarioTabBar({
  activeTab,
  onTabChange,
  onPrintSecao,
  onPrintCompleto,
}: ProntuarioTabBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {PRONTUARIO_TABS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => onTabChange(id)}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === id
              ? "text-white"
              : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700"
          }`}
          style={activeTab === id ? { backgroundColor: 'var(--cb-primary, #8B3D52)' } : undefined}
        >
          <Icon size={16} />
          {label}
        </button>
      ))}

      <div className="hidden sm:block w-px h-6 bg-gray-300 dark:bg-neutral-600 mx-1" />

      <button
        type="button"
        onClick={onPrintSecao}
        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors"
        title="Imprimir todos os documentos desta seção"
      >
        <Printer size={16} />
        <span className="hidden md:inline">Imprimir Seção</span>
      </button>

      <button
        type="button"
        onClick={onPrintCompleto}
        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white transition-colors"
        style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
        title="Imprimir prontuário completo do paciente"
      >
        <Printer size={16} />
        <span className="hidden md:inline">Imprimir Completo</span>
      </button>
    </div>
  );
}
