'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

const ASSINATURA_PATH_RE = /\/assinatura\/?$/;
const LOGIN_PATH_RE = /\/login\/?$/;
const TROCAR_SENHA_PATH = '/loja/trocar-senha';

export type AssinaturaAviso = {
  nivel: 'aviso' | 'urgente' | 'critico';
  mensagem: string;
  dias_restantes?: number;
  dias_atraso?: number;
  dias_ate_bloqueio?: number;
  data_vencimento?: string;
};

function dismissKey(slug: string) {
  const hoje = new Date().toISOString().slice(0, 10);
  return `lwk_aviso_assinatura_${slug}_${hoje}`;
}

function isDismissedToday(slug: string) {
  if (typeof window === 'undefined') return false;
  return sessionStorage.getItem(dismissKey(slug)) === '1';
}

/**
 * Bloqueio por inadimplência + aviso de vencimento (5 dias antes).
 */
export function useLojaInadimplenciaGuard(slug: string) {
  const router = useRouter();
  const pathname = usePathname();
  const checkedRef = useRef('');
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
    if (authService.getUserType() !== 'loja') return;
    if (LOGIN_PATH_RE.test(pathname) || pathname === TROCAR_SENHA_PATH) {
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
          setAviso(null);
          setAvisoVisivel(false);
          const target = `/loja/${slug}/assinatura`;
          if (!ASSINATURA_PATH_RE.test(pathname) && !pathname.startsWith(target)) {
            router.replace(target);
          }
          return;
        }

        const avisoData = data?.assinatura_aviso as AssinaturaAviso | null | undefined;
        if (avisoData?.mensagem) {
          setAviso(avisoData);
          setAvisoVisivel(!isDismissedToday(slug));
        } else {
          setAviso(null);
          setAvisoVisivel(false);
        }
      } catch {
        /* heartbeat falhou: middleware/API retorna 403 em rotas bloqueadas */
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [slug, pathname, router]);

  return { aviso, avisoVisivel, dismissAviso };
}
