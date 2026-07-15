'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useParams } from 'next/navigation';
import { Parisienne } from 'next/font/google';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import type { LojaInfo } from '@/types/dashboard';
import { SalaoShell } from './SalaoShell';

const scriptFont = Parisienne({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-salao-script',
  display: 'swap',
});

export function SalaoLojaLayout({ children }: { children: ReactNode }) {
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
        // Preferir o slug/atalho da URL (ex.: luminademo) para o middleware não bloquear o menu.
        sessionStorage.setItem('loja_slug', slug);
        document.cookie = `loja_slug=${encodeURIComponent(slug)}; path=/; max-age=86400; SameSite=Lax`;
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

  if (!ready || !isLoja || !loja) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F7F0F3]">
        <p className="text-sm text-gray-500">Carregando salão...</p>
      </div>
    );
  }

  return (
    <div className={scriptFont.variable}>
      <SalaoShell loja={loja} onLogout={handleLogout}>
        {children}
      </SalaoShell>
    </div>
  );
}
