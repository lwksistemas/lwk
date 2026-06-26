'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import { ClinicaBelezaShell } from '@/components/clinica-beleza/ClinicaBelezaShell';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import type { LojaInfo } from '@/types/dashboard';

export default function AgendaLayout({ children }: { children: React.ReactNode }) {
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
    loadLoja();
  }, [ready, isLoja, loadLoja]);

  useEffect(() => {
    if (ready && !isLoja) window.location.href = loginPath;
  }, [ready, isLoja, loginPath]);

  if (!ready || !isLoja || !loja) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8f9fa] dark:bg-gray-950">
        <div className="text-center">
          <div
            className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: `${CLINICA_BELEZA_PRIMARY} transparent transparent transparent` }}
          />
          <p className="text-sm text-gray-600 dark:text-gray-300">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <ClinicaBelezaShell
      loja={loja}
      onLogout={handleLogout}
      mainClassName="overflow-hidden !overflow-y-hidden flex flex-col"
    >
      {children}
    </ClinicaBelezaShell>
  );
}
