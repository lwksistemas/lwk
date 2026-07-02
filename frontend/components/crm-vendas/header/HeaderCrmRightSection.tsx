'use client';

import Link from 'next/link';
import { Bell, DollarSign, HelpCircle, MessageCircle, Plus, User, Users } from 'lucide-react';
import ModalChamado from '@/components/suporte/ModalChamado';
import type { CrmHeaderNotificacao } from '@/lib/crm-header';

interface Props {
  slug: string;
  userName: string;
  userRole: 'vendedor' | 'administrador';
  showUserMenu: boolean;
  setShowUserMenu: (v: boolean) => void;
  showNovoMenu: boolean;
  setShowNovoMenu: (v: boolean | ((prev: boolean) => boolean)) => void;
  showSuporteMenu: boolean;
  setShowSuporteMenu: (v: boolean | ((prev: boolean) => boolean)) => void;
  novoRef: React.RefObject<HTMLDivElement | null>;
  suporteRef: React.RefObject<HTMLDivElement | null>;
  modalSuporteAberto: boolean;
  setModalSuporteAberto: (v: boolean) => void;
  lojaNome: string;
  showNotifs: boolean;
  setShowNotifs: (v: boolean) => void;
  notifs: CrmHeaderNotificacao[];
  notifsNaoLidas: number;
  toggleNotifs: () => void;
  marcarComoLida: (id: number) => void;
  limparNotifs: () => void;
}

export function HeaderCrmRightSection({
  slug,
  userName,
  userRole,
  showUserMenu,
  setShowUserMenu,
  showNovoMenu,
  setShowNovoMenu,
  showSuporteMenu,
  setShowSuporteMenu,
  novoRef,
  suporteRef,
  modalSuporteAberto,
  setModalSuporteAberto,
  lojaNome,
  showNotifs,
  setShowNotifs,
  notifs,
  notifsNaoLidas,
  toggleNotifs,
  marcarComoLida,
  limparNotifs,
}: Props) {
  return (
    <>
      <div className="flex items-center gap-1 sm:gap-2">
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
          <button
            type="button"
            onClick={() => setShowSuporteMenu((v) => !v)}
            className="lg:hidden p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
            aria-label="Suporte"
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

        <div className="relative" ref={novoRef}>
          <button
            type="button"
            onClick={() => setShowNovoMenu((v) => !v)}
            className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors"
          >
            <Plus size={16} />
            <span>Novo</span>
          </button>
          <button
            type="button"
            onClick={() => setShowNovoMenu((v) => !v)}
            className="lg:hidden p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
            aria-label="Novo"
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

        <div className="relative">
          <button
            type="button"
            onClick={toggleNotifs}
            className="relative p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
            aria-label="Notificações"
          >
            <Bell size={20} />
            {notifsNaoLidas > 0 && (
              <span className="absolute top-0.5 right-0.5 min-w-[16px] h-4 px-1 bg-red-500 rounded-full text-[10px] font-bold text-white flex items-center justify-center">
                {notifsNaoLidas > 9 ? '9+' : notifsNaoLidas}
              </span>
            )}
          </button>
          {showNotifs && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowNotifs(false)} />
              <div className="fixed sm:absolute right-2 sm:right-0 left-2 sm:left-auto top-14 sm:top-auto sm:mt-2 w-auto sm:w-80 bg-white dark:bg-[#16325c] rounded-lg shadow-xl border border-gray-200 dark:border-[#0d1f3c] z-20 max-h-[70vh] sm:max-h-80 overflow-y-auto">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-[#0d1f3c] flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">Notificações</p>
                  <div className="flex items-center gap-2">
                    {notifs.length > 0 && (
                      <button
                        type="button"
                        onClick={limparNotifs}
                        className="text-xs text-red-500 hover:text-red-700 dark:text-red-400 font-medium"
                      >
                        Limpar
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setShowNotifs(false)}
                      className="sm:hidden p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                {notifs.length === 0 ? (
                  <p className="px-4 py-6 text-sm text-gray-500 dark:text-gray-400 text-center">
                    Nenhuma notificação
                  </p>
                ) : (
                  notifs.slice(0, 10).map((n) => (
                    <div
                      key={n.id}
                      className={`px-4 py-3 border-b border-gray-100 dark:border-[#0d1f3c] ${
                        n.status !== 'lido' ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''
                      }`}
                      onClick={() => {
                        if (n.status !== 'lido') marcarComoLida(n.id);
                      }}
                    >
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{n.titulo}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{n.mensagem}</p>
                      <p className="text-[10px] text-gray-400 mt-1">
                        {new Date(n.created_at).toLocaleString('pt-BR')}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </div>

        <button
          type="button"
          className="hidden sm:flex p-2 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] transition-colors text-gray-600 dark:text-gray-300"
          aria-label="Ajuda"
        >
          <HelpCircle size={20} />
        </button>

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
          {showUserMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowUserMenu(false)} />
              <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-[#16325c] rounded-lg shadow-lg border border-gray-200 dark:border-[#0d1f3c] z-20 py-1">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-[#0d1f3c]">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{userName}</p>
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
                  Alternar Tema
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {modalSuporteAberto && (
        <ModalChamado
          aberto={modalSuporteAberto}
          onFechar={() => setModalSuporteAberto(false)}
          lojaSlug={slug}
          lojaNome={lojaNome}
        />
      )}
    </>
  );
}
