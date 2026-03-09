'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import SidebarCrm from '@/components/crm-vendas/SidebarCrm';
import HeaderCrm from '@/components/crm-vendas/HeaderCrm';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
}

const CACHE_KEY = 'crm_loja_info';
const CACHE_TTL_MS = 2 * 60 * 1000; // 2 min

function getCachedLojaInfo(slug: string): LojaInfo | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = sessionStorage.getItem(`${CACHE_KEY}:${slug}`);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL_MS) return null;
    return data;
  } catch {
    return null;
  }
}

function setCachedLojaInfo(slug: string, data: LojaInfo) {
  if (typeof window === 'undefined') return;
  try {
    sessionStorage.setItem(`${CACHE_KEY}:${slug}`, JSON.stringify({ data, ts: Date.now() }));
  } catch {
    /* ignore */
  }
}

export default function CrmVendasLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const slug = params.slug as string;
  const { loginPath, handleLogout, isLoja, ready } = useLojaAuth(slug);
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(() => getCachedLojaInfo(slug));

  const fetchLojaInfo = useCallback(async () => {
    const cached = getCachedLojaInfo(slug);
    if (cached) {
      setLojaInfo(cached);
      if (cached.id) {
        sessionStorage.setItem('current_loja_id', String(cached.id));
        if (cached.slug) sessionStorage.setItem('loja_slug', cached.slug);
      }
      return;
    }
    try {
      const r = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      const data = r.data as LojaInfo;
      setLojaInfo(data);
      setCachedLojaInfo(slug, data);
      if (typeof window !== 'undefined' && data?.id) {
        sessionStorage.setItem('current_loja_id', String(data.id));
        if (data?.slug) sessionStorage.setItem('loja_slug', data.slug);
        document.cookie = 'loja_usa_crm=1; path=/; max-age=86400; SameSite=Lax';
      }
    } catch {
      setLojaInfo(null);
    }
  }, [slug]);

  useEffect(() => {
    if (!ready || !isLoja) return;
    if (typeof window !== 'undefined' && slug) {
      sessionStorage.setItem('loja_slug', slug);
    }
    fetchLojaInfo();
  }, [ready, isLoja, fetchLojaInfo, slug]);

  useEffect(() => {
    if (ready && !isLoja) window.location.href = loginPath;
  }, [ready, isLoja, loginPath]);

  if (!ready || !isLoja) return null;

  return (
    <div className="flex min-h-screen bg-[#f3f2f2] dark:bg-[#0d1f3c]">
      <SidebarCrm lojaNome={lojaInfo?.nome} onLogout={handleLogout} />
      <div className="flex-1 flex flex-col min-w-0">
        <HeaderCrm
          title={lojaInfo ? `${lojaInfo.nome}` : 'Sales Cloud'}
          userName={lojaInfo?.nome ?? 'Admin'}
          slug={slug}
        />
        <main className="p-4 sm:p-6 lg:p-8 flex-1 min-h-0 overflow-y-auto bg-[#f3f2f2] dark:bg-[#0d1f3c]">
          {children}
        </main>
      </div>
    </div>
  );
}
