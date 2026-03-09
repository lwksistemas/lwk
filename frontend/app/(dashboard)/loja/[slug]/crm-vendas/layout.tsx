'use client';

import { useEffect, useState } from 'react';
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

export default function CrmVendasLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const slug = params.slug as string;
  const { loginPath, handleLogout, isLoja, ready } = useLojaAuth(slug);
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);

  useEffect(() => {
    if (!ready || !isLoja) return;
    apiClient
      .get(`/superadmin/lojas/info_publica/?slug=${slug}`)
      .then((r) => setLojaInfo(r.data))
      .catch(() => setLojaInfo(null));
  }, [ready, isLoja, slug]);

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
        />
        <main className="p-4 sm:p-6 lg:p-8 flex-1 min-h-0 overflow-y-auto bg-[#f3f2f2] dark:bg-[#0d1f3c]">
          {children}
        </main>
      </div>
    </div>
  );
}
