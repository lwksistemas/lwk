'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { resolveLojaApiSlug } from '@/lib/resolve-loja-slug';
import {
  calcularAvisoAssinaturaLocal,
  type AssinaturaAviso,
} from '@/lib/assinatura-aviso';

const ASSINATURA_PATH_RE = /\/assinatura\/?$/;
const LOGIN_PATH_RE = /\/login\/?$/;
const TROCAR_SENHA_PATH = '/loja/trocar-senha';

export type { AssinaturaAviso };

function hasLojaSession(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(sessionStorage.getItem('session_id') || sessionStorage.getItem('access_token'));
}

/**
 * Bloqueio por inadimplência + aviso de vencimento (5 dias antes).
 * O aviso permanece visível em todas as páginas enquanto houver pendência (sem botão fechar).
 */
export function useLojaInadimplenciaGuard(slug: string) {
  const router = useRouter();
  const pathname = usePathname();
  const [aviso, setAviso] = useState<AssinaturaAviso | null>(null);
  const fetchingRef = useRef(false);

  const applyAviso = useCallback((avisoData: AssinaturaAviso | null | undefined) => {
    if (avisoData?.mensagem) {
      setAviso(avisoData);
    } else {
      setAviso(null);
    }
  }, []);

  const fetchViaFinanceiro = useCallback(async (urlSlug: string): Promise<boolean> => {
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

    fetchingRef.current = true;
    try {
      const { data } = await apiClient.get('/superadmin/lojas/heartbeat/', {
        params: { slug: slug.trim() },
      });

      if (data?.is_blocked) {
        setAviso(null);
        const target = `/loja/${slug}/assinatura`;
        if (!ASSINATURA_PATH_RE.test(pathname) && !pathname.startsWith(target)) {
          router.replace(target);
        }
        return;
      }

      const avisoHb = data?.assinatura_aviso as AssinaturaAviso | null | undefined;
      if (avisoHb?.mensagem) {
        applyAviso(avisoHb);
        return;
      }

      await fetchViaFinanceiro(slug.trim());
    } catch {
      await fetchViaFinanceiro(slug.trim());
    } finally {
      fetchingRef.current = false;
    }
  }, [slug, pathname, router, applyAviso, fetchViaFinanceiro]);

  useEffect(() => {
    if (!slug?.trim()) return;
    if (LOGIN_PATH_RE.test(pathname) || pathname === TROCAR_SENHA_PATH) return;

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
      if (!document.hidden) void fetchStatus();
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
