'use client';

import { useEffect, useRef } from 'react';
import apiClient from '@/lib/api-client';

/**
 * Monitor de sessão única: GET /superadmin/lojas/heartbeat/ a cada 60s quando a aba está visível.
 * Com a aba em segundo plano, o intervalo pausa (menos carga no Heroku).
 */
const CHECK_INTERVAL_MS = 60000;

export function useSessionMonitor() {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isCheckingRef = useRef(false);

  useEffect(() => {
    const checkSession = async () => {
      if (isCheckingRef.current) return;
      const token = typeof window !== 'undefined' ? sessionStorage.getItem('access_token') : null;
      if (!token) return;

      isCheckingRef.current = true;
      try {
        await apiClient.get('/superadmin/lojas/heartbeat/');
      } catch {
        // 401: interceptor trata DIFFERENT_SESSION → logout + redirect
      } finally {
        isCheckingRef.current = false;
      }
    };

    const clearTimer = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };

    const startTimer = () => {
      clearTimer();
      intervalRef.current = setInterval(checkSession, CHECK_INTERVAL_MS);
    };

    const onVisibility = () => {
      if (document.hidden) {
        clearTimer();
        return;
      }
      void checkSession();
      startTimer();
    };

    if (typeof document === 'undefined') return;

    document.addEventListener('visibilitychange', onVisibility);

    if (!document.hidden) {
      void checkSession();
      startTimer();
    }

    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      clearTimer();
    };
  }, []);
}
