'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface Chamado {
  id: number;
  titulo: string;
  loja_nome: string;
  status: string;
  prioridade: string;
  created_at: string;
}

export default function SuporteDashboardPage() {
  const router = useRouter();
  const [chamados, setChamados] = useState<Chamado[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'suporte') {
        router.push('/suporte/login');
        return;
      }
      loadChamados();
    }
  }, [router]);

  const loadChamados = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/suporte/chamados/');
      setChamados(response.data.results || response.data);
    } catch (error) {
      console.error('Erro ao carregar chamados:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    router.push('/suporte/login');
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'aberto': 'bg-yellow-100 text-yellow-800',
      'em_andamento': 'bg-blue-100 text-blue-800',
      'resolvido': 'bg-green-100 text-green-800',
      'fechado': 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPrioridadeColor = (prioridade: string) => {
    const colors: Record<string, string> = {
      'baixa': 'text-gray-600',
      'media': 'text-yellow-600',
      'alta': 'text-orange-600',
      'urgente': 'text-red-600',
    };
    return colors[prioridade] || 'text-gray-600';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div>
              <h1 className="text-2xl font-bold">Portal de Suporte</h1>
              <p className="text-blue-200 text-sm">Gerenciamento de Chamados</p>
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
          {/* Estatísticas */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Total de Chamados</h3>
              <p className="text-3xl font-bold text-blue-600 mt-2">{chamados.length}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Abertos</h3>
              <p className="text-3xl font-bold text-yellow-600 mt-2">
                {chamados.filter(c => c.status === 'aberto').length}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Em Andamento</h3>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {chamados.filter(c => c.status === 'em_andamento').length}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Resolvidos</h3>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {chamados.filter(c => c.status === 'resolvido').length}
              </p>
            </div>
          </div>

          {/* Chamados */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-semibold">Chamados</h3>
            </div>
            <div className="p-6">
              {loading ? (
                <p className="text-center text-gray-500">Carregando...</p>
              ) : chamados.length === 0 ? (
                <p className="text-center text-gray-500 py-12">Nenhum chamado encontrado</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Título
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Loja
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Prioridade
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Ações
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {chamados.map((chamado) => (
                        <tr key={chamado.id}>
                          <td className="px-6 py-4 whitespace-nowrap">#{chamado.id}</td>
                          <td className="px-6 py-4">{chamado.titulo}</td>
                          <td className="px-6 py-4 whitespace-nowrap">{chamado.loja_nome}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(chamado.status)}`}>
                              {chamado.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`font-semibold ${getPrioridadeColor(chamado.prioridade)}`}>
                              {chamado.prioridade}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <button className="text-blue-600 hover:text-blue-800">
                              Atender
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
