'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import { ClinicaBelezaShell } from '@/components/clinica-beleza/clinica-beleza-shell/ClinicaBelezaShell';
import { ClinicaBelezaThemeProvider } from '@/components/clinica-beleza/ClinicaBelezaThemeContext';
import type { LojaInfo } from '@/types/dashboard';

type ClinicaBelezaLojaLayoutProps = {
  children: ReactNode;
  /** Classes extras no <main> do shell (ex.: agenda fullscreen). */
  mainClassName?: string;
  /** Spinner com cor da marca (agenda) vs texto simples. */
  loadingVariant?: 'default' | 'branded';
};

function lojaInfoCacheKey(slug: string) {
  return `cb_loja_info_${(slug || '').trim().toLowerCase()}`;
}

function readCachedLojaInfo(slug: string): LojaInfo | null {
  if (typeof window === 'undefined' || !slug) return null;
  try {
    const raw = sessionStorage.getItem(lojaInfoCacheKey(slug));
    if (!raw) return null;
    const data = JSON.parse(raw) as LojaInfo;
    return data?.id ? data : null;
  } catch {
    return null;
  }
}

function writeCachedLojaInfo(urlSlug: string, data: LojaInfo) {
  if (typeof window === 'undefined' || !data?.id) return;
  const payload = JSON.stringify(data);
  const keys = new Set<string>([
    urlSlug,
    data.slug || '',
    data.atalho || '',
  ].map((s) => s.trim().toLowerCase()).filter(Boolean));
  for (const key of keys) {
    sessionStorage.setItem(lojaInfoCacheKey(key), payload);
  }
  sessionStorage.setItem('current_loja_id', String(data.id));
  if (data.slug) sessionStorage.setItem('loja_slug', data.slug);
}

function LoadingScreen({ variant }: { variant: 'default' | 'branded' }) {
  if (variant === 'branded') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8f9fa] dark:bg-gray-950">
        <div className="text-center">
          <div
            className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: 'var(--cb-primary, #8B3D52) transparent transparent transparent' }}
          />
          <p className="text-sm text-gray-600 dark:text-gray-300">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <p className="text-gray-500">Carregando...</p>
    </div>
  );
}

/** Layout compartilhado: auth loja + info_publica + ClinicaBelezaShell. */
export function ClinicaBelezaLojaLayout({
  children,
  mainClassName,
  loadingVariant = 'default',
}: ClinicaBelezaLojaLayoutProps) {
  const params = useParams();
  const slug = params.slug as string;
  const { loginPath, handleLogout, isLoja, ready } = useLojaAuth(slug);
  const [loja, setLoja] = useState<LojaInfo | null>(() => readCachedLojaInfo(slug));
  const [lojaLoading, setLojaLoading] = useState(() => !readCachedLojaInfo(slug));
  const [lojaError, setLojaError] = useState<string | null>(null);

  const loadLoja = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = Boolean(opts?.silent && readCachedLojaInfo(slug));
    if (!silent) {
      setLojaLoading(true);
      setLojaError(null);
    }
    try {
      const res = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`);
      const data = res.data as LojaInfo;
      if (!data?.id) {
        if (!silent) {
          setLoja(null);
          setLojaError('Não foi possível carregar os dados da loja.');
        }
        return;
      }
      setLoja(data);
      writeCachedLojaInfo(slug, data);
      setLojaError(null);
    } catch {
      if (!silent) {
        setLoja(null);
        setLojaError('Falha ao carregar o módulo. Verifique a conexão e tente novamente.');
      }
    } finally {
      if (!silent) setLojaLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    if (!ready || !isLoja) return;
    const cached = readCachedLojaInfo(slug);
    if (cached) {
      setLoja(cached);
      setLojaLoading(false);
      void loadLoja({ silent: true });
      return;
    }
    void loadLoja();
  }, [ready, isLoja, loadLoja, slug]);

  useEffect(() => {
    if (ready && !isLoja) window.location.href = loginPath;
  }, [ready, isLoja, loginPath]);

  if (!ready || !isLoja) {
    return <LoadingScreen variant={loadingVariant} />;
  }

  if (lojaLoading && !loja) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <p className="text-gray-500">Carregando módulo...</p>
      </div>
    );
  }

  if (!loja) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3 bg-gray-50 dark:bg-gray-900 px-4">
        <p className="text-sm text-red-600 dark:text-red-400 text-center max-w-md">
          {lojaError || 'Não foi possível carregar o módulo da clínica.'}
        </p>
        <button
          type="button"
          onClick={() => void loadLoja()}
          className="px-4 py-2 rounded-lg text-sm font-medium text-white"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <ClinicaBelezaThemeProvider
      corPrimaria={loja.cor_primaria}
      corSecundaria={loja.cor_secundaria}
      corFundoPagina={loja.cor_fundo_pagina}
      agendaStatusColors={loja.agenda_status_colors}
    >
      <ClinicaBelezaShell loja={loja} onLogout={handleLogout} mainClassName={mainClassName}>
        {children}
      </ClinicaBelezaShell>
    </ClinicaBelezaThemeProvider>
  );
}
