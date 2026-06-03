'use client';

import { useEffect, useState } from 'react';
import { useParams, usePathname, useRouter } from 'next/navigation';
import { ChevronDown, LogOut, Menu, Moon, Sun } from 'lucide-react';
import { ClinicaBelezaTopBar } from './ClinicaBelezaTopBar';
import { ClinicaBelezaPageHeaderProvider } from './ClinicaBelezaPageHeaderContext';
import type { LojaInfo } from '@/types/dashboard';
import { useClinicaBelezaDark } from '@/hooks/useClinicaBelezaDark';
import { syncLojaTenantSlug } from '@/lib/auth';
import {
  CLINICA_BELEZA_NAV_ITEMS,
  CLINICA_BELEZA_PRIMARY,
  getClinicaBelezaNavHref,
  isClinicaBelezaNavActive,
  isClinicaBelezaNavGroupActive,
  type ClinicaBelezaNavItem,
} from './clinica-beleza-nav';

interface ClinicaBelezaShellProps {
  loja: LojaInfo;
  onLogout?: () => void;
  children: React.ReactNode;
  mainClassName?: string;
}

function NavItemButton({
  label,
  icon: Icon,
  isActive,
  collapsed,
  hasChildren,
  expanded,
  onClick,
}: {
  label: string;
  icon: React.ElementType;
  isActive: boolean;
  collapsed: boolean;
  hasChildren?: boolean;
  expanded?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={collapsed ? label : undefined}
      className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
        collapsed ? 'justify-center px-2' : ''
      } ${
        isActive
          ? 'text-white shadow-sm'
          : 'text-gray-600 hover:bg-white/80 dark:text-gray-300 dark:hover:bg-gray-700/50'
      }`}
      style={isActive ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
    >
      <Icon className="w-5 h-5 shrink-0" />
      {!collapsed && (
        <>
          <span className="flex-1 text-left">{label}</span>
          {hasChildren && (
            <ChevronDown
              className={`w-4 h-4 shrink-0 transition-transform ${expanded ? 'rotate-180' : ''}`}
            />
          )}
        </>
      )}
    </button>
  );
}

function SidebarNav({
  slug,
  pathname,
  collapsed,
  onNavigate,
}: {
  slug: string;
  pathname: string;
  collapsed: boolean;
  onNavigate: (href: string) => void;
}) {
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const initial: Record<string, boolean> = {};
    CLINICA_BELEZA_NAV_ITEMS.forEach((item) => {
      if (item.children && isClinicaBelezaNavGroupActive(pathname, slug, item)) {
        initial[item.label] = true;
      }
    });
    setOpenGroups((prev) => ({ ...initial, ...prev }));
  }, [pathname, slug]);

  const toggleGroup = (label: string) => {
    setOpenGroups((prev) => ({ ...prev, [label]: !prev[label] }));
  };

  const renderItem = (item: ClinicaBelezaNavItem) => {
    if (item.children && item.children.length > 0) {
      const groupActive = isClinicaBelezaNavGroupActive(pathname, slug, item);
      const expanded = openGroups[item.label] ?? groupActive;

      return (
        <div key={item.label} className="space-y-0.5">
          <NavItemButton
            label={item.label}
            icon={item.icon}
            isActive={groupActive && !expanded}
            collapsed={collapsed}
            hasChildren={!collapsed}
            expanded={expanded}
            onClick={() => {
              if (collapsed && item.children?.[0]) {
                onNavigate(getClinicaBelezaNavHref(slug, item.children[0].path));
              } else {
                toggleGroup(item.label);
              }
            }}
          />
          {!collapsed && expanded && (
            <div className="ml-4 pl-3 border-l border-gray-200 dark:border-gray-600 space-y-0.5">
              {item.children.map((child) => {
                const href = getClinicaBelezaNavHref(slug, child.path);
                const childActive = isClinicaBelezaNavActive(pathname, slug, child.path);
                return (
                  <button
                    key={child.path}
                    type="button"
                    onClick={() => onNavigate(href)}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      childActive
                        ? 'font-medium text-white'
                        : 'text-gray-500 hover:text-gray-800 hover:bg-white/60 dark:text-gray-400 dark:hover:bg-gray-700/40'
                    }`}
                    style={childActive ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
                  >
                    {child.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      );
    }

    const path = item.path!;
    const href = getClinicaBelezaNavHref(slug, path);
    const isActive = isClinicaBelezaNavActive(pathname, slug, path);

    return (
      <NavItemButton
        key={path}
        label={item.label}
        icon={item.icon}
        isActive={isActive}
        collapsed={collapsed}
        onClick={() => onNavigate(href)}
      />
    );
  };

  return (
    <nav className={`flex-1 overflow-y-auto space-y-0.5 ${collapsed ? 'p-2' : 'px-3 py-2'}`}>
      {CLINICA_BELEZA_NAV_ITEMS.map(renderItem)}
    </nav>
  );
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
        className={`border-b border-gray-200/80 dark:border-gray-700 ${sidebarCollapsed ? 'p-3 flex justify-center' : 'px-4 py-5'}`}
      >
        <div className={`flex items-center gap-3 ${sidebarCollapsed ? 'justify-center' : ''}`}>
          {loja?.logo ? (
            <img src={loja.logo} alt={loja.nome} className="w-10 h-10 rounded-lg object-cover shrink-0" />
          ) : (
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-lg font-bold shrink-0"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {loja?.nome?.charAt(0) || 'B'}
            </div>
          )}
          {!sidebarCollapsed && (
            <div className="min-w-0">
              <h2 className="text-xs font-bold text-gray-800 dark:text-white uppercase leading-tight tracking-wide truncate">
                {loja?.nome || 'Clínica'}
              </h2>
              <p className="text-[10px] text-gray-500 leading-snug mt-0.5">
                Clínica de Estética Avançada
              </p>
            </div>
          )}
        </div>
      </div>

      <SidebarNav
        slug={slug}
        pathname={pathname}
        collapsed={sidebarCollapsed}
        onNavigate={onNavigate}
      />

      <div
        className={`border-t border-gray-200/80 dark:border-gray-700 space-y-0.5 ${sidebarCollapsed ? 'p-2' : 'px-3 py-2'}`}
      >
        <button
          type="button"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hidden lg:flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-white/80 dark:hover:bg-gray-700/50 transition-colors"
          title={sidebarCollapsed ? 'Expandir menu' : 'Recolher menu'}
        >
          <Menu className="w-5 h-5 shrink-0" />
          {!sidebarCollapsed && 'Recolher menu'}
        </button>
        <button
          type="button"
          onClick={() => setDarkMode(!darkMode)}
          className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-white/80 dark:hover:bg-gray-700/50 transition-colors ${sidebarCollapsed ? 'lg:justify-center' : ''}`}
          title={darkMode ? 'Modo claro' : 'Modo escuro'}
        >
          {darkMode ? <Sun className="w-5 h-5 shrink-0" /> : <Moon className="w-5 h-5 shrink-0" />}
          {!sidebarCollapsed && <span>{darkMode ? 'Modo claro' : 'Modo escuro'}</span>}
        </button>
        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors ${sidebarCollapsed ? 'lg:justify-center' : ''}`}
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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window === 'undefined') return true;
    const stored = sessionStorage.getItem('sidebar-collapsed');
    return stored !== null ? stored === 'true' : true; // default: collapsed
  });
  const [darkMode, setDarkMode] = useClinicaBelezaDark();

  useEffect(() => {
    sessionStorage.setItem('sidebar-collapsed', String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  useEffect(() => {
    if (slug) syncLojaTenantSlug(slug);
  }, [slug]);

  const handleNavigate = (href: string) => {
    setSidebarOpen(false);
    const normalizedPath = pathname.replace(/\/$/, '').split('?')[0];
    const normalizedHref = href.replace(/\/$/, '').split('?')[0];
    if (normalizedPath === normalizedHref && !href.includes('?')) return;
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

  const sidebarClass = `flex flex-col shrink-0 sticky top-0 h-screen z-20 bg-[#f3f4f6] dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 ${
    sidebarCollapsed ? 'w-16' : 'w-64'
  }`;

  const isDashboard =
    pathname === `/loja/${slug}/dashboard` || pathname === `/loja/${slug}/dashboard/`;

  return (
    <div className="flex min-h-screen bg-[#f8f9fa] dark:bg-gray-950">
      <aside className={`hidden lg:flex ${sidebarClass}`}>
        <SidebarContent {...sidebarProps} />
      </aside>

      <aside
        className={`lg:hidden fixed inset-y-0 left-0 z-[100] w-64 flex flex-col bg-[#f3f4f6] dark:bg-gray-900 border-r border-gray-200 shadow-xl transform transition-transform duration-200 ${
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
        <ClinicaBelezaPageHeaderProvider>
          <ClinicaBelezaTopBar
            loja={loja}
            isDashboard={isDashboard}
            onOpenMobileMenu={() => setSidebarOpen(true)}
          />
          <main className={`relative flex-1 min-h-0 min-w-0 overflow-y-auto ${mainClassName}`}>{children}</main>
        </ClinicaBelezaPageHeaderProvider>
      </div>
    </div>
  );
}
