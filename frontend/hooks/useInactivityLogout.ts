'use client';

import { useEffect, useRef, useCallback } from 'react';
import { clearSessionAndRedirect, getLoginUrlForRedirect } from '@/lib/api-client';

/**
 * Logout automático após inatividade.
 * Monitora interações reais do usuário (click, keydown, scroll, touch).
 * Após INACTIVITY_TIMEOUT_MS sem interação, faz logout.
 */
const INACTIVITY_TIMEOUT_MS = 2 * 60 * 60 * 1000; // 2 horas
const STORAGE_KEY = 'lwk_last_activity';

function hasActiveSession(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(
    sessionStorage.getItem('access_token') || sessionStorage.getItem('session_id')
  );
}

function getLastActivity(): number {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored ? parseInt(stored, 10) : Date.now();
}

function setLastActivity(): void {
  localStorage.setItem(STORAGE_KEY, String(Date.now()));
}

export function useInactivityLogout() {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const checkInactivity = useCallback(() => {
    if (!hasActiveSession()) return;
    const elapsed = Date.now() - getLastActivity();
    if (elapsed >= INACTIVITY_TIMEOUT_MS) {
      void clearSessionAndRedirect(
        getLoginUrlForRedirect(),
        'Sessão encerrada por inatividade. Faça login novamente.',
      );
    }
  }, []);

  const resetTimer = useCallback(() => {
    setLastActivity();
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(checkInactivity, INACTIVITY_TIMEOUT_MS);
  }, [checkInactivity]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!hasActiveSession()) return;

    // Inicializar
    setLastActivity();
    timerRef.current = setTimeout(checkInactivity, INACTIVITY_TIMEOUT_MS);

    // Eventos de atividade do usuário
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach((event) => window.addEventListener(event, resetTimer, { passive: true }));

    // Verificar ao voltar à aba (pode ter ficado inativa em background)
    const onVisibility = () => {
      if (!document.hidden) checkInactivity();
    };
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      events.forEach((event) => window.removeEventListener(event, resetTimer));
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [checkInactivity, resetTimer]);
}
