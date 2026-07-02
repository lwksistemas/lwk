'use client';

import Link from 'next/link';
import { Bell, HelpCircle, LogOut, Settings } from 'lucide-react';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import {
  buildCrmSidebarNavItems,
  filterCrmSidebarNavItems,
  isCrmSidebarNavActive,
} from '@/lib/crm-sidebar-nav';
import { hasCrmAcessoTotal, temPermissaoCrm } from '@/lib/crm-permissoes';
import { SidebarCrmNavLink } from '@/components/crm-vendas/sidebar/SidebarCrmNavLink';

interface Props {
  base: string;
  currentPath: string;
  collapsed: boolean;
  onNotifications: () => void;
  onHelp: () => void;
  onLogout?: () => void;
}

export function SidebarCrmNav({
  base,
  currentPath,
  collapsed,
  onNotifications,
  onHelp,
  onLogout,
}: Props) {
  const { moduloAtivo } = useCRMConfig();
  const items = filterCrmSidebarNavItems(buildCrmSidebarNavItems(base), {
    moduloAtivo,
    hasAcessoTotal: hasCrmAcessoTotal,
    temPermissao: temPermissaoCrm,
  });

  return (
    <>
      <nav className="space-y-1 p-2 flex-1 overflow-y-auto">
        {items.map((item) => (
          <SidebarCrmNavLink key={item.href} item={item} currentPath={currentPath} collapsed={collapsed} />
        ))}

        {!collapsed && <div className="my-2 border-t border-gray-200 dark:border-[#0d1f3c]" />}

        <button
          type="button"
          onClick={onNotifications}
          className="flex items-center gap-3 px-3 py-2 rounded text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] w-full text-left transition-all"
          title={collapsed ? 'Notificações' : undefined}
        >
          <Bell size={18} className="shrink-0" />
          {!collapsed && <span>Notificações</span>}
        </button>

        <button
          type="button"
          onClick={onHelp}
          className="flex items-center gap-3 px-3 py-2 rounded text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] w-full text-left transition-all"
          title={collapsed ? 'Ajuda' : undefined}
        >
          <HelpCircle size={18} className="shrink-0" />
          {!collapsed && <span>Ajuda</span>}
        </button>
      </nav>

      <div className="p-2 border-t border-gray-200 dark:border-[#0d1f3c] space-y-1">
        <Link
          href={`${base}/configuracoes`}
          className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-all ${
            isCrmSidebarNavActive(currentPath, {
              href: `${base}/configuracoes`,
              label: 'Configurações',
              icon: Settings,
            })
              ? 'bg-[#0176d3] text-white shadow-sm'
              : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c]'
          } ${!hasCrmAcessoTotal() ? 'pointer-events-none opacity-40' : ''}`}
          title={collapsed ? 'Configurações' : undefined}
          aria-disabled={!hasCrmAcessoTotal()}
          onClick={(e) => {
            if (!hasCrmAcessoTotal()) e.preventDefault();
          }}
        >
          <Settings size={18} className="shrink-0" />
          {!collapsed && <span>Configurações</span>}
        </Link>

        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className="flex items-center gap-3 px-3 py-2 rounded text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 w-full text-left transition-all"
            title={collapsed ? 'Sair' : undefined}
          >
            <LogOut size={18} className="shrink-0" />
            {!collapsed && <span>Sair</span>}
          </button>
        )}
      </div>
    </>
  );
}
