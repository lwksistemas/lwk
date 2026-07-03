"use client";

import { ClinicaBelezaTopBar } from "../ClinicaBelezaTopBar";
import { ClinicaBelezaPageHeaderProvider } from "../ClinicaBelezaPageHeaderContext";
import { ClinicaBelezaSidebarContent } from "./ClinicaBelezaSidebarContent";
import {
  getDesktopSidebarClassName,
  getMobileDrawerClassName,
} from "./clinica-beleza-shell-utils";
import type { ClinicaBelezaShellProps } from "./clinica-beleza-shell-types";
import { useClinicaBelezaShell } from "./useClinicaBelezaShell";

export function ClinicaBelezaShell({
  loja,
  onLogout,
  children,
  mainClassName = "",
}: ClinicaBelezaShellProps) {
  const {
    slug,
    pathname,
    sidebarOpen,
    setSidebarOpen,
    sidebarCollapsed,
    setSidebarCollapsed,
    darkMode,
    setDarkMode,
    handleNavigate,
  } = useClinicaBelezaShell(loja);

  const sidebarProps = {
    loja,
    slug,
    pathname,
    sidebarCollapsed,
    setSidebarCollapsed,
    onNavigate: handleNavigate,
  };

  return (
    <div className="flex min-h-screen bg-[#f7f2f4] dark:bg-gray-950">
      <aside className={`hidden lg:flex ${getDesktopSidebarClassName(sidebarCollapsed)}`}>
        <ClinicaBelezaSidebarContent {...sidebarProps} />
      </aside>

      <aside
        className={getMobileDrawerClassName(sidebarOpen)}
        aria-hidden={!sidebarOpen}
        role="dialog"
        aria-modal={sidebarOpen}
        aria-label="Menu de navegação"
      >
        <ClinicaBelezaSidebarContent
          {...sidebarProps}
          isMobileDrawer
          onCloseMobile={() => setSidebarOpen(false)}
        />
      </aside>

      {sidebarOpen && (
        <button
          type="button"
          aria-label="Fechar menu"
          className="lg:hidden fixed inset-0 z-[90] bg-black/40 touch-manipulation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <ClinicaBelezaPageHeaderProvider
          shellActions={{ loja, darkMode, setDarkMode, onLogout }}
        >
          <ClinicaBelezaTopBar loja={loja} onOpenMobileMenu={() => setSidebarOpen(true)} />
          <main
            className={`relative flex flex-col flex-1 min-h-0 min-w-0 overflow-y-auto ${mainClassName}`}
          >
            {children}
          </main>
        </ClinicaBelezaPageHeaderProvider>
      </div>
    </div>
  );
}
