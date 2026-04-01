'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
}

export default function ClinicaEsteticaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const slug = params.slug as string;
  const { loginPath, isLoja, ready } = useLojaAuth(slug);
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);

  const fetchLojaInfo = useCallback(async () => {
    try {
      const r = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      const data = r.data as LojaInfo;
      setLojaInfo(data);
      if (typeof window !== 'undefined' && data?.id) {
        sessionStorage.setItem('current_loja_id', String(data.id));
        if (data?.slug) sessionStorage.setItem('loja_slug', data.slug);
      }
    } catch (err) {
      setLojaInfo(null);
    }
  }, [slug]);

  useEffect(() => {
    if (!ready || !isLoja) return;
    fetchLojaInfo();
  }, [ready, isLoja, fetchLojaInfo]);

  useEffect(() => {
    if (ready && !isLoja) window.location.href = loginPath;
  }, [ready, isLoja, loginPath]);

  if (!ready || !isLoja) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {children}
    </div>
  );
}
