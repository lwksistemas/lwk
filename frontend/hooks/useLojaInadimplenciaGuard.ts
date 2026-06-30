'use client';

import { useEffect, useState, useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import type { AssinaturaAviso } from '@/lib/assinatura-aviso';

const ASSINATURA_PATH_RE = /\/assinatura\/?$/;
const LOGIN_PATH_RE = /\/login\/?$/;
const TROCAR_SENHA_PATH = '/loja/trocar-senha';

export type { AssinaturaAviso };

function dismissKey(slug: string) {
  const hoje = new Date().toISOString().slice(0, 10);
  return `lwk_aviso_assinatura_${slug}_${hoje}`;
}

function isDismissedToday(slug: string) {
  if (typeof window === 'undefined') return false;
  return sessionStorage.getItem(dismissKey(slug)) === '1';
}

function hasLojaSession(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(sessionStorage.getItem('session_id') || sessionStorage.getItem('access_token'));
}

/**
 * Bloqueio por inadimplência + aviso de vencimento (5 dias antes).
 */
export function useLojaInadimplenciaGuard(slug: string) {
  const router = useRouter();
  const pathname = usePathname();
  const [aviso, setAviso] = useState<AssinaturaAviso | null>(null);
  const [avisoVisivel, setAvisoVisivel] = useState(false);

  const dismissAviso = useCallback(() => {
    if (slug?.trim()) {
      sessionStorage.setItem(dismissKey(slug.trim()), '1');
    }
    setAvisoVisivel(false);
  }, [slug]);

  useEffect(() => {
    if (!slug?.trim()) return;
    if (LOGIN_PATH_RE.test(pathname) || pathname === TROCAR_SENHA_PATH) {
      return;
    }

    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const applyAviso = (avisoData: AssinaturaAviso | null | undefined) => {
      if (avisoData?.mensagem) {
        setAviso(avisoData);
        setAvisoVisivel(!isDismissedToday(slug.trim()));
      } else {
        setAviso(null);
        setAvisoVisivel(false);
      }
    };

    const fetchStatus = async (): Promise<boolean> => {
      if (!hasLojaSession()) return false;
      if (authService.getUserType() !== 'loja') return false;

      try {
        const { data } = await apiClient.get('/superadmin/lojas/heartbeat/', {
          params: { slug: slug.trim() },
        });
        if (cancelled) return true;

        if (data?.is_blocked) {
          setAviso(null);
          setAvisoVisivel(false);
          const target = `/loja/${slug}/assinatura`;
          if (!ASSINATURA_PATH_RE.test(pathname) && !pathname.startsWith(target)) {
            router.replace(target);
          }
          return true;
        }

        applyAviso(data?.assinatura_aviso as AssinaturaAviso | null | undefined);
        return true;
      } catch {
        return false;
      }
    };

    const scheduleRetry = (attempt: number) => {
      if (cancelled || attempt > 12) return;
      retryTimer = setTimeout(async () => {
        const ok = await fetchStatus();
        if (!ok && !cancelled) scheduleRetry(attempt + 1);
      }, 400);
    };

    void (async () => {
      const ok = await fetchStatus();
      if (!ok && !cancelled) scheduleRetry(1);
    })();

    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, [slug, pathname, router]);

  return { aviso, avisoVisivel, dismissAviso };
}
