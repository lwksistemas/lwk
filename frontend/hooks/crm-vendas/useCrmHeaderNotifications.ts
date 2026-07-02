'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { CRM_HEADER_NOTIFICATIONS_POLL_MS, type CrmHeaderNotificacao } from '@/lib/crm-header';

export function useCrmHeaderNotifications() {
  const [showNotifs, setShowNotifs] = useState(false);
  const [notifs, setNotifs] = useState<CrmHeaderNotificacao[]>([]);
  const [notifsNaoLidas, setNotifsNaoLidas] = useState(0);

  const fetchNotifs = useCallback(async () => {
    try {
      const res = await apiClient.get<CrmHeaderNotificacao[]>('/notificacoes/');
      const list = Array.isArray(res.data) ? res.data : [];
      setNotifs(list);
      setNotifsNaoLidas(list.filter((n) => n.status !== 'lido').length);
    } catch {
      /* silencioso */
    }
  }, []);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;

    const clear = () => {
      if (interval) {
        clearInterval(interval);
        interval = null;
      }
    };

    const start = () => {
      clear();
      interval = setInterval(fetchNotifs, CRM_HEADER_NOTIFICATIONS_POLL_MS);
    };

    const onVisibility = () => {
      if (document.hidden) {
        clear();
        return;
      }
      void fetchNotifs();
      start();
    };

    document.addEventListener('visibilitychange', onVisibility);
    if (!document.hidden) {
      void fetchNotifs();
      start();
    }

    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      clear();
    };
  }, [fetchNotifs]);

  const toggleNotifs = useCallback(() => {
    setShowNotifs((prev) => {
      const next = !prev;
      if (next) void fetchNotifs();
      return next;
    });
  }, [fetchNotifs]);

  const marcarComoLida = useCallback((id: number) => {
    apiClient.post(`/notificacoes/${id}/read/`).catch(() => {});
    setNotifs((prev) => prev.map((x) => (x.id === id ? { ...x, status: 'lido' } : x)));
    setNotifsNaoLidas((prev) => Math.max(0, prev - 1));
  }, []);

  const limparNotifs = useCallback(() => {
    apiClient
      .post('/notificacoes/clear/')
      .then(() => {
        setNotifs([]);
        setNotifsNaoLidas(0);
      })
      .catch(() => {});
  }, []);

  return {
    showNotifs,
    setShowNotifs,
    notifs,
    notifsNaoLidas,
    toggleNotifs,
    marcarComoLida,
    limparNotifs,
  };
}
