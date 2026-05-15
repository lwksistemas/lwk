'use client';

import { useEffect, useRef } from 'react';
import axios from 'axios';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

/**
 * Monitor de sessão única: GET /superadmin/lojas/heartbeat/ a cada 60s quando a aba está visível.
 * Usa axios direto (sem interceptor de refresh) para detectar SESSION_REPLACED.
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
        const sid = sessionStorage.getItem('session_id') || '';
        const accessToken = sessionStorage.getItem('access_token') || '';
        const base = getPrimaryApiBaseUrl();
        await axios.get(`${base}/superadmin/lojas/heartbeat/${sid ? `?sid=${sid}` : ''}`, {
          headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
        });
      } catch (err: any) {
        const code = err?.response?.data?.code;
        if (code === 'SESSION_REPLACED') {
          sessionStorage.removeItem('access_token');
          sessionStorage.removeItem('refresh_token');
          sessionStorage.removeItem('session_id');
          sessionStorage.removeItem('user_type');
          sessionStorage.removeItem('loja_slug');
          const path = window.location.pathname;
          const lojaMatch = path.match(/^\/loja\/([^/]+)/);
          window.location.href = lojaMatch ? `/loja/${lojaMatch[1]}/login` : '/superadmin/login';
          return;
        }
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
