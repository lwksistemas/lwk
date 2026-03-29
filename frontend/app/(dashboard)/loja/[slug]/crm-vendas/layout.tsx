'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import { clearOrphanStorageForSlug } from '@/lib/storage-cleanup';
import SidebarCrm from '@/components/crm-vendas/SidebarCrm';
import HeaderCrm from '@/components/crm-vendas/HeaderCrm';
import { CRMConfigProvider } from '@/contexts/CRMConfigContext';

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
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<'vendedor' | 'administrador'>('administrador');

  /** Busca vendedor_id e nome do usuário (para menu: Nayara vs Felix). */
  const fetchCrmMe = useCallback(async () => {
    try {
      const r = await apiClient.get<{
        vendedor_id: number | null;
        is_vendedor: boolean;
        user_display_name?: string | null;
        user_role?: 'vendedor' | 'administrador';
      }>('/crm-vendas/me/');
      const d = r.data;
      // IMPORTANTE: Só setar is_vendedor se o BACKEND explicitamente disser que é vendedor
      // Owner pode ter vendedor_id mas is_vendedor=false (acesso total)
      if (typeof window !== 'undefined') {
        if (d?.is_vendedor === true && typeof d?.vendedor_id === 'number') {
          sessionStorage.setItem('is_vendedor', '1');
          sessionStorage.setItem('current_vendedor_id', String(d.vendedor_id));
        } else if (typeof d?.vendedor_id === 'number') {
          // Tem vendedor_id mas não é vendedor (owner) - só salva o ID
          sessionStorage.setItem('current_vendedor_id', String(d.vendedor_id));
          // NÃO seta is_vendedor - owner mantém acesso total
        }
      }
      setUserDisplayName(d?.user_display_name ?? null);
      setUserRole(d?.user_role === 'vendedor' ? 'vendedor' : 'administrador');
    } catch {
      /* ignore - vendedor_id permanece do login ou vazio */
    }
  }, []);

  const fetchLojaInfo = useCallback(async () => {
    const cached = getCachedLojaInfo(slug);
    if (cached) {
      setLojaInfo(cached);
      if (cached.id) {
        sessionStorage.setItem('current_loja_id', String(cached.id));
        if (cached.slug) sessionStorage.setItem('loja_slug', cached.slug);
      }
      await fetchCrmMe();
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
      await fetchCrmMe();
    } catch (err: unknown) {
      setLojaInfo(null);
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 404) clearOrphanStorageForSlug(slug);
    }
  }, [slug, fetchCrmMe]);

  // Garantir loja_slug ANTES de qualquer requisição (evita lista vazia em produtos-serviços).
  // Se o usuário trocou de loja na URL mas o sessionStorage ainda tem ID da loja anterior,
  // X-Loja-ID quebrava o tenant em produção (JWT valida o header antes do slug).
  if (typeof window !== 'undefined' && slug) {
    const prev = sessionStorage.getItem('loja_slug');
    if (prev && prev !== slug) {
      sessionStorage.removeItem('current_loja_id');
    }
    sessionStorage.setItem('loja_slug', slug);
  }

  useEffect(() => {
    if (!ready || !isLoja) return;
    fetchLojaInfo();
  }, [ready, isLoja, fetchLojaInfo, slug]);

  useEffect(() => {
    if (ready && !isLoja) window.location.href = loginPath;
  }, [ready, isLoja, loginPath]);

  if (!ready || !isLoja) return null;

  return (
    <CRMConfigProvider>
      <div className="flex min-h-screen bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <SidebarCrm lojaNome={lojaInfo?.nome} onLogout={handleLogout} />
        <div className="flex-1 flex flex-col min-w-0">
          <HeaderCrm
            title={lojaInfo ? `${lojaInfo.nome}` : 'Sales Cloud'}
            userName={userDisplayName ?? lojaInfo?.nome ?? 'Admin'}
            userRole={userRole}
            slug={slug}
          />
          <main className="p-4 sm:p-6 lg:p-8 flex-1 min-h-0 overflow-y-auto bg-[#f3f2f2] dark:bg-[#0d1f3c]">
            {children}
          </main>
        </div>
      </div>
    </CRMConfigProvider>
  );
}
