'use client';

import { useEffect, useState, useCallback } from 'react';
import { authService } from '@/lib/auth';

/**
 * Centraliza autenticação e logout para páginas do dashboard da loja.
 * Retorna slug resolvido, path de login, handler de logout e se o usuário é loja.
 */
export function useLojaAuth(paramSlug?: string | null) {
  const [slug, setSlug] = useState('');
  const [isLoja, setIsLoja] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const userType = authService.getUserType();
    const resolvedSlug = (paramSlug ?? authService.getLojaSlug() ?? '').toString();
    setSlug(resolvedSlug);
    setIsLoja(userType === 'loja');
    setReady(true);
  }, [paramSlug]);

  const loginPath = slug ? `/loja/${slug}/login` : '/loja/login';

  const handleLogout = useCallback(() => {
    authService.logout();
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('current_loja_id');
      // Redirecionar para login da loja (window.location garante reload e evita ir para home)
      let targetSlug = slug;
      if (!targetSlug && window.location.pathname.includes('/loja/')) {
        const match = window.location.pathname.match(/^\/loja\/([^/]+)/);
        if (match) targetSlug = match[1];
      }
      const loginUrl = targetSlug ? `/loja/${targetSlug}/login` : '/';
      window.location.href = loginUrl;
    }
  }, [slug]);

  return { slug, loginPath, handleLogout, isLoja, ready };
}
