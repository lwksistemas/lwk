'use client';

import React from 'react';
import Link from 'next/link';
import { useCRMUIStore } from '@/store/crm-ui';
import { Menu, Search, Grid, Plus, Bell, HelpCircle, User, Users, DollarSign } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

interface HeaderCrmProps {
  title?: string;
  userName?: string;
  slug?: string;
}

function HeaderCrm({ title = 'Sales Cloud', userName = 'Admin', slug = '' }: HeaderCrmProps) {
  const { toggle } = useCRMUIStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNovoMenu, setShowNovoMenu] = useState(false);
  const novoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (novoRef.current && !novoRef.current.contains(e.target as Node)) {
        setShowNovoMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-14 bg-white dark:bg-[#16325c] border-b border-gray-200 dark:border-[#0d1f3c] flex items-center px-3 sm:px-4 justify-between gap-2 sm:gap-4 shrink-0 shadow-sm">
      {/* Left Section */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Menu Toggle - Mobile friendly */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            toggle();
          }}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] active:bg-gray-200 dark:active:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300 cursor-pointer touch-manipulation select-none"
          aria-label="Mostrar menu lateral"
        >
          <Menu size={20} />
        </button>

        {/* App Launcher - Estilo Salesforce */}
        <button
          type="button"
          className="hidden sm:flex p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
          aria-label="App Launcher"
          title="App Launcher"
        >
          <Grid size={20} />
        </button>

        {/* Title/Breadcrumb */}
        <div className="hidden md:flex items-center gap-2">
          <h1 className="text-sm font-semibold text-gray-900 dark:text-white">
            {title}
          </h1>
        </div>
      </div>

      {/* Center Section - Search */}
      <div className="flex-1 max-w-2xl hidden sm:block">
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="search"
            placeholder="Buscar em Sales Cloud..."
            className="w-full pl-9 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-[#0d1f3c] text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-[#0176d3] focus:border-transparent text-sm transition-all"
          />
        </div>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center gap-1 sm:gap-2">
        {/* New Button - Estilo Salesforce */}
        <div className="relative" ref={novoRef}>
          <button
            type="button"
            onClick={() => setShowNovoMenu((v) => !v)}
            className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors"
            title="Novo"
          >
            <Plus size={16} />
            <span>Novo</span>
          </button>

          {/* Mobile New Button */}
          <button
            type="button"
            onClick={() => setShowNovoMenu((v) => !v)}
            className="lg:hidden p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
            aria-label="Novo"
            title="Novo"
          >
            <Plus size={20} />
          </button>

          {showNovoMenu && slug && (
            <div className="absolute right-0 mt-2 w-52 bg-white dark:bg-[#16325c] rounded-lg shadow-lg border border-gray-200 dark:border-[#0d1f3c] py-1 z-20">
              <Link
                href={`/loja/${slug}/crm-vendas/leads?novo=1`}
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]"
                onClick={() => setShowNovoMenu(false)}
              >
                <Users size={16} />
                Novo Lead
              </Link>
              <Link
                href={`/loja/${slug}/crm-vendas/pipeline?novo=1`}
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]"
                onClick={() => setShowNovoMenu(false)}
              >
                <DollarSign size={16} />
                Nova Oportunidade
              </Link>
            </div>
          )}
        </div>

        {/* Notifications */}
        <button
          type="button"
          className="relative p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
          aria-label="Notificações"
          title="Notificações"
        >
          <Bell size={20} />
          {/* Badge de notificação */}
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* Help */}
        <button
          type="button"
          className="hidden sm:flex p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
          aria-label="Ajuda"
          title="Ajuda"
        >
          <HelpCircle size={20} />
        </button>

        {/* User Menu */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1.5 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors"
            aria-label="Menu do usuário"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-semibold text-sm">
              {userName?.charAt(0).toUpperCase() || 'A'}
            </div>
          </button>

          {/* Dropdown Menu - Estilo Salesforce */}
          {showUserMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowUserMenu(false)}
              />
              <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-[#16325c] rounded-lg shadow-lg border border-gray-200 dark:border-[#0d1f3c] z-20 py-1">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-[#0d1f3c]">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                    {userName}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Administrador
                  </p>
                </div>
                <Link
                  href={slug ? `/loja/${slug}/trocar-senha` : '/loja/trocar-senha'}
                  onClick={() => setShowUserMenu(false)}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] flex items-center gap-2"
                >
                  <User size={16} />
                  Meu Perfil
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    const html = document.documentElement;
                    const isDark = html.classList.contains('dark');
                    if (isDark) {
                      html.classList.remove('dark');
                      localStorage.setItem('theme', 'light');
                    } else {
                      html.classList.add('dark');
                      localStorage.setItem('theme', 'dark');
                    }
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  Alternar Tema
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

// Memoização para evitar re-renders desnecessários
export default React.memo(HeaderCrm);

