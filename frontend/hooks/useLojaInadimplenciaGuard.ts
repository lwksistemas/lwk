'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { usePathname } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { resolveLojaApiSlug } from '@/lib/resolve-loja-slug';
import {
  calcularAvisoAssinaturaLocal,
  type AssinaturaAviso,
} from '@/lib/assinatura-aviso';
import {
  clearStoreBlockedMark,
  isAssinaturaPath,
  isStoreBlockedMarked,
  markStoreBlocked,
  redirectToAssinatura,
} from '@/lib/loja-bloqueio-inadimplencia';

const LOGIN_PATH_RE = /\/login\/?$/;
const TROCAR_SENHA_PATH = '/loja/trocar-senha';

export type { AssinaturaAviso };

function hasLojaSession(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(sessionStorage.getItem('session_id') || sessionStorage.getItem('access_token'));
}

/**
 * Bloqueio por inadimplência + aviso de vencimento (5 dias antes).
 * Na rota /assinatura não redireciona nem consulta heartbeat (evita loop e 429).
 */
export function useLojaInadimplenciaGuard(slug: string) {
  const pathname = usePathname();
  const [aviso, setAviso] = useState<AssinaturaAviso | null>(null);
  const fetchingRef = useRef(false);
  const pathnameRef = useRef(pathname);
  pathnameRef.current = pathname;

  const applyAviso = useCallback((avisoData: AssinaturaAviso | null | undefined) => {
    if (avisoData?.mensagem) {
      setAviso(avisoData);
    } else {
      setAviso(null);
    }
  }, []);

  const redirectIfBlocked = useCallback((urlSlug: string): boolean => {
    if (isAssinaturaPath(pathnameRef.current)) {
      return false;
    }
    markStoreBlocked();
    setAviso(null);
    return redirectToAssinatura(urlSlug);
  }, []);

  const checkInfoPublicaBlocked = useCallback(async (urlSlug: string): Promise<boolean> => {
    try {
      const { data } = await apiClient.get<{ is_blocked?: boolean; id?: number; slug?: string }>(
        `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(urlSlug)}`,
      );
      if (data?.id) {
        sessionStorage.setItem('current_loja_id', String(data.id));
      }
      if (data?.slug) {
        sessionStorage.setItem('loja_slug', data.slug);
      }
      if (data?.is_blocked) {
        return redirectIfBlocked(urlSlug);
      }
      clearStoreBlockedMark();
      return false;
    } catch {
      return false;
    }
  }, [redirectIfBlocked]);

  const fetchViaFinanceiro = useCallback(async (urlSlug: string): Promise<boolean> => {
    if (isAssinaturaPath(pathnameRef.current) || isStoreBlockedMarked()) return false;
    try {
      const apiSlug = await resolveLojaApiSlug(urlSlug);
      const { data } = await apiClient.get(`/superadmin/loja/${apiSlug}/financeiro/`);
      const fin = data?.financeiro;
      const avisoApi = data?.assinatura_aviso as AssinaturaAviso | null | undefined;
      const avisoCalc = avisoApi ?? calcularAvisoAssinaturaLocal(fin?.data_proxima_cobranca);
      if (data?.loja?.id) {
        sessionStorage.setItem('current_loja_id', String(data.loja.id));
      }
      applyAviso(avisoCalc);
      return Boolean(avisoCalc?.mensagem);
    } catch {
      return false;
    }
  }, [applyAviso]);

  const fetchStatus = useCallback(async (): Promise<void> => {
    if (fetchingRef.current) return;
    if (!slug?.trim()) return;
    if (!hasLojaSession()) return;
    if (authService.getUserType() !== 'loja') return;

    const urlSlug = slug.trim();
    const currentPath = pathnameRef.current;

    if (isAssinaturaPath(currentPath)) {
      clearStoreBlockedMark();
      return;
    }

    if (isStoreBlockedMarked()) {
      redirectIfBlocked(urlSlug);
      return;
    }

    fetchingRef.current = true;
    try {
      const redirected = await checkInfoPublicaBlocked(urlSlug);
      if (redirected) return;

      const { data } = await apiClient.get('/superadmin/lojas/heartbeat/', {
        params: { slug: urlSlug },
      });

      if (data?.is_blocked) {
        redirectIfBlocked(urlSlug);
        return;
      }

      clearStoreBlockedMark();

      const avisoHb = data?.assinatura_aviso as AssinaturaAviso | null | undefined;
      if (avisoHb?.mensagem) {
        applyAviso(avisoHb);
        return;
      }

      await fetchViaFinanceiro(urlSlug);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 429) return;
      const redirected = await checkInfoPublicaBlocked(urlSlug);
      if (!redirected) {
        await fetchViaFinanceiro(urlSlug);
      }
    } finally {
      fetchingRef.current = false;
    }
  }, [slug, applyAviso, fetchViaFinanceiro, checkInfoPublicaBlocked, redirectIfBlocked]);

  useEffect(() => {
    if (!slug?.trim()) return;
    if (LOGIN_PATH_RE.test(pathname) || pathname === TROCAR_SENHA_PATH) return;

    if (isAssinaturaPath(pathname)) {
      clearStoreBlockedMark();
      return;
    }

    if (isStoreBlockedMarked()) {
      redirectToAssinatura(slug.trim());
      return;
    }

    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;

    const run = async () => {
      if (cancelled) return;
      if (!hasLojaSession() || authService.getUserType() !== 'loja') {
        if (attempt < 20) {
          attempt += 1;
          retryTimer = setTimeout(run, 500);
        }
        return;
      }
      await fetchStatus();
    };

    void run();

    const onVisible = () => {
      if (!document.hidden && !isAssinaturaPath(pathnameRef.current)) {
        void fetchStatus();
      }
    };
    document.addEventListener('visibilitychange', onVisible);

    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [slug, pathname, fetchStatus]);

  const avisoVisivel = Boolean(aviso?.mensagem);

  return { aviso, avisoVisivel };
}
