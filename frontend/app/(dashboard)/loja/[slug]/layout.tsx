'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import RouteGuard from '@/components/RouteGuard';
import { useSessionMonitor } from '@/hooks/useSessionMonitor';
import { registrarSincronizacaoAoVoltarOnline } from '@/lib/offline-sync';
import { resetToPrimaryAPI } from '@/lib/api-client';
import CapturaErrosNavegador from '@/components/suporte/CapturaErrosNavegador';

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

  // Lojas sempre usam Heroku; ao entrar em rota de loja, forçar servidor principal
  useEffect(() => {
    resetToPrimaryAPI();
  }, []);

  // Modo offline: ao voltar online, sincronizar fila de agendamentos (e demais itens) pendentes
  useEffect(() => {
    registrarSincronizacaoAoVoltarOnline();
  }, []);

  // Respeitar servidor selecionado (Heroku ou Render); não forçar Heroku — Render usa o mesmo banco.
  // Persistir slug para PWA: ao abrir o app instalado, redirecionar para login da loja
  useEffect(() => {
    if (slug?.trim()) {
      localStorage.setItem(PWA_LOJA_SLUG_KEY, slug.trim());
    }
  }, [slug]);

  // Usar manifest da loja nas páginas /loja/[slug] para que "Adicionar à tela de início" no iPhone/Android
  // instale um app que abre direto no login desta loja
  useEffect(() => {
    if (!slug?.trim()) return;
    const manifestUrl = `/api/manifest/loja?slug=${encodeURIComponent(slug.trim())}`;
    let link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]');
    if (!link) {
      link = document.createElement('link');
      link.rel = 'manifest';
      document.head.appendChild(link);
    }
    if (link.getAttribute('href') !== manifestUrl) {
      link.setAttribute('href', manifestUrl);
    }
    return () => {
      // Ao sair da loja, restaurar manifest padrão
      link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]');
      if (link) link.setAttribute('href', '/manifest.json');
    };
  }, [slug]);
  
  return (
    <RouteGuard allowedUserType="loja" requiredSlug={slug}>
      <CapturaErrosNavegador />
      {children}
    </RouteGuard>
  );
}
