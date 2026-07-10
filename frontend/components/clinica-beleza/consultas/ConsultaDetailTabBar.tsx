"use client";

import { Fragment } from "react";
import {
  Activity,
  Camera,
  ClipboardList,
  FileText,
  FolderOpen,
  History,
  Package,
  type LucideIcon,
} from "lucide-react";
import { ConsultaTermoConsentimentoButton } from "./ConsultaTermoConsentimentoButton";
import type { Consulta, TabId } from "./consultas-types";

const ALL_TABS: { id: TabId; label: string; icon: LucideIcon }[] = [
  { id: "atendimento", label: "Atendimento", icon: ClipboardList },
  { id: "produtos", label: "Produtos", icon: Package },
  { id: "documentos", label: "Documentos", icon: FolderOpen },
  { id: "anamnese", label: "Anamnese", icon: FileText },
  { id: "evolucao", label: "Evolução", icon: Activity },
  { id: "fotos", label: "Fotos", icon: Camera },
  { id: "historico", label: "Histórico", icon: History },
];

interface ConsultaDetailTabBarProps {
  tab: TabId;
  selected: Consulta;
  consultaAtiva: boolean;
  consultaFinalizada: boolean;
  temHistoricoAnterior: boolean;
  onTabChange: (tab: TabId) => void;
  onRefreshConsulta: () => void;
}

export function ConsultaDetailTabBar({
  tab,
  selected,
  consultaAtiva,
  consultaFinalizada,
  temHistoricoAnterior,
  onTabChange,
  onRefreshConsulta,
}: ConsultaDetailTabBarProps) {
  const tabsConsultaFinalizada: TabId[] = [
    "atendimento",
    "produtos",
    "documentos",
    "anamnese",
    "evolucao",
    "fotos",
  ];

  const visibleTabs = (consultaFinalizada
    ? ALL_TABS.filter((t) => tabsConsultaFinalizada.includes(t.id))
    : ALL_TABS
  ).filter((t) => t.id !== "historico" || temHistoricoAnterior);

  return (
    <div className={`flex flex-wrap gap-2 ${consultaAtiva ? "mt-0" : "mt-4"}`}>
      {visibleTabs.map(({ id, label, icon: Icon }) => {
        const disabled = !consultaAtiva && !consultaFinalizada && id !== "historico";
        return (
          <Fragment key={id}>
            <button
              type="button"
              onClick={() => {
                if (!disabled) onTabChange(id);
              }}
              disabled={disabled}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
                tab === id
                  ? "text-white"
                  : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300"
              }`}
              style={tab === id ? { backgroundColor: 'var(--cb-primary, #8B3D52)' } : undefined}
            >
              <Icon size={16} />
              {label}
            </button>
            {id === "evolucao" && consultaAtiva && selected.exige_termo_consentimento && (
              <ConsultaTermoConsentimentoButton
                consultaId={selected.id}
                exigeTermo={selected.exige_termo_consentimento}
                onUpdated={onRefreshConsulta}
              />
            )}
          </Fragment>
        );
      })}
    </div>
  );
}
