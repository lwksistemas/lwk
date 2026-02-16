'use client';

import { useEffect, useState, useCallback } from 'react';
import { fetchNotifications, markNotificationAsRead } from '@/services/notifications';
import type { Notification } from '@/types/notification';

const POLL_INTERVAL_MS = 30000; // 30s

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (typeof window === 'undefined') return;
    const token = sessionStorage.getItem('access_token') || localStorage.getItem('token');
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
    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [load]);

  return { notifications, unreadCount, read, loading };
}
