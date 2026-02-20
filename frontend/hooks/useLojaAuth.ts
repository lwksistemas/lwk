'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';

/**
 * Centraliza autenticação e logout para páginas do dashboard da loja.
 * Retorna slug resolvido, path de login, handler de logout e se o usuário é loja.
 */
export function useLojaAuth(paramSlug?: string | null) {
  const router = useRouter();
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
    }
    router.push(slug ? `/loja/${slug}/login` : '/loja/login');
  }, [router, slug]);

  return { slug, loginPath, handleLogout, isLoja, ready };
}
