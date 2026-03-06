'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import { isTipoClinicaEstetica, isTipoClinicaBeleza, isTipoRestaurante, isTipoCabeleireiro, isTipoCommerce, isTipoServicos } from '@/lib/loja-tipo';
import ModalChamado from '@/components/suporte/ModalChamado';
import BackupButton from '@/components/loja/BackupButton';

const DashboardChunkSkeleton = () => (
  <div className="flex flex-col items-center justify-center min-h-[200px] gap-3 p-6">
    <div className="h-8 w-8 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" aria-hidden />
    <p className="text-sm text-gray-500 dark:text-gray-400">Carregando dashboard...</p>
  </div>
);

const DashboardClinicaEstetica = dynamic(() => import('./templates/clinica-estetica'), { loading: DashboardChunkSkeleton });
const DashboardClinicaBeleza = dynamic(() => import('./templates/clinica-beleza'), { loading: DashboardChunkSkeleton });
const DashboardRestaurante = dynamic(() => import('./templates/restaurante'), { loading: DashboardChunkSkeleton });
const DashboardServicos = dynamic(() => import('./templates/servicos'), { loading: DashboardChunkSkeleton });
const DashboardCabeleireiro = dynamic(() => import('./templates/dashboard-cabeleireiro-novo'), { loading: DashboardChunkSkeleton });

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
  senha_foi_alterada: boolean;
}

export default function LojaDashboardDinamicoPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;
  const { loginPath, handleLogout, isLoja, ready } = useLojaAuth(slug);

  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingLento, setLoadingLento] = useState(false);
  const [modalSuporteAberto, setModalSuporteAberto] = useState(false);
  const [chamadosDropdownAberto, setChamadosDropdownAberto] = useState(false);
  const chamadosDropdownRef = useRef<HTMLDivElement>(null);

  // Forçar reload se vier de cache (bfcache)
  useEffect(() => {
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) window.location.reload();
    };
    window.addEventListener('pageshow', handlePageShow);
    return () => window.removeEventListener('pageshow', handlePageShow);
  }, []);

  const verificarECarregarLoja = useCallback(async () => {
    try {
      setLoading(true);
      const lojaResponse = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      const data = lojaResponse.data;
      if (data?.id && typeof window !== 'undefined') {
        sessionStorage.setItem('current_loja_id', String(data.id));
        if (data.slug) sessionStorage.setItem('loja_slug', data.slug);
      }
      setLojaInfo(data);
    } catch (error: unknown) {
      console.error('Erro ao carregar loja:', error);
      const ax = error && typeof error === 'object' && 'response' in error ? (error as { response?: { status?: number } }).response : undefined;
      if (ax?.status === 401) router.push(`/loja/${slug}/login`);
    } finally {
      setLoading(false);
    }
  }, [slug, router]);

  useEffect(() => {
    if (!ready || !isLoja) return;
    verificarECarregarLoja();
  }, [ready, isLoja, slug, verificarECarregarLoja]);

  useEffect(() => {
    if (ready && !isLoja) router.push(loginPath);
  }, [ready, isLoja, loginPath, router]);

  // Fechar dropdown Chamados ao clicar fora
  useEffect(() => {
    if (!chamadosDropdownAberto) return;
    const handleClick = (e: MouseEvent) => {
      if (chamadosDropdownRef.current && !chamadosDropdownRef.current.contains(e.target as Node)) {
        setChamadosDropdownAberto(false);
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [chamadosDropdownAberto]);

  // Mostrar dica se o carregamento passar de 8s (ex.: cold start Heroku)
  useEffect(() => {
    if (!loading) return;
    const t = setTimeout(() => setLoadingLento(true), 8000);
    return () => clearTimeout(t);
  }, [loading]);

  if (ready && !isLoja) return null;

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 p-4 gap-4">
        <div className="text-lg sm:text-xl text-gray-600 dark:text-gray-400 text-center">
          Carregando o dashboard...
        </div>
        <div className="h-8 w-8 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" aria-hidden />
        {loadingLento && (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center max-w-xs mt-2">
            Está demorando? O servidor pode estar acordando. Aguarde ou atualize a página.
          </p>
        )}
      </div>
    );
  }

  if (!lojaInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
        <div className="text-center">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-4">Erro ao carregar loja</h2>
          <button
            onClick={() => router.push(`/loja/${slug}/login`)}
            className="px-6 py-3 min-h-[44px] bg-blue-600 text-white rounded-md hover:bg-blue-700 active:scale-95 transition-transform"
          >
            Voltar para Login
          </button>
        </div>
      </div>
    );
  }

  const isClinicaEstetica = isTipoClinicaEstetica(lojaInfo.tipo_loja_nome);
  const isClinicaBeleza = isTipoClinicaBeleza(lojaInfo.tipo_loja_nome);
  const isRestaurante = isTipoRestaurante(lojaInfo.tipo_loja_nome);
  const isCabeleireiro = isTipoCabeleireiro(lojaInfo.tipo_loja_nome);
  const isFullWidth = isClinicaEstetica || isClinicaBeleza || isRestaurante || isCabeleireiro;

  // Renderizar dashboard específico por tipo de app
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Para cabeleireiro e clínica da beleza, renderizar SEM header/container (layout próprio) */}
      {(isCabeleireiro || isClinicaBeleza) ? (
        renderDashboardPorTipo(lojaInfo, handleLogout)
      ) : (
        <>
          {/* Header */}
          <nav 
        className="text-white shadow-lg"
        style={{ backgroundColor: lojaInfo.cor_primaria }}
      >
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between min-h-[56px] sm:h-16 py-2 sm:py-0 items-start sm:items-center gap-2 sm:gap-0">
            <div className="w-full sm:w-auto">
              <h1 className="text-lg sm:text-xl md:text-2xl font-bold truncate">{lojaInfo.nome}</h1>
              <p className="text-xs sm:text-sm opacity-90">{lojaInfo.tipo_loja_nome}</p>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
              {isClinicaEstetica ? (
                <>
                  {/* Chamados: dropdown com "Ver chamados" e "Abrir chamado" */}
                  <div className="relative flex-1 sm:flex-none" ref={chamadosDropdownRef}>
                    <button
                      onClick={() => setChamadosDropdownAberto((v) => !v)}
                      className="w-full sm:w-auto px-3 sm:px-4 py-2 min-h-[40px] bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md transition-colors flex items-center justify-center gap-2 text-sm active:scale-95"
                      title="Chamados"
                    >
                      <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                      <span>Chamados</span>
                      <svg className="w-4 h-4 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                    </button>
                    {chamadosDropdownAberto && (
                      <div className="absolute top-full right-0 mt-1 py-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                        <button
                          onClick={() => { setChamadosDropdownAberto(false); router.push(`/loja/${slug}/suporte`); }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                          Ver meus chamados
                        </button>
                        <button
                          onClick={() => { setChamadosDropdownAberto(false); setModalSuporteAberto(true); }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                          Abrir chamado
                        </button>
                      </div>
                    )}
                  </div>
                  {/* Backup (verde) no lugar do antigo Abrir Suporte */}
                  <div className="flex-1 sm:flex-none">
                    <BackupButton lojaId={lojaInfo.id} lojaNome={lojaInfo.nome} className="!min-h-[40px] !px-3 sm:!px-4 !py-2 !rounded-md !bg-green-600 hover:!bg-green-700 !text-white !border-0" />
                  </div>
                </>
              ) : (
                <>
                  <button
                    onClick={() => router.push(`/loja/${slug}/suporte`)}
                    className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md transition-colors flex items-center justify-center gap-2 text-sm active:scale-95"
                    title="Ver meus chamados de suporte"
                  >
                    <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    <span>Chamados</span>
                  </button>
                  <button
                    onClick={() => setModalSuporteAberto(true)}
                    className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-green-600 hover:bg-green-700 rounded-md transition-colors flex items-center justify-center gap-2 text-sm active:scale-95"
                    title="Abrir novo chamado de suporte"
                  >
                    <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    <span className="hidden sm:inline">Abrir Suporte</span>
                    <span className="sm:hidden">Suporte</span>
                  </button>
                </>
              )}
              <button
                onClick={() => {
                  const html = document.documentElement;
                  const isDark = html.classList.contains('dark');
                  if (isDark) {
                    html.classList.remove('dark');
                    localStorage.setItem('theme', 'light');
                  } else {
                    html.classList.add('dark');
                    localStorage.setItem('theme', 'dark');
                  }
                }}
                className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md transition-colors flex items-center justify-center gap-2 text-sm active:scale-95"
                title="Alternar modo escuro/claro"
              >
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <span className="hidden sm:inline">Tema</span>
              </button>
              <button
                onClick={handleLogout}
                className="flex-1 sm:flex-none px-3 sm:px-4 py-2 min-h-[40px] bg-red-600 hover:bg-red-700 rounded-md transition-colors text-sm active:scale-95"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content - tela cheia para Clínica e Restaurante (sem faixas laterais) */}
      <main
        className={`${
          isFullWidth ? 'max-w-full' : 'max-w-7xl'
        } mx-auto py-4 sm:py-6 px-2 sm:px-4 md:px-6 lg:px-8`}
      >
        <div className="py-2 sm:py-4">
          {/* Dashboard específico por tipo */}
          {renderDashboardPorTipo(lojaInfo, handleLogout)}
        </div>
      </main>

      {/* Modal de Suporte - Aberto pelo botão fixo da barra superior */}
      {modalSuporteAberto && (
        <ModalChamado
          aberto={modalSuporteAberto}
          onFechar={() => setModalSuporteAberto(false)}
          lojaSlug={slug}
          lojaNome={lojaInfo.nome}
        />
      )}
        </>
      )}
    </div>
  );
}

