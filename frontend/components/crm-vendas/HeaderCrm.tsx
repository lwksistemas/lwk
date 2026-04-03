'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCRMUIStore } from '@/store/crm-ui';
import { Menu, Search, Grid, Plus, Bell, HelpCircle, User, Users, DollarSign, Building2, MessageCircle } from 'lucide-react';
import { useState, useRef, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import ModalChamado from '@/components/suporte/ModalChamado';

interface BuscaResult {
  leads: { id: number; nome: string; empresa: string; status: string }[];
  oportunidades: { id: number; titulo: string; valor: string; etapa: string; lead_nome: string; lead_empresa: string }[];
  contas: { id: number; nome: string; segmento: string }[];
}

interface HeaderCrmProps {
  title?: string;
  userName?: string;
  userRole?: 'vendedor' | 'administrador';
  slug?: string;
}

const DEBOUNCE_MS = 300;
const MIN_QUERY_LEN = 2;

function HeaderCrm({ title = 'Sales Cloud', userName = 'Admin', userRole = 'administrador', slug = '' }: HeaderCrmProps) {
  const router = useRouter();
  const { toggle } = useCRMUIStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNovoMenu, setShowNovoMenu] = useState(false);
  const [showSuporteMenu, setShowSuporteMenu] = useState(false);
  const [modalSuporteAberto, setModalSuporteAberto] = useState(false);
  const [lojaNome, setLojaNome] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<BuscaResult | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const novoRef = useRef<HTMLDivElement>(null);
  const suporteRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchBusca = useCallback(async (q: string) => {
    if (!q || q.length < MIN_QUERY_LEN) {
      setSearchResults(null);
      return;
    }
    setSearchLoading(true);
    try {
      const res = await apiClient.get<BuscaResult>('/crm-vendas/busca/', {
        params: { q: q.trim(), limit: 5 },
      });
      setSearchResults(res.data);
    } catch {
      setSearchResults({ leads: [], oportunidades: [], contas: [] });
    } finally {
      setSearchLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (searchQuery.length < MIN_QUERY_LEN) {
      setSearchResults(null);
      setShowSearchDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(() => {
      fetchBusca(searchQuery);
      setShowSearchDropdown(true);
      debounceRef.current = null;
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, fetchBusca]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (novoRef.current && !novoRef.current.contains(e.target as Node)) {
        setShowNovoMenu(false);
      }
      if (suporteRef.current && !suporteRef.current.contains(e.target as Node)) {
        setShowSuporteMenu(false);
      }
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearchDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchSelect = useCallback(() => {
    setSearchQuery('');
    setSearchResults(null);
    setShowSearchDropdown(false);
  }, []);

  // Carregar nome da loja para o modal de suporte
  useEffect(() => {
    if (!slug) return;
    apiClient
      .get(`/superadmin/lojas/info_publica/?slug=${slug}`)
      .then((res) => setLojaNome(res.data?.nome || ''))
      .catch(() => setLojaNome(''));
  }, [slug]);

  const hasResults = searchResults && (
    searchResults.leads.length > 0 ||
    searchResults.oportunidades.length > 0 ||
    searchResults.contas.length > 0
  );

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
          onTouchStart={(e) => {
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
      <div className="flex-1 max-w-2xl hidden sm:block" ref={searchRef}>
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => searchQuery.length >= MIN_QUERY_LEN && setShowSearchDropdown(true)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                setShowSearchDropdown(false);
                (e.target as HTMLInputElement).blur();
              }
            }}
            placeholder="Buscar leads, oportunidades, contas..."
            className="w-full pl-9 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-[#0d1f3c] text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-[#0176d3] focus:border-transparent text-sm transition-all"
            aria-label="Buscar no CRM"
          />
          {showSearchDropdown && searchQuery.length >= MIN_QUERY_LEN && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-[#16325c] rounded-lg shadow-xl border border-gray-200 dark:border-[#0d1f3c] py-2 z-30 max-h-80 overflow-y-auto">
              {searchLoading ? (
                <div className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                  Buscando...
                </div>
              ) : !hasResults ? (
                <div className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                  Nenhum resultado encontrado
                </div>
              ) : (
                <div className="space-y-1">
                  {searchResults!.leads.length > 0 && (
                    <div className="px-3 py-1">
                      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                        Leads
                      </p>
                      {searchResults!.leads.map((l) => (
                        <Link
                          key={`lead-${l.id}`}
                          href={slug ? `/loja/${slug}/crm-vendas/leads?ver=${l.id}` : '#'}
                          onClick={handleSearchSelect}
                          className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-sm text-gray-900 dark:text-white"
                        >
                          <Users size={14} className="text-[#06a59a] shrink-0" />
                          <span className="truncate">{l.nome}</span>
                          {l.empresa && (
                            <span className="text-gray-500 dark:text-gray-400 truncate">• {l.empresa}</span>
                          )}
                        </Link>
                      ))}
                    </div>
                  )}
                  {searchResults!.oportunidades.length > 0 && (
                    <div className="px-3 py-1">
                      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                        Oportunidades
                      </p>
                      {searchResults!.oportunidades.map((o) => (
                        <Link
                          key={`opp-${o.id}`}
                          href={slug ? `/loja/${slug}/crm-vendas/pipeline` : '#'}
                          onClick={handleSearchSelect}
                          className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-sm text-gray-900 dark:text-white"
                        >
                          <DollarSign size={14} className="text-[#e287b2] shrink-0" />
                          <span className="truncate">{o.titulo}</span>
                          <span className="text-gray-500 dark:text-gray-400 shrink-0">
                            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(Number(o.valor))}
                          </span>
                        </Link>
                      ))}
                    </div>
                  )}
                  {searchResults!.contas.length > 0 && (
                    <div className="px-3 py-1">
                      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                        Contas
                      </p>
                      {searchResults!.contas.map((c) => (
                        <Link
                          key={`conta-${c.id}`}
                          href={slug ? `/loja/${slug}/crm-vendas/customers?ver=${c.id}` : '#'}
                          onClick={handleSearchSelect}
                          className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-sm text-gray-900 dark:text-white"
                        >
                          <Building2 size={14} className="text-[#0176d3] shrink-0" />
                          <span className="truncate">{c.nome}</span>
                          {c.segmento && (
                            <span className="text-gray-500 dark:text-gray-400 truncate">• {c.segmento}</span>
                          )}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center gap-1 sm:gap-2">
        {/* Botão Suporte */}
        <div className="relative" ref={suporteRef}>
          <button
            type="button"
            onClick={() => setShowSuporteMenu((v) => !v)}
            className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium transition-colors"
            title="Suporte"
          >
            <MessageCircle size={16} />
            <span>Suporte</span>
          </button>

          {/* Mobile Suporte Button */}
          <button
            type="button"
            onClick={() => setShowSuporteMenu((v) => !v)}
            className="lg:hidden p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
            aria-label="Suporte"
            title="Suporte"
          >
            <MessageCircle size={20} />
          </button>

          {showSuporteMenu && slug && (
            <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-[#16325c] rounded-lg shadow-lg border border-gray-200 dark:border-[#0d1f3c] py-1 z-20">
              <a
                href={`/loja/${slug}/suporte`}
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]"
                onClick={() => setShowSuporteMenu(false)}
              >
                <MessageCircle size={16} />
                Acompanhar chamados
              </a>
            </div>
          )}
        </div>

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
              <a
                href={`/loja/${slug}/crm-vendas/leads/novo`}
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]"
                onClick={() => setShowNovoMenu(false)}
              >
                <Users size={16} />
                Novo Lead
              </a>
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
                    {userRole === 'vendedor' ? 'Vendedor' : 'Administrador'}
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

      {/* Modal de Suporte */}
      {modalSuporteAberto && (
        <ModalChamado
          aberto={modalSuporteAberto}
          onFechar={() => setModalSuporteAberto(false)}
          lojaSlug={slug}
          lojaNome={lojaNome}
        />
      )}
    </header>
  );
}

// Memoização para evitar re-renders desnecessários
export default React.memo(HeaderCrm);

