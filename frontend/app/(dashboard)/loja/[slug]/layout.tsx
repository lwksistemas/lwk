'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import RouteGuard from '@/components/RouteGuard';
import { useSessionMonitor } from '@/hooks/useSessionMonitor';
import { useInactivityLogout } from '@/hooks/useInactivityLogout';
import { registrarSincronizacaoAoVoltarOnline } from '@/lib/offline-sync';
import CapturaErrosNavegador from '@/components/suporte/CapturaErrosNavegador';
import { authService, syncLojaTenantSlug } from '@/lib/auth';
import { useLojaInadimplenciaGuard } from '@/hooks/useLojaInadimplenciaGuard';
import {
  LojaAssinaturaAvisoBanner,
  LojaAssinaturaAvisoSpacer,
} from '@/components/loja/LojaAssinaturaAvisoBanner';

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
  useInactivityLogout();
  const { aviso, avisoVisivel, lojaSlugCanonico } = useLojaInadimplenciaGuard(slug);
  const bannerSlug = lojaSlugCanonico || slug;

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

  // Manter cookie/session alinhados com a URL (evita middleware bloquear cliques no menu)
  useEffect(() => {
    if (!slug?.trim()) return;
    if (authService.getUserType() === 'loja') {
      syncLojaTenantSlug(slug.trim());
    }
  }, [slug]);

  // Atualizar título da página com nome da loja (para PWA mostrar nome correto na barra)
  useEffect(() => {
    if (!slug?.trim()) return;
    const cached = sessionStorage.getItem(`loja_nome_${slug}`);
    if (cached) {
      document.title = cached;
      return;
    }
    // Buscar nome da loja
    import('@/lib/api-client').then(({ default: apiClient }) => {
      apiClient.get(`/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`)
        .then((res) => {
          const data = res.data as { nome?: string; id?: number; slug?: string };
          if (data?.nome) {
            document.title = data.nome;
            sessionStorage.setItem(`loja_nome_${slug}`, data.nome);
          }
          if (data?.id) {
            sessionStorage.setItem('current_loja_id', String(data.id));
          }
          if (data?.slug) {
            sessionStorage.setItem('loja_slug', data.slug);
          }
        })
        .catch(() => {});
    });
    return () => {
      document.title = 'LWK Sistemas - Gestão de Lojas';
    };
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
      <LojaAssinaturaAvisoBanner slug={bannerSlug} aviso={aviso} visivel={avisoVisivel} />
      <LojaAssinaturaAvisoSpacer visivel={avisoVisivel} />
      {children}
    </RouteGuard>
  );
}
