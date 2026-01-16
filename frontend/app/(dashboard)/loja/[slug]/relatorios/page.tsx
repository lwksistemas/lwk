'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
}

export default function RelatoriosPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;
  
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [periodoSelecionado, setPeriodoSelecionado] = useState('mes_atual');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'loja') {
        router.push(`/loja/${slug}/login`);
        return;
      }

      carregarLoja();
    }
  }, [router, slug]);

  const carregarLoja = async () => {
    try {
      setLoading(true);
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

  const handleVoltar = () => {
    router.push(`/loja/${slug}/dashboard`);
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
              <p className="text-sm opacity-90">Relatórios</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleVoltar}
                className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md transition-colors"
              >
                ← Voltar
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          
          {/* Filtros */}
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4">Filtros</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Período
                </label>
                <select
                  value={periodoSelecionado}
                  onChange={(e) => setPeriodoSelecionado(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                >
                  <option value="hoje">Hoje</option>
                  <option value="semana_atual">Semana Atual</option>
                  <option value="mes_atual">Mês Atual</option>
                  <option value="mes_anterior">Mês Anterior</option>
                  <option value="trimestre">Último Trimestre</option>
                  <option value="ano">Ano Atual</option>
                  <option value="personalizado">Personalizado</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Início
                </label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Fim
                </label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0"
                />
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                className="px-6 py-2 text-white rounded-md hover:opacity-90"
                style={{ backgroundColor: lojaInfo.cor_primaria }}
              >
                Aplicar Filtros
              </button>
            </div>
          </div>

          {/* Resumo Financeiro */}
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4" style={{ color: lojaInfo.cor_primaria }}>
              📊 Resumo Financeiro
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Receita Total</p>
                <p className="text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  R$ 0,00
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Despesas</p>
                <p className="text-2xl font-bold text-red-600">
                  R$ 0,00
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Lucro Líquido</p>
                <p className="text-2xl font-bold text-green-600">
                  R$ 0,00
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Margem</p>
                <p className="text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  0%
                </p>
              </div>
            </div>
          </div>

          {/* Agendamentos */}
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4" style={{ color: lojaInfo.cor_primaria }}>
              📅 Relatório de Agendamentos
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Total de Agendamentos</p>
                <p className="text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  0
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Realizados</p>
                <p className="text-2xl font-bold text-green-600">
                  0 (0%)
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Cancelados</p>
                <p className="text-2xl font-bold text-red-600">
                  0 (0%)
                </p>
              </div>
            </div>

            <div className="text-center py-8 text-gray-500">
              <p className="text-lg">Nenhum agendamento registrado no período</p>
            </div>
          </div>

          {/* Clientes */}
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4" style={{ color: lojaInfo.cor_primaria }}>
              👥 Relatório de Clientes
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Total de Clientes</p>
                <p className="text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  0
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Novos no Período</p>
                <p className="text-2xl font-bold text-green-600">
                  0
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Clientes Ativos</p>
                <p className="text-2xl font-bold" style={{ color: lojaInfo.cor_primaria }}>
                  0
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Taxa de Retorno</p>
                <p className="text-2xl font-bold text-green-600">
                  0%
                </p>
              </div>
            </div>
          </div>

          {/* Profissionais */}
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h3 className="text-lg font-semibold mb-4" style={{ color: lojaInfo.cor_primaria }}>
              👨‍⚕️ Desempenho dos Profissionais
            </h3>
            <div className="text-center py-8 text-gray-500">
              <p className="text-lg">Nenhum profissional cadastrado</p>
            </div>
          </div>

          {/* Botões de Exportação */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Exportar Relatórios</h3>
            <div className="flex flex-wrap gap-4">
              <button
                className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                📄 Exportar Excel
              </button>
              <button
                className="px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                📑 Exportar PDF
              </button>
              <button
                className="px-6 py-3 text-white rounded-md hover:opacity-90 transition-colors"
                style={{ backgroundColor: lojaInfo.cor_primaria }}
              >
                📧 Enviar por Email
              </button>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