function renderDashboardPorTipo(loja: LojaInfo, onLogout: () => void) {
  if (isTipoClinicaBeleza(loja.tipo_loja_nome)) return <DashboardClinicaBeleza loja={loja} onLogout={onLogout} />;
  if (isTipoClinicaEstetica(loja.tipo_loja_nome)) return <DashboardClinicaEstetica loja={loja} onLogout={onLogout} />;
  if (isTipoCommerce(loja.tipo_loja_nome)) return <DashboardEcommerce loja={loja} />;
  if (isTipoRestaurante(loja.tipo_loja_nome)) return <DashboardRestaurante loja={loja} />;
  if (isTipoServicos(loja.tipo_loja_nome)) return <DashboardServicos loja={loja} />;
  if (isTipoCabeleireiro(loja.tipo_loja_nome)) return <DashboardCabeleireiro loja={loja} />;
  return <DashboardGenerico loja={loja} />;
}

// Dashboard para E-commerce
function DashboardEcommerce({ loja }: { loja: LojaInfo }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
        Dashboard - E-commerce
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Pedidos Hoje</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>0</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Produtos</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>0</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Estoque</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>0</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Faturamento</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>R$ 0</p>
        </div>
      </div>
    </div>
  );
}

// Restaurante: usando DashboardRestaurante do template restaurante.tsx

// Dashboard Genérico (fallback)
function DashboardGenerico({ loja }: { loja: LojaInfo }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
        Dashboard - {loja.tipo_loja_nome}
      </h2>
      <div className="bg-white p-6 rounded-lg shadow text-center mb-6">
        <p className="text-gray-600 mb-4">
          Dashboard específico para {loja.tipo_loja_nome} em desenvolvimento
        </p>
        <p className="text-sm text-gray-500 mb-6">
          Em breve você terá acesso a funcionalidades personalizadas para seu tipo de negócio
        </p>
        <a
          href={`/loja/${loja.slug}/assinatura`}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-white hover:opacity-90 transition-opacity"
          style={{ backgroundColor: loja.cor_primaria || '#6366f1' }}
        >
          Pagar Assinatura (Boleto / PIX)
        </a>
      </div>
    </div>
  );
}
