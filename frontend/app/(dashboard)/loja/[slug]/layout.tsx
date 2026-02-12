'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import RouteGuard from '@/components/RouteGuard';

const PWA_LOJA_SLUG_KEY = 'pwa_loja_slug';

export default function LojaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const slug = params.slug as string;

  // Persistir slug para PWA: ao abrir o app instalado, redirecionar para login da loja
  useEffect(() => {
    if (slug?.trim()) {
      localStorage.setItem(PWA_LOJA_SLUG_KEY, slug.trim());
    }
  }, [slug]);
  
  return (
    <RouteGuard allowedUserType="loja" requiredSlug={slug}>
      {children}
    </RouteGuard>
  );
}
