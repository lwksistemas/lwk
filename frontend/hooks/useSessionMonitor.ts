'use client';

import { useEffect, useRef } from 'react';
import axios from 'axios';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';
import { USE_JWT_HTTPONLY_COOKIES } from '@/lib/auth-cookies';
import { clearSessionAndRedirect, getLoginUrlForRedirect, tryRefreshAccessToken } from '@/lib/api-client';

/**
 * Monitor de sessão única: GET /superadmin/lojas/heartbeat/ a cada 60s quando a aba está visível.
 * Usa axios direto (sem interceptor de refresh) para detectar SESSION_REPLACED.
 */
const CHECK_INTERVAL_MS = 60000;
const PROACTIVE_REFRESH_MS = 25 * 60 * 1000;
const INACTIVITY_LIMIT_MS = 2 * 60 * 60 * 1000; // Não renovar se inativo por 2h
const ACTIVITY_STORAGE_KEY = 'lwk_last_activity';

function hasActiveSession(): boolean {
  if (typeof window === 'undefined') return false;
  if (USE_JWT_HTTPONLY_COOKIES) {
    return Boolean(sessionStorage.getItem('session_id'));
  }
  return Boolean(sessionStorage.getItem('access_token'));
}

export function useSessionMonitor() {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isCheckingRef = useRef(false);
  const lastRefreshRef = useRef(0);

  useEffect(() => {
    const checkSession = async () => {
      if (isCheckingRef.current) return;
      if (!hasActiveSession()) return;

      isCheckingRef.current = true;
      try {
        const now = Date.now();
        const lastActivity = parseInt(localStorage.getItem(ACTIVITY_STORAGE_KEY) || String(now), 10) || now;
        const inactiveMs = now - lastActivity;

        // Não renovar token se inativo por mais de 2h
        if (inactiveMs >= INACTIVITY_LIMIT_MS) {
          void clearSessionAndRedirect(
            getLoginUrlForRedirect(),
            'Sessão encerrada por inatividade. Faça login novamente.',
          );
          return;
        }

        if (now - lastRefreshRef.current >= PROACTIVE_REFRESH_MS) {
          const refreshed = await tryRefreshAccessToken();
          if (refreshed) lastRefreshRef.current = now;
        }

        const sid = sessionStorage.getItem('session_id') || '';
        const accessToken = sessionStorage.getItem('access_token') || '';
        const base = getPrimaryApiBaseUrl();
        const headers: Record<string, string> = {};
        if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
        if (sid) headers['X-Session-ID'] = sid;
        await axios.get(`${base}/superadmin/lojas/heartbeat/${sid ? `?sid=${sid}` : ''}`, {
          headers,
          withCredentials: USE_JWT_HTTPONLY_COOKIES,
        });
      } catch (err: unknown) {
        const code = (err as { response?: { data?: { code?: string } } })?.response?.data?.code;
        if (code === 'SESSION_REPLACED') {
          void clearSessionAndRedirect(
            getLoginUrlForRedirect(),
            'Sessão encerrada — login realizado em outro dispositivo. Faça login novamente.',
          );
        }
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
