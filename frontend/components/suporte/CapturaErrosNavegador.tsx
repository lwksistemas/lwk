'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';

/**
 * Captura erros do navegador (window.onerror, unhandledrejection) e envia
 * para o backend por loja (sessão única). Usado no painel "Detalhes" do suporte.
 * Não sobrecarrega: só envia quando ocorre um erro.
 */
export default function CapturaErrosNavegador() {
  const params = useParams();
  const slug = (params?.slug as string) || '';

  useEffect(() => {
    if (typeof window === 'undefined' || !slug) return;

    const lojaSlug = slug || (typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('loja_slug') : null) || '';

    const enviar = (mensagem: string, stack?: string, url?: string) => {
      if (!mensagem) return;
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
  }, [slug]);

  return null;
}
