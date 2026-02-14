'use client';

import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';

/**
 * Hook para monitorar sessão em tempo real
 * Verifica a cada 10 segundos se a sessão ainda é válida
 * Se detectar que foi desconectado (outra sessão ativa), faz logout automático
 */
export function useSessionMonitor() {
  const router = useRouter();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isCheckingRef = useRef(false);

  useEffect(() => {
    const checkSession = async () => {
      // Evitar múltiplas verificações simultâneas
      if (isCheckingRef.current) return;
      
      isCheckingRef.current = true;
      
      try {
        const token = authService.getToken();
        if (!token) {
          // Sem token, redirecionar para login
          authService.logout();
          return;
        }

        // Fazer uma requisição simples para verificar se o token ainda é válido
        const response = await fetch('/api/auth/verify-session', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.status === 401) {
          // Sessão inválida - outra sessão foi criada
          console.warn('🚨 Sessão invalidada - Outra sessão ativa detectada');
          authService.logout();
          
          // Mostrar mensagem ao usuário
          alert('Sua sessão foi encerrada porque você fez login em outro dispositivo.');
          
          // Redirecionar para login
          window.location.href = '/';
        }
      } catch (error) {
        console.error('Erro ao verificar sessão:', error);
      } finally {
        isCheckingRef.current = false;
      }
    };

    // Verificar a cada 10 segundos
    intervalRef.current = setInterval(checkSession, 10000);

    // Verificar imediatamente ao montar
    checkSession();

    // Limpar intervalo ao desmontar
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [router]);
}
