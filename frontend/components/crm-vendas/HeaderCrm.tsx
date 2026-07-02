'use client';

import React, { useEffect } from 'react';
import { Grid, Menu, Search } from 'lucide-react';
import { useCRMUIStore } from '@/store/crm-ui';
import { useCrmHeaderSearch } from '@/hooks/crm-vendas/useCrmHeaderSearch';
import { useCrmHeaderNotifications } from '@/hooks/crm-vendas/useCrmHeaderNotifications';
import { useCrmHeaderMenus } from '@/hooks/crm-vendas/useCrmHeaderMenus';
import { CRM_HEADER_SEARCH_MIN_LEN } from '@/lib/crm-header';
import { HeaderCrmSearchDropdown } from '@/components/crm-vendas/header/HeaderCrmSearchDropdown';
import { HeaderCrmRightSection } from '@/components/crm-vendas/header/HeaderCrmRightSection';

interface HeaderCrmProps {
  title?: string;
  userName?: string;
  userRole?: 'vendedor' | 'administrador';
  slug?: string;
}

function HeaderCrm({
  title = 'Sales Cloud',
  userName = 'Admin',
  userRole = 'administrador',
  slug = '',
}: HeaderCrmProps) {
  const { toggle } = useCRMUIStore();
  const search = useCrmHeaderSearch();
  const notifications = useCrmHeaderNotifications();
  const menus = useCrmHeaderMenus(slug);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menus.searchRef.current && !menus.searchRef.current.contains(e.target as Node)) {
        search.setShowSearchDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menus.searchRef, search]);

  return (
    <header className="h-14 bg-white dark:bg-[#16325c] border-b border-gray-200 dark:border-[#0d1f3c] flex items-center px-3 sm:px-4 justify-between gap-2 sm:gap-4 shrink-0 shadow-sm">
      <div className="flex items-center gap-2 sm:gap-3">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            toggle();
          }}
          onTouchStart={(e) => {
            e.stopPropagation();
            toggle();
          }}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] active:bg-gray-200 dark:active:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300 cursor-pointer touch-manipulation select-none"
          aria-label="Mostrar menu lateral"
        >
          <Menu size={20} />
        </button>
        <button
          type="button"
          className="hidden sm:flex p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
          aria-label="App Launcher"
        >
          <Grid size={20} />
        </button>
        <div className="hidden md:flex items-center gap-2">
          <h1 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h1>
        </div>
      </div>

      <div className="flex-1 max-w-2xl hidden sm:block" ref={menus.searchRef}>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="search"
            value={search.searchQuery}
            onChange={(e) => search.setSearchQuery(e.target.value)}
            onFocus={() =>
              search.searchQuery.length >= CRM_HEADER_SEARCH_MIN_LEN && search.setShowSearchDropdown(true)
            }
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                search.setShowSearchDropdown(false);
                (e.target as HTMLInputElement).blur();
              }
            }}
            placeholder="Buscar por nome, CPF, CNPJ, email..."
            className="w-full pl-9 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-[#0d1f3c] text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-[#0176d3] focus:border-transparent text-sm transition-all"
            aria-label="Buscar no CRM"
          />
          <HeaderCrmSearchDropdown
            slug={slug}
            searchQuery={search.searchQuery}
            searchResults={search.searchResults}
            searchLoading={search.searchLoading}
            showSearchDropdown={search.showSearchDropdown}
            onSelect={search.clearSearch}
          />
        </div>
      </div>

      <HeaderCrmRightSection
        slug={slug}
        userName={userName}
        userRole={userRole}
        showUserMenu={menus.showUserMenu}
        setShowUserMenu={menus.setShowUserMenu}
        showNovoMenu={menus.showNovoMenu}
        setShowNovoMenu={menus.setShowNovoMenu}
        showSuporteMenu={menus.showSuporteMenu}
        setShowSuporteMenu={menus.setShowSuporteMenu}
        novoRef={menus.novoRef}
        suporteRef={menus.suporteRef}
        modalSuporteAberto={menus.modalSuporteAberto}
        setModalSuporteAberto={menus.setModalSuporteAberto}
        lojaNome={menus.lojaNome}
        showNotifs={notifications.showNotifs}
        setShowNotifs={notifications.setShowNotifs}
        notifs={notifications.notifs}
        notifsNaoLidas={notifications.notifsNaoLidas}
        toggleNotifs={notifications.toggleNotifs}
        marcarComoLida={notifications.marcarComoLida}
        limparNotifs={notifications.limparNotifs}
      />
    </header>
  );
}

export default React.memo(HeaderCrm);
