'use client';

import { useEffect, useState } from 'react';
import { useParams, usePathname, useRouter } from 'next/navigation';
import { LogOut, Menu, Moon, Sun } from 'lucide-react';
import type { LojaInfo } from '@/types/dashboard';
import { useClinicaBelezaDark } from '@/hooks/useClinicaBelezaDark';
import { syncLojaTenantSlug } from '@/lib/auth';
import {
  CLINICA_BELEZA_NAV_ITEMS,
  getClinicaBelezaNavHref,
  isClinicaBelezaNavActive,
} from './clinica-beleza-nav';

interface ClinicaBelezaShellProps {
  loja: LojaInfo;
  onLogout?: () => void;
  children: React.ReactNode;
  /** Classes extras no `<main>` (ex.: agenda fullscreen) */
  mainClassName?: string;
}

function SidebarContent({
  loja,
  slug,
  pathname,
  sidebarCollapsed,
  darkMode,
  setDarkMode,
  setSidebarCollapsed,
  onLogout,
  onNavigate,
}: {
  loja: LojaInfo;
  slug: string;
  pathname: string;
  sidebarCollapsed: boolean;
  darkMode: boolean;
  setDarkMode: (v: boolean) => void;
  setSidebarCollapsed: (v: boolean) => void;
  onLogout?: () => void;
  onNavigate: (href: string) => void;
}) {
  return (
    <>
      <div
        className={`border-b border-gray-100 dark:border-gray-700 ${sidebarCollapsed ? 'p-3 flex justify-center' : 'p-5'}`}
      >
        <div className={`flex items-center gap-3 ${sidebarCollapsed ? 'justify-center' : ''}`}>
          {loja?.logo && (
            <img src={loja.logo} alt={loja.nome} className="w-9 h-9 rounded-lg object-cover shrink-0" />
          )}
          {!sidebarCollapsed && (
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-gray-800 dark:text-white truncate">{loja?.nome}</h2>
              <p className="text-xs text-gray-400">Clínica de Beleza</p>
            </div>
          )}
        </div>
      </div>

      <nav className={`flex-1 p-3 space-y-1 overflow-y-auto ${sidebarCollapsed ? 'p-2' : ''}`}>
        {CLINICA_BELEZA_NAV_ITEMS.map((item) => {
          const href = getClinicaBelezaNavHref(slug, item.path);
          const isActive = isClinicaBelezaNavActive(pathname, slug, item.path);
          return (
            <button
              key={item.path}
              type="button"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors w-full text-left cursor-pointer ${sidebarCollapsed ? 'justify-center px-2' : ''} ${
                isActive
                  ? 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                  : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700/50'
              }`}
              onClick={() => onNavigate(href)}
              title={sidebarCollapsed ? item.label : undefined}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {!sidebarCollapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      <div className={`p-3 border-t border-gray-100 dark:border-gray-700 space-y-1 ${sidebarCollapsed ? 'p-2' : ''}`}>
        <button
          type="button"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hidden lg:flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
          title={sidebarCollapsed ? 'Expandir menu' : 'Recolher menu'}
        >
          <Menu className="w-5 h-5 shrink-0" />
          {!sidebarCollapsed && 'Recolher menu'}
        </button>
        <button
          type="button"
          onClick={() => setDarkMode(!darkMode)}
          className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''}`}
          title={darkMode ? 'Modo claro' : 'Modo escuro'}
        >
          {darkMode ? <Sun className="w-5 h-5 shrink-0" /> : <Moon className="w-5 h-5 shrink-0" />}
          {!sidebarCollapsed && <span>{darkMode ? 'Modo claro' : 'Modo escuro'}</span>}
        </button>
        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''}`}
            title="Sair"
          >
            <LogOut className="w-5 h-5 shrink-0" />
            {!sidebarCollapsed && <span>Sair</span>}
          </button>
        )}
      </div>
    </>
  );
}

export function ClinicaBelezaShell({
  loja,
  onLogout,
  children,
  mainClassName = '',
}: ClinicaBelezaShellProps) {
  const params = useParams();
  const pathname = usePathname() ?? '';
  const router = useRouter();
  const slug = (params?.slug as string) || loja?.slug || '';
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useClinicaBelezaDark();

  useEffect(() => {
    if (slug) syncLojaTenantSlug(slug);
  }, [slug]);

  const handleNavigate = (href: string) => {
    setSidebarOpen(false);
    const normalizedPath = pathname.replace(/\/$/, '');
    const normalizedHref = href.replace(/\/$/, '');
    if (normalizedPath === normalizedHref) return;
    syncLojaTenantSlug(slug);
    router.push(href);
  };

  const sidebarProps = {
    loja,
    slug,
    pathname,
    sidebarCollapsed,
    darkMode,
    setDarkMode,
    setSidebarCollapsed,
    onLogout,
    onNavigate: handleNavigate,
  };

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-gray-950">
      {/* Sidebar desktop — coluna fixa no fluxo (sem position:fixed) */}
      <aside
        className={`hidden lg:flex lg:flex-col lg:shrink-0 lg:sticky lg:top-0 lg:h-screen lg:z-20 bg-white dark:bg-gray-800 border-r border-gray-100 dark:border-gray-700 ${
          sidebarCollapsed ? 'lg:w-16' : 'lg:w-64'
        }`}
      >
        <SidebarContent {...sidebarProps} />
      </aside>

      {/* Sidebar mobile — drawer */}
      <aside
        className={`lg:hidden fixed inset-y-0 left-0 z-[100] w-64 flex flex-col bg-white dark:bg-gray-800 border-r border-gray-100 dark:border-gray-700 shadow-xl transform transition-transform duration-200 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full pointer-events-none'
        }`}
        aria-hidden={!sidebarOpen}
      >
        <SidebarContent {...sidebarProps} />
      </aside>

      {sidebarOpen && (
        <button
          type="button"
          aria-label="Fechar menu"
          className="lg:hidden fixed inset-0 z-[90] bg-black/30"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <div className="lg:hidden sticky top-0 z-50 flex items-center gap-2 px-4 py-3 bg-white/95 dark:bg-gray-800/95 backdrop-blur border-b border-gray-100 dark:border-gray-700">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Abrir menu"
          >
            <Menu className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-100 truncate">{loja?.nome}</span>
        </div>
        <main className={`relative flex-1 min-h-0 min-w-0 overflow-y-auto ${mainClassName}`}>{children}</main>
      </div>
    </div>
  );
}
