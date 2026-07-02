'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, usePathname } from 'next/navigation';
import { useCRMUIStore } from '@/store/crm-ui';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';

export interface CrmSidebarNotificacao {
  id: number;
  titulo: string;
  mensagem: string;
  tipo: string;
  status: string;
  read_at: string | null;
  created_at: string;
}

export function useCrmSidebar() {
  const { collapsed, toggle } = useCRMUIStore();
  const params = useParams();
  const pathname = usePathname();
  const slug =
    (params?.slug as string) ||
    (typeof pathname === 'string' && pathname.startsWith('/loja/') ? pathname.split('/')[2] : '') ||
    '';
  const base = `/loja/${slug}/crm-vendas`;
  const currentPath = typeof pathname === 'string' ? pathname : '';

  const [showNotifications, setShowNotifications] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [notificacoes, setNotificacoes] = useState<CrmSidebarNotificacao[]>([]);
  const [notificacoesLoading, setNotificacoesLoading] = useState(false);
  const [notificacoesErro, setNotificacoesErro] = useState<string | null>(null);

  const carregarNotificacoes = useCallback(async () => {
    setNotificacoesLoading(true);
    setNotificacoesErro(null);
    try {
      const res = await apiClient.get<CrmSidebarNotificacao[]>('notificacoes/');
      setNotificacoes(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      logger.warn('Erro ao carregar notificações:', err);
      setNotificacoes([]);
      setNotificacoesErro('Não foi possível carregar as notificações.');
    } finally {
      setNotificacoesLoading(false);
    }
  }, []);

  const handleNotifications = () => {
    setShowNotifications(true);
    void carregarNotificacoes();
    setTimeout(() => setShowNotifications(false), 5000);
  };

  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 768 && !collapsed) {
      toggle();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPath]);

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

  return {
    collapsed,
    toggle,
    slug,
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
  };
}
