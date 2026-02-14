'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import RouteGuard from '@/components/RouteGuard';
import { useSessionMonitor } from '@/hooks/useSessionMonitor';
import { registrarSincronizacaoAoVoltarOnline } from '@/lib/offline-sync';

const PWA_LOJA_SLUG_KEY = 'pwa_loja_slug';

export default function LojaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const slug = params.slug as string;

  // Monitorar sessão em tempo real
  useSessionMonitor();

  // Modo offline: ao voltar online, sincronizar fila de agendamentos (e demais itens) pendentes
  useEffect(() => {
    registrarSincronizacaoAoVoltarOnline();
  }, []);

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
