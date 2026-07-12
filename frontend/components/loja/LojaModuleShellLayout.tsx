'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { ClinicaBelezaShell } from '@/components/clinica-beleza/clinica-beleza-shell/ClinicaBelezaShell';
import { ClinicaBelezaThemeProvider } from '@/components/clinica-beleza/ClinicaBelezaThemeContext';
import { CrmVendasShell } from '@/components/crm-vendas/CrmVendasShell';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import { isTipoClinicaBeleza, isTipoCRMVendas } from '@/lib/loja-tipo';
import type { LojaInfo } from '@/types/dashboard';

function LoadingScreen({ bg = '#f7f2f4' }: { bg?: string }) {
  return (
    <div
      className="min-h-screen flex items-center justify-center dark:bg-gray-950"
      style={{ backgroundColor: bg }}
    >
      <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
    </div>
  );
}

/** Shell com sidebar para páginas compartilhadas fora de `/clinica-beleza/*` (suporte, WhatsApp). */
export function LojaModuleShellLayout({ children }: { children: ReactNode }) {
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

  if (!ready || !isLoja || !loja) return <LoadingScreen />;

  const tipoNome = loja.tipo_loja_nome || '';

  if (isTipoClinicaBeleza(tipoNome)) {
    return (
      <ClinicaBelezaThemeProvider
        corPrimaria={loja.cor_primaria}
        corSecundaria={loja.cor_secundaria}
        corFundoPagina={loja.cor_fundo_pagina}
        agendaStatusColors={loja.agenda_status_colors}
      >
        <ClinicaBelezaShell loja={loja} onLogout={handleLogout}>
          {children}
        </ClinicaBelezaShell>
      </ClinicaBelezaThemeProvider>
    );
  }

  if (isTipoCRMVendas(tipoNome)) {
    return <CrmVendasShell>{children}</CrmVendasShell>;
  }

  return <>{children}</>;
}
