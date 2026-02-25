'use client';

import { useEffect, useRef } from 'react';
import apiClient from '@/lib/api-client';

/**
 * Hook para monitorar sessão em tempo real (sessão única).
 * Chama o backend a cada 60s; se outra sessão foi aberta, o backend retorna 401
 * e o interceptor do apiClient faz logout e redireciona para o login.
 * 
 * Otimização v663: Aumentado de 15s para 60s para reduzir carga no servidor
 * (de 4 req/min para 1 req/min por usuário = 75% de redução)
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
        // 401 ou outro erro: o interceptor do apiClient já trata (DIFFERENT_SESSION → logout + redirect)
      } finally {
        isCheckingRef.current = false;
      }
    };

    intervalRef.current = setInterval(checkSession, CHECK_INTERVAL_MS);
    checkSession();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);
}
