import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { ClinicaBelezaSidebarNav } from "./ClinicaBelezaSidebarNav";
import type { ClinicaBelezaSidebarContentProps } from "./clinica-beleza-shell-types";

export function ClinicaBelezaSidebarContent({
  loja,
  slug,
  pathname,
  sidebarCollapsed,
  isMobileDrawer = false,
  onCloseMobile,
  setSidebarCollapsed,
  onNavigate,
}: ClinicaBelezaSidebarContentProps) {
  const collapsed = isMobileDrawer ? false : sidebarCollapsed;

  return (
    <>
      <div
        className={`border-b border-gray-200/80 dark:border-gray-700 shrink-0 ${collapsed ? "p-3" : "px-4 py-4"}`}
      >
        <div className={`flex items-center gap-2 w-full ${collapsed ? "justify-center" : ""}`}>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <h2 className="text-xs font-bold text-gray-800 dark:text-white uppercase leading-tight tracking-wide truncate">
                {loja?.nome || "Clínica"}
              </h2>
              <p className="text-[10px] text-gray-500 leading-snug mt-0.5">
                Clínica de Estética Avançada
              </p>
            </div>
          )}
          {!isMobileDrawer && (
            <button
              type="button"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hidden lg:flex w-8 h-8 rounded-lg items-center justify-center text-white shrink-0 hover:opacity-90 transition-opacity"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
              title={sidebarCollapsed ? "Expandir menu" : "Recolher menu"}
              aria-label={sidebarCollapsed ? "Expandir menu" : "Recolher menu"}
            >
              {sidebarCollapsed ? (
                <ChevronRight className="w-5 h-5" strokeWidth={2.5} />
              ) : (
                <ChevronLeft className="w-5 h-5" strokeWidth={2.5} />
              )}
            </button>
          )}
          {isMobileDrawer && onCloseMobile && (
            <button
              type="button"
              onClick={onCloseMobile}
              className="ml-auto p-2 rounded-lg text-gray-500 hover:bg-white/80 dark:hover:bg-gray-700/50 shrink-0"
              aria-label="Fechar menu"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      <ClinicaBelezaSidebarNav
        slug={slug}
        pathname={pathname}
        collapsed={collapsed}
        onNavigate={onNavigate}
      />
    </>
  );
}
