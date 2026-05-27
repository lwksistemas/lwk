'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchNotifications, markNotificationAsRead } from '@/services/notifications';
import type { Notification } from '@/types/notification';

const POLL_INTERVAL_MS = 60000; // 60s

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (typeof window === 'undefined') return;
    const token = sessionStorage.getItem('access_token');
    if (!token) {
      setNotifications([]);
      setLoading(false);
      return;
    }
    try {
      const data = await fetchNotifications();
      setNotifications(data);
    } catch {
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const read = useCallback(async (id: number) => {
    try {
      await markNotificationAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: 'lido' as const } : n))
      );
    } catch {
      // atualização otimista mesmo em falha
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: 'lido' as const } : n))
      );
    }
  }, []);

  const unreadCount = notifications.filter((n) => n.status !== 'lido').length;

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
      interval = setInterval(load, POLL_INTERVAL_MS);
    };

    const onVisibility = () => {
      if (document.hidden) {
        clear();
        return;
      }
      void load();
      start();
    };

    if (typeof document === 'undefined') return;

    document.addEventListener('visibilitychange', onVisibility);
    if (!document.hidden) {
      void load();
      start();
    }

    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      clear();
    };
  }, [load]);

  return { notifications, unreadCount, read, loading };
}
