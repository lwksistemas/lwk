'use client';

import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { useCRMUIStore } from '@/store/crm-ui';
import { authService } from '@/lib/auth';
import {
  LayoutDashboard,
  Users,
  DollarSign,
  User,
  Calendar,
  LogOut,
  X,
  Settings,
  Bell,
  HelpCircle,
} from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';

interface Notificacao {
  id: number;
  titulo: string;
  mensagem: string;
  tipo: string;
  status: string;
  read_at: string | null;
  created_at: string;
}

interface SidebarCrmProps {
  lojaNome?: string;
  onLogout?: () => void;
}

export default function SidebarCrm({ lojaNome, onLogout }: SidebarCrmProps) {
  const { collapsed, toggle } = useCRMUIStore();
  const params = useParams();
  const pathname = usePathname();
  const slug = (params?.slug as string) || (typeof pathname === 'string' && pathname.startsWith('/loja/') ? pathname.split('/')[2] : '') || '';
  const base = `/loja/${slug}/crm-vendas`;
  const currentPath = typeof pathname === 'string' ? pathname : '';

  const [showNotifications, setShowNotifications] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [notificacoes, setNotificacoes] = useState<Notificacao[]>([]);
  const [notificacoesLoading, setNotificacoesLoading] = useState(false);
  const [notificacoesErro, setNotificacoesErro] = useState<string | null>(null);

  const carregarNotificacoes = useCallback(async () => {
    setNotificacoesLoading(true);
    setNotificacoesErro(null);
    try {
      const res = await apiClient.get<Notificacao[]>('notificacoes/');
      setNotificacoes(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Erro ao carregar notificações:', err);
      setNotificacoes([]);
      setNotificacoesErro('Não foi possível carregar as notificações.');
    } finally {
      setNotificacoesLoading(false);
    }
  }, []);

  const handleNotifications = () => {
    setShowNotifications(true);
    carregarNotificacoes();
    setTimeout(() => setShowNotifications(false), 5000);
  };

  const isActive = (href: string) => {
    if (href === base) return currentPath === base || currentPath === `${base}/`;
    return currentPath.startsWith(href);
  };

  const handleHelp = () => {
    setShowHelp(true);
  };


  // Fechar sidebar em mobile ao mudar de rota (evita re-renders desnecessários)
  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 768 && !collapsed) {
      toggle();
    }
  }, [currentPath]);

  // Prevenir scroll do body quando sidebar mobile está aberta
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    if (!collapsed && window.innerWidth < 768) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [collapsed]);

  return (
    <>
      {/* Backdrop para mobile */}
      {!collapsed && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={toggle}
          aria-hidden="true"
        />
      )}

      {/* Sidebar - Estilo Salesforce Lightning */}
      <aside
        className={`
          bg-white dark:bg-[#16325c] transition-all duration-300 h-full flex flex-col shrink-0
          fixed md:relative inset-y-0 left-0 z-50
          border-r border-gray-200 dark:border-[#0d1f3c]
          ${collapsed ? '-translate-x-full md:translate-x-0 md:w-16' : 'translate-x-0 w-64'}
        `}
      >
        {/* Header da Sidebar - Estilo Salesforce */}
        <div className="p-4 flex items-center justify-between border-b border-gray-200 dark:border-[#0d1f3c] min-h-[4rem]">
          {!collapsed && (
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {/* Logo/Avatar estilo Salesforce */}
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
          
          {/* Botão de fechar (apenas mobile) */}
          {!collapsed && (
            <button
              type="button"
              onClick={toggle}
              className="md:hidden p-1.5 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-gray-600 dark:text-gray-300 transition-colors"
              aria-label="Fechar menu"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Navegação - Estilo Salesforce Lightning */}
        <nav className="space-y-1 p-2 flex-1 overflow-y-auto">
          <Link
            href={base}
            className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-all ${
              isActive(base)
                ? 'bg-[#0176d3] text-white shadow-sm'
                : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c]'
            }`}
            title={collapsed ? 'Home' : undefined}
          >
            <LayoutDashboard size={18} className="shrink-0" />
            {!collapsed && <span>Home</span>}
          </Link>
          
          <Link
            href={`${base}/leads`}
            className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-all ${
              isActive(`${base}/leads`)
                ? 'bg-[#0176d3] text-white shadow-sm'
                : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c]'
            }`}
            title={collapsed ? 'Leads' : undefined}
          >
            <Users size={18} className="shrink-0" />
            {!collapsed && <span>Leads</span>}
          </Link>
          
          <Link
            href={`${base}/pipeline`}
            className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-all ${
              isActive(`${base}/pipeline`)
                ? 'bg-[#0176d3] text-white shadow-sm'
                : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c]'
            }`}
            title={collapsed ? 'Oportunidades' : undefined}
          >
            <DollarSign size={18} className="shrink-0" />
            {!collapsed && <span>Oportunidades</span>}
          </Link>
          
          <Link
            href={`${base}/customers`}
            className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-all ${
              isActive(`${base}/customers`)
                ? 'bg-[#0176d3] text-white shadow-sm'
                : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c]'
            }`}
            title={collapsed ? 'Contas' : undefined}
          >
            <User size={18} className="shrink-0" />
            {!collapsed && <span>Contas</span>}
          </Link>

          <Link
            href={`${base}/calendario`}
            className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-all ${
              isActive(`${base}/calendario`)
                ? 'bg-[#0176d3] text-white shadow-sm'
                : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c]'
            }`}
            title={collapsed ? 'Calendário' : undefined}
          >
            <Calendar size={18} className="shrink-0" />
            {!collapsed && <span>Calendário</span>}
          </Link>

          {/* Divider */}
          {!collapsed && (
            <div className="my-2 border-t border-gray-200 dark:border-[#0d1f3c]" />
          )}

          {/* Ações secundárias */}
          <button
            type="button"
            onClick={handleNotifications}
            className="flex items-center gap-3 px-3 py-2 rounded text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] w-full text-left transition-all"
            title={collapsed ? 'Notificações' : undefined}
          >
            <Bell size={18} className="shrink-0" />
            {!collapsed && <span>Notificações</span>}
          </button>

          <button
            type="button"
            onClick={handleHelp}
            className="flex items-center gap-3 px-3 py-2 rounded text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] w-full text-left transition-all"
            title={collapsed ? 'Ajuda' : undefined}
          >
            <HelpCircle size={18} className="shrink-0" />
            {!collapsed && <span>Ajuda</span>}
          </button>
        </nav>

        {/* Footer da Sidebar - Estilo Salesforce */}
        <div className="p-2 border-t border-gray-200 dark:border-[#0d1f3c] space-y-1">
          {!authService.isVendedor() && (
            <Link
              href={`${base}/configuracoes`}
              className={`flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-all ${
                isActive(`${base}/configuracoes`)
                  ? 'bg-[#0176d3] text-white shadow-sm'
                  : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#0d1f3c]'
              }`}
              title={collapsed ? 'Configurações' : undefined}
            >
              <Settings size={18} className="shrink-0" />
              {!collapsed && <span>Configurações</span>}
            </Link>
          )}

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
      </aside>

      {/* Painel de Notificações */}
      {showNotifications && (
        <div className="fixed top-4 right-4 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 max-w-sm animate-slide-in max-h-[80vh] overflow-hidden flex flex-col">
          <div className="flex items-start gap-3 shrink-0">
            <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
              <Bell size={20} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 dark:text-white text-sm">
                Notificações
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Sincronizado com o sistema (agendamentos, tarefas, lembretes, financeiro)
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowNotifications(false)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 shrink-0"
            >
              <X size={16} />
            </button>
          </div>
          <div className="mt-3 overflow-y-auto flex-1 min-h-0">
            {notificacoesLoading ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
            ) : notificacoesErro ? (
              <p className="text-sm text-amber-600 dark:text-amber-400">{notificacoesErro}</p>
            ) : notificacoes.length === 0 ? (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Você não tem novas notificações no momento.
              </p>
            ) : (
              <ul className="space-y-2">
                {notificacoes.slice(0, 10).map((n) => (
                  <li
                    key={n.id}
                    className={`text-sm p-2 rounded border-l-2 ${
                      n.read_at ? 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400' : 'border-[#0176d3] bg-blue-50/50 dark:bg-blue-900/10 text-gray-900 dark:text-white'
                    }`}
                  >
                    <span className="font-medium">{n.titulo}</span>
                    <p className="text-xs mt-0.5 line-clamp-2">{n.mensagem}</p>
                  </li>
                ))}
                {notificacoes.length > 10 && (
                  <li className="text-xs text-gray-500 dark:text-gray-400">
                    +{notificacoes.length - 10} mais
                  </li>
                )}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Modal de Ajuda */}
      {showHelp && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setShowHelp(false)}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                    <HelpCircle size={20} />
                  </div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Central de Ajuda
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={() => setShowHelp(false)}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Bem-vindo ao CRM de Vendas
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Sistema completo de gestão de vendas estilo Salesforce Lightning.
                  </p>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3 mb-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-2">
                    O que está sincronizado
                  </h4>
                  <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                    <li>• <strong>Calendário</strong> — Atividades do CRM com Google Calendar</li>
                    <li>• <strong>Notificações</strong> — Agendamentos, lembretes, financeiro</li>
                  </ul>
                </div>

                <div className="space-y-4">
                  <div className="border-l-4 border-[#0176d3] pl-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                      Home
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Dashboard com métricas, gráficos e visão geral das vendas.
                    </p>
                  </div>

                  <div className="border-l-4 border-[#06a59a] pl-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                      Leads
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Gerencie seus leads, qualifique e converta em oportunidades.
                    </p>
                  </div>

                  <div className="border-l-4 border-[#ffb75d] pl-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                      Oportunidades
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Pipeline visual com etapas de vendas e acompanhamento de negociações.
                    </p>
                  </div>

                  <div className="border-l-4 border-[#e287b2] pl-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                      Contas
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Cadastro completo de clientes com informações de contato e segmentação.
                    </p>
                  </div>

                  <div className="border-l-4 border-[#0176d3] pl-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                      Calendário
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Visualize e gerencie reuniões, ligações e tarefas em um calendário estilo Google, sincronizado com as atividades do CRM.
                    </p>
                  </div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                  <h4 className="font-semibold text-blue-900 dark:text-blue-200 text-sm mb-2">
                    💡 Dica
                  </h4>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    Use os atalhos de teclado para navegar mais rápido. Pressione <kbd className="px-2 py-1 bg-white dark:bg-gray-700 rounded border border-blue-300 dark:border-blue-700 text-xs">Ctrl + K</kbd> para busca rápida.
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => setShowHelp(false)}
                  className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded transition-colors text-sm font-medium"
                >
                  Entendi
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
