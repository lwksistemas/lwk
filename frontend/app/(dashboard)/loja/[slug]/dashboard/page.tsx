'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import DashboardClinicaEstetica from './templates/clinica-estetica';
import DashboardCRMVendas from './templates/crm-vendas';

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

  const verificarECarregarLoja = async () => {
    try {
      setLoading(true);
      
      // Verificar se precisa trocar senha
      const checkResponse = await apiClient.get('/superadmin/lojas/verificar_senha_provisoria/');
      
      if (checkResponse.data.precisa_trocar_senha) {
        // Redirecionar para página de troca de senha
        router.push('/loja/trocar-senha');
        return;
      }
      
      // Carregar informações da loja
      const lojaResponse = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLojaInfo(lojaResponse.data);
      
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
    router.push(`/loja/${slug}/login`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-xl text-gray-600">Carregando...</div>
      </div>
    );
  }

  if (!lojaInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Erro ao carregar loja</h2>
          <button
            onClick={() => router.push(`/loja/${slug}/login`)}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Voltar para Login
          </button>
        </div>
      </div>
    );
  }

  // Renderizar dashboard específico por tipo de loja
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav 
        className="text-white shadow-lg"
        style={{ backgroundColor: lojaInfo.cor_primaria }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div>
              <h1 className="text-2xl font-bold">{lojaInfo.nome}</h1>
              <p className="text-sm opacity-90">{lojaInfo.tipo_loja_nome}</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              Sair
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Dashboard específico por tipo */}
          {renderDashboardPorTipo(lojaInfo)}
        </div>
      </main>
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
  if (tipoSlug.includes('servicos')) {
    return <DashboardServicos loja={loja} />;
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
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>24</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Produtos</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>156</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Estoque</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>1.234</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Faturamento</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>R$ 12.450</p>
        </div>
      </div>
    </div>
  );
}

// Dashboard para Restaurante
function DashboardRestaurante({ loja }: { loja: LojaInfo }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
        Dashboard - Restaurante
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Pedidos Hoje</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>45</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Mesas Ocupadas</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>12/20</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Cardápio</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>68</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Faturamento</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>R$ 3.890</p>
        </div>
      </div>
    </div>
  );
}

// Dashboard para CRM Vendas
function DashboardCRM({ loja }: { loja: LojaInfo }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
        Dashboard - CRM Vendas
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Leads Ativos</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>89</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Negociações</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>23</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Vendas Mês</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>156</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Receita</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>R$ 89.450</p>
        </div>
      </div>
    </div>
  );
}

// Dashboard para Serviços
function DashboardServicos({ loja }: { loja: LojaInfo }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
        Dashboard - Serviços
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Serviços Ativos</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>34</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Clientes</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>128</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Agendamentos</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>45</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm font-medium">Receita</h3>
          <p className="text-3xl font-bold mt-2" style={{ color: loja.cor_primaria }}>R$ 23.890</p>
        </div>
      </div>
    </div>
  );
}

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
