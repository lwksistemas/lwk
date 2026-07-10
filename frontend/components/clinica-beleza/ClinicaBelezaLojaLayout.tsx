'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import { ClinicaBelezaShell } from '@/components/clinica-beleza/ClinicaBelezaShell';
import { ClinicaBelezaThemeProvider } from '@/components/clinica-beleza/ClinicaBelezaThemeContext';
import type { LojaInfo } from '@/types/dashboard';

type ClinicaBelezaLojaLayoutProps = {
  children: ReactNode;
  /** Classes extras no <main> do shell (ex.: agenda fullscreen). */
  mainClassName?: string;
  /** Spinner com cor da marca (agenda) vs texto simples. */
  loadingVariant?: 'default' | 'branded';
};

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
  const [loja, setLoja] = useState<LojaInfo | null>(null);

  const loadLoja = useCallback(async () => {
    try {
      const res = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      const data = res.data as LojaInfo;
      setLoja(data);
      if (typeof window !== 'undefined' && data?.id) {
        sessionStorage.setItem('current_loja_id', String(data.id));
        if (data.slug) sessionStorage.setItem('loja_slug', data.slug);
      }
    } catch {
      setLoja(null);
    }
  }, [slug]);

  useEffect(() => {
    if (!ready || !isLoja) return;
    void loadLoja();
  }, [ready, isLoja, loadLoja]);

  useEffect(() => {
    if (ready && !isLoja) window.location.href = loginPath;
  }, [ready, isLoja, loginPath]);

  if (!ready || !isLoja) {
    return <LoadingScreen variant={loadingVariant} />;
  }

  if (!loja) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <p className="text-gray-500">Carregando módulo...</p>
      </div>
    );
  }

  return (
    <ClinicaBelezaThemeProvider
      corPrimaria={loja.cor_primaria}
      corSecundaria={loja.cor_secundaria}
      agendaStatusColors={loja.agenda_status_colors}
    >
      <ClinicaBelezaShell loja={loja} onLogout={handleLogout} mainClassName={mainClassName}>
        {children}
      </ClinicaBelezaShell>
    </ClinicaBelezaThemeProvider>
  );
}
