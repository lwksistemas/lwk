"use client";

import { CalendarClock, ClipboardList, Printer } from "lucide-react";
import { isProntuarioLocalTab } from "./prontuario-utils";
import { PRONTUARIO_TABS, type ProntuarioTabId } from "./prontuario-types";

interface ProntuarioTabBarProps {
  activeTab: ProntuarioTabId;
  onTabChange: (tabId: ProntuarioTabId) => void;
  onPrintSecao: () => void;
  onPrintCompleto: () => void;
  printando?: "secao" | "completo" | null;
  finalizadasCount?: number;
  onAbrirProtocolo: () => void;
  showPrazoButton?: boolean;
  prazoAberto?: boolean;
  onTogglePrazo?: () => void;
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
  finalizadasCount = 0,
  onAbrirProtocolo,
  showPrazoButton = false,
  prazoAberto = false,
  onTogglePrazo,
}: ProntuarioTabBarProps) {
  return (
    <div className="flex flex-nowrap items-center gap-2 overflow-x-auto">
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
        title="Baixa o PDF desta seção com o nome da cliente"
      >
        <Printer size={16} />
        <span className="hidden md:inline">{printando === "secao" ? "Gerando…" : "Baixar seção"}</span>
      </button>
      )}

      <div className="flex items-center gap-2 shrink-0 sm:ml-auto">
        {showPrazoButton && (
          <button
            type="button"
            onClick={onTogglePrazo}
            aria-pressed={prazoAberto}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              prazoAberto
                ? "text-white"
                : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700"
            }`}
            style={prazoAberto ? { backgroundColor: "var(--cb-primary, #8B3D52)" } : undefined}
            title="Configurar prazo de pagamento do paciente"
          >
            <CalendarClock size={16} />
            <span className="hidden md:inline">Prazo de pagamento</span>
          </button>
        )}
        <button
          type="button"
          onClick={onPrintCompleto}
          disabled={!!printando}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
          title="Baixa o prontuário completo com o nome da cliente"
        >
          <Printer size={16} />
          <span className="hidden md:inline">{printando === "completo" ? "Gerando…" : "Baixar completo"}</span>
        </button>
        <button
          type="button"
          onClick={onAbrirProtocolo}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white shrink-0"
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          <ClipboardList size={16} />
          <span className="whitespace-nowrap">Protocolo personalizado</span>
        </button>
        <ContagemConsulta label="Finalizadas" value={finalizadasCount} />
      </div>
    </div>
  );
}
