'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { LogOut, Menu, Moon, Sun } from 'lucide-react';
import type { LojaInfo } from '@/types/dashboard';
import { useClinicaBelezaDark } from '@/hooks/useClinicaBelezaDark';
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

export function ClinicaBelezaShell({
  loja,
  onLogout,
  children,
  mainClassName = '',
}: ClinicaBelezaShellProps) {
  const params = useParams();
  const pathname = usePathname() ?? '';
  const slug = (params?.slug as string) || loja?.slug || '';
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useClinicaBelezaDark();

  return (
    <div className="flex h-screen min-h-0 bg-gradient-to-br from-pink-50 via-purple-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-gray-950 isolate">
      <aside
        className={`fixed inset-y-0 left-0 z-50 shrink-0 bg-white dark:bg-gray-800 border-r border-gray-100 dark:border-gray-700 transform transition-all duration-200 pointer-events-auto lg:translate-x-0 lg:static lg:inset-auto ${sidebarCollapsed ? 'lg:w-16' : 'lg:w-64'} ${sidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full'}`}
      >
        <div className="flex flex-col h-full">
          <div className={`p-5 border-b border-gray-100 dark:border-gray-700 ${sidebarCollapsed ? 'lg:p-3 lg:flex lg:justify-center' : ''}`}>
            <div className={`flex items-center gap-3 ${sidebarCollapsed ? 'lg:justify-center' : ''}`}>
              {loja?.logo && (
                <img src={loja.logo} alt={loja.nome} className="w-9 h-9 rounded-lg object-cover shrink-0" />
              )}
              {!sidebarCollapsed && (
                <div className="min-w-0 lg:block">
                  <h2 className="text-sm font-bold text-gray-800 dark:text-white truncate">{loja?.nome}</h2>
                  <p className="text-xs text-gray-400">Clínica de Beleza</p>
                </div>
              )}
            </div>
          </div>

          <nav className={`flex-1 p-3 space-y-1 overflow-y-auto ${sidebarCollapsed ? 'lg:p-2' : ''}`}>
            {CLINICA_BELEZA_NAV_ITEMS.map((item) => {
              const href = getClinicaBelezaNavHref(slug, item.path);
              const isActive = isClinicaBelezaNavActive(pathname, slug, item.path);
              return (
                <Link
                  key={item.path}
                  href={href}
                  prefetch
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''} ${
                    isActive
                      ? 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                      : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700/50'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <item.icon className="w-5 h-5 shrink-0" />
                  {!sidebarCollapsed && <span className="lg:inline">{item.label}</span>}
                  {sidebarCollapsed && <span className="lg:hidden">{item.label}</span>}
                </Link>
              );
            })}
          </nav>

          <div className={`p-3 border-t border-gray-100 dark:border-gray-700 space-y-1 ${sidebarCollapsed ? 'lg:p-2' : ''}`}>
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
              {!sidebarCollapsed && <span className="lg:inline">{darkMode ? 'Modo claro' : 'Modo escuro'}</span>}
              {sidebarCollapsed && <span className="lg:hidden">{darkMode ? 'Modo claro' : 'Modo escuro'}</span>}
            </button>
            {onLogout && (
              <button
                type="button"
                onClick={onLogout}
                className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''}`}
                title="Sair"
              >
                <LogOut className="w-5 h-5 shrink-0" />
                {!sidebarCollapsed && <span className="lg:inline">Sair</span>}
                {sidebarCollapsed && <span className="lg:hidden">Sair</span>}
              </button>
            )}
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          type="button"
          aria-label="Fechar menu"
          className="fixed inset-0 bg-black/30 z-40 lg:hidden cursor-default"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex flex-1 flex-col min-w-0 min-h-0 relative z-0">
        <div className="lg:hidden sticky top-0 z-30 flex items-center gap-2 px-4 py-3 bg-white/90 dark:bg-gray-800/90 backdrop-blur border-b border-gray-100 dark:border-gray-700">
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
        <main className={`flex-1 min-h-0 overflow-y-auto ${mainClassName}`}>{children}</main>
      </div>
    </div>
  );
}
