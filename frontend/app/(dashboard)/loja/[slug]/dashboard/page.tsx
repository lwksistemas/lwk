'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import ModalChamado from '@/components/suporte/ModalChamado';
import DashboardClinicaEstetica from './templates/clinica-estetica';
import DashboardCRMVendas from './templates/crm-vendas';
import DashboardRestaurante from './templates/restaurante';
import DashboardServicos from './templates/servicos';
import DashboardCabeleireiro from './templates/cabeleireiro';

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
  
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingLento, setLoadingLento] = useState(false);
  const [modalSuporteAberto, setModalSuporteAberto] = useState(false);

  // Forçar reload se vier de cache (bfcache)
  useEffect(() => {
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        console.log('⚠️ Página carregada do cache (bfcache) - forçando reload');
        window.location.reload();
      }
    };
    
    window.addEventListener('pageshow', handlePageShow);
    return () => window.removeEventListener('pageshow', handlePageShow);
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'loja') {
        router.push(`/loja/${slug}/login`);
        return;
      }

      verificarECarregarLoja();
    }
  }, [router, slug]);

  // Mostrar dica se o carregamento passar de 8s (ex.: cold start Heroku)
  useEffect(() => {
    if (!loading) return;
    const t = setTimeout(() => setLoadingLento(true), 8000);
    return () => clearTimeout(t);
  }, [loading]);

  const verificarECarregarLoja = async () => {
    try {
      setLoading(true);
      
      // Carregar informações da loja
      const lojaResponse = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      const data = lojaResponse.data;
      // ✅ Definir current_loja_id e loja_slug ANTES de renderizar (APIs da clínica usam X-Loja-ID; loja_slug é fallback no mobile)
      if (data?.id && typeof window !== 'undefined') {
        sessionStorage.setItem('current_loja_id', String(data.id));
        if (data.slug) sessionStorage.setItem('loja_slug', data.slug);
      }
      setLojaInfo(data);
      
    } catch (error: any) {
      console.error('Erro ao carregar loja:', error);
      if (error.response?.status === 401) {
        router.push(`/loja/${slug}/login`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    sessionStorage.removeItem('current_loja_id'); // Limpar loja_id
    router.push(`/loja/${slug}/login`);
  };

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

  // Descobrir se é clínica de estética ou restaurante para layout em tela cheia (sem faixas laterais)
  const tipoSlug = lojaInfo.tipo_loja_nome.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const isClinicaEstetica = tipoSlug.includes('clinica') || tipoSlug.includes('estetica');
  const isRestaurante = tipoSlug.includes('restaurante');
  const isFullWidth = isClinicaEstetica || isRestaurante;

  // Renderizar dashboard específico por tipo de loja
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
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
          {renderDashboardPorTipo(lojaInfo)}
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
    </div>
  );
}

function renderDashboardPorTipo(loja: LojaInfo) {
  const tipoSlug = loja.tipo_loja_nome.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  
  // Dashboard específico para Clínica de Estética
  if (tipoSlug.includes('clinica') || tipoSlug.includes('estetica')) {
    return <DashboardClinicaEstetica loja={loja} />;
  }
  
  // Dashboard específico para E-commerce
  if (tipoSlug.includes('commerce')) {
    return <DashboardEcommerce loja={loja} />;
  }
  
  // Dashboard específico para Restaurante
  if (tipoSlug.includes('restaurante')) {
    return <DashboardRestaurante loja={loja} />;
  }
  
  // Dashboard específico para CRM Vendas
  if (tipoSlug.includes('crm') || tipoSlug.includes('vendas')) {
    return <DashboardCRMVendas loja={loja} />;
  }
  
  // Dashboard específico para Serviços
  if (tipoSlug.includes('servicos') || tipoSlug.includes('servico')) {
    return <DashboardServicos loja={loja} />;
  }
  
  // Dashboard específico para Cabeleireiro (v561 - FORÇADO)
  if (tipoSlug.includes('cabeleireiro') || tipoSlug.includes('salao') || tipoSlug.includes('barbearia')) {
    console.log('✅✅✅ CARREGANDO DASHBOARD CABELEIREIRO v561 - NOVO ✅✅✅');
    return <DashboardCabeleireiro loja={loja} />;
  }
  
  // Dashboard genérico (fallback)
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
      <div className="bg-white p-6 rounded-lg shadow text-center">
        <p className="text-gray-600 mb-4">
          Dashboard específico para {loja.tipo_loja_nome} em desenvolvimento
        </p>
        <p className="text-sm text-gray-500">
          Em breve você terá acesso a funcionalidades personalizadas para seu tipo de negócio
        </p>
      </div>
    </div>
  );
}
