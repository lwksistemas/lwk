'use client';

import { useEffect } from 'react';
import { useParams, usePathname } from 'next/navigation';
import apiClient from '@/lib/api-client';

/** Obtém loja_slug no momento do envio: params, sessionStorage ou pathname. */
function getLojaSlugAtSendTime(): string {
  if (typeof window === 'undefined') return '';
  const fromSession = sessionStorage.getItem('loja_slug');
  if (fromSession?.trim()) return fromSession.trim();
  const match = window.location.pathname.match(/^\/loja\/([^/]+)(\/|$)/);
  if (match?.[1]) return match[1];
  return '';
}

/**
 * Captura erros do navegador (window.onerror, unhandledrejection) e envia
 * para o backend por loja. Usado no painel "Detalhes" do suporte.
 * Só envia quando há erro; loja_slug é obtido na hora (params, session ou URL).
 */
export default function CapturaErrosNavegador() {
  const params = useParams();
  const pathname = usePathname();
  const slugFromParams = (params?.slug as string) || '';

  useEffect(() => {
    if (typeof window === 'undefined') return;
    // Só capturar quando estiver em uma rota de loja (/loja/[slug]/...)
    if (!pathname?.startsWith('/loja/')) return;

    const enviar = (mensagem: string, stack?: string, url?: string) => {
      if (!mensagem?.trim()) return;
      const lojaSlug = slugFromParams.trim() || getLojaSlugAtSendTime();
      if (!lojaSlug) return; // evita enviar como "sistema" quando estamos numa loja
      const payload = {
        mensagem: mensagem.slice(0, 500),
        stack: (stack || '').slice(0, 5000),
        url: (url || window.location?.href || '').slice(0, 500),
        loja_slug: lojaSlug,
      };
      apiClient.post('/suporte/registrar-erro-frontend/', payload).catch(() => {});
    };

    const onError = (event: ErrorEvent) => {
      const msg = event.message || String(event.error);
      const stack = event.error?.stack;
      enviar(msg, stack, window.location?.href);
    };

    const onRejection = (event: PromiseRejectionEvent) => {
      const msg = event.reason?.message || String(event.reason);
      const stack = event.reason?.stack;
      enviar(msg, stack, window.location?.href);
    };

    window.addEventListener('error', onError);
    window.addEventListener('unhandledrejection', onRejection);
    return () => {
      window.removeEventListener('error', onError);
      window.removeEventListener('unhandledrejection', onRejection);
    };
  }, [pathname, slugFromParams]);

  return null;
}
