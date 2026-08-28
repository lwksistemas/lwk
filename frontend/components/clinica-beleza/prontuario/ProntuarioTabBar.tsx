"use client";

import { Printer } from "lucide-react";
import { isProntuarioLocalTab } from "./prontuario-utils";
import { PRONTUARIO_TABS, type ProntuarioTabId } from "./prontuario-types";

interface ProntuarioTabBarProps {
  activeTab: ProntuarioTabId;
  onTabChange: (tabId: ProntuarioTabId) => void;
  onPrintSecao: () => void;
  onPrintCompleto: () => void;
  printando?: "secao" | "completo" | null;
  consultaAtualCount?: number;
  finalizadasCount?: number;
}

function ContagemConsulta({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 py-1.5 min-w-[5.25rem]">
      <p className="text-[10px] leading-tight text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-base font-semibold leading-tight text-gray-900 dark:text-gray-100">{value}</p>
    </div>
  );
}

export function ProntuarioTabBar({
  activeTab,
  onTabChange,
  onPrintSecao,
  onPrintCompleto,
  printando = null,
  consultaAtualCount = 0,
  finalizadasCount = 0,
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

      {!isProntuarioLocalTab(activeTab) && (
      <div className="hidden sm:block w-px h-6 bg-gray-300 dark:bg-neutral-600 mx-1" />
      )}

      {!isProntuarioLocalTab(activeTab) && (
      <button
        type="button"
        onClick={onPrintSecao}
        disabled={!!printando}
        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
        title="Imprimir todos os documentos desta seção"
      >
        <Printer size={16} />
        <span className="hidden md:inline">{printando === "secao" ? "Gerando…" : "Imprimir Seção"}</span>
      </button>
      )}

      <div className="flex items-center gap-2 shrink-0">
        <button
          type="button"
          onClick={onPrintCompleto}
          disabled={!!printando}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
          title="Imprimir prontuário completo do paciente"
        >
          <Printer size={16} />
          <span className="hidden md:inline">{printando === "completo" ? "Gerando…" : "Imprimir Completo"}</span>
        </button>
        <ContagemConsulta label="Consulta atual" value={consultaAtualCount} />
        <ContagemConsulta label="Finalizadas" value={finalizadasCount} />
      </div>
    </div>
  );
}
