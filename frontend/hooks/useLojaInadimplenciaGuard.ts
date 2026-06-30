'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

const ASSINATURA_PATH_RE = /\/assinatura\/?$/;
const LOGIN_PATH_RE = /\/login\/?$/;
const TROCAR_SENHA_PATH = '/loja/trocar-senha';

/**
 * Redireciona para /assinatura quando a loja está bloqueada por inadimplência.
 */
export function useLojaInadimplenciaGuard(slug: string) {
  const router = useRouter();
  const pathname = usePathname();
  const checkedRef = useRef('');

  useEffect(() => {
    if (!slug?.trim()) return;
    if (authService.getUserType() !== 'loja') return;
    if (ASSINATURA_PATH_RE.test(pathname) || LOGIN_PATH_RE.test(pathname) || pathname === TROCAR_SENHA_PATH) {
      return;
    }

    const key = `${slug}:${pathname}`;
    if (checkedRef.current === key) return;
    checkedRef.current = key;

    let cancelled = false;
    (async () => {
      try {
        const { data } = await apiClient.get('/superadmin/lojas/heartbeat/');
        if (cancelled) return;
        if (data?.is_blocked) {
          const target = `/loja/${slug}/assinatura`;
          if (!pathname.startsWith(target)) {
            router.replace(target);
          }
        }
      } catch {
        /* heartbeat falhou: middleware/API retorna 403 em rotas bloqueadas */
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [slug, pathname, router]);
}
