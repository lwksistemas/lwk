'use client';

import React from 'react';
import { X } from 'lucide-react';
import { useCrmSidebar } from '@/hooks/crm-vendas/useCrmSidebar';
import { SidebarCrmNav } from '@/components/crm-vendas/sidebar/SidebarCrmNav';
import { SidebarCrmNotificationsPanel } from '@/components/crm-vendas/sidebar/SidebarCrmNotificationsPanel';
import { SidebarCrmHelpModal } from '@/components/crm-vendas/sidebar/SidebarCrmHelpModal';

interface SidebarCrmProps {
  lojaNome?: string;
  onLogout?: () => void;
}

function SidebarCrm({ lojaNome, onLogout }: SidebarCrmProps) {
  const {
    collapsed,
    toggle,
    base,
    currentPath,
    showNotifications,
    setShowNotifications,
    showHelp,
    setShowHelp,
    notificacoes,
    notificacoesLoading,
    notificacoesErro,
    handleNotifications,
  } = useCrmSidebar();

  return (
    <>
      {!collapsed && (
        <div
          className="fixed inset-0 bg-black/50 z-[60] md:hidden cursor-pointer touch-manipulation"
          onClick={() => toggle()}
          aria-hidden="true"
        />
      )}

      <aside
        className={`
          bg-white dark:bg-[#16325c] transition-all duration-300 h-full flex flex-col shrink-0
          fixed md:relative inset-y-0 left-0 z-[70]
          border-r border-gray-200 dark:border-[#0d1f3c]
          ${collapsed ? '-translate-x-full md:translate-x-0 md:w-16' : 'translate-x-0 w-64'}
        `}
      >
        <div className="p-4 flex items-center justify-between border-b border-gray-200 dark:border-[#0d1f3c] min-h-[4rem]">
          {!collapsed && (
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="w-8 h-8 rounded bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-bold text-sm shrink-0">
                {lojaNome?.charAt(0).toUpperCase() || 'L'}
              </div>
              <div className="flex flex-col flex-1 min-w-0">
                <span className="font-semibold text-sm text-gray-900 dark:text-white truncate" title={lojaNome}>
                  {lojaNome || 'LWK'}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400">Sales Cloud</span>
              </div>
            </div>
          )}

          {!collapsed && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                toggle();
              }}
              className="md:hidden min-h-[44px] min-w-[44px] flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-gray-600 dark:text-gray-300 transition-colors cursor-pointer touch-manipulation -mr-1"
              aria-label="Ocultar menu lateral"
            >
              <X size={20} />
            </button>
          )}
        </div>

        <SidebarCrmNav
          base={base}
          currentPath={currentPath}
          collapsed={collapsed}
          onNotifications={handleNotifications}
          onHelp={() => setShowHelp(true)}
          onLogout={onLogout}
        />
      </aside>

      <SidebarCrmNotificationsPanel
        open={showNotifications}
        onClose={() => setShowNotifications(false)}
        notificacoes={notificacoes}
        loading={notificacoesLoading}
        erro={notificacoesErro}
      />

      <SidebarCrmHelpModal open={showHelp} onClose={() => setShowHelp(false)} />
    </>
  );
}

export default React.memo(SidebarCrm);
