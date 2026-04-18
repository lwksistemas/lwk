'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { useTipoAppList } from '@/hooks/useTipoAppList';
import { usePlanoList } from '@/hooks/usePlanoList';
import { usePlanoActions, Plano } from '@/hooks/usePlanoActions';
import { ModalNovoPlano, PlanoCard, TipoAppCard } from '@/components/superadmin/planos';

export default function PlanosPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<'tipos' | 'planos'>('tipos');
  const [tipoSelecionado, setTipoSelecionado] = useState<number | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingPlano, setEditingPlano] = useState<Plano | null>(null);

  const { tipos, loading: loadingTipos } = useTipoAppList();
  const { planos, loading: loadingPlanos, loadPlanos } = usePlanoList(tipoSelecionado);
  const { excluirPlano } = usePlanoActions();

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
    }
  }, [router]);

  const handleSelectTipo = (tipoId: number) => {
    setTipoSelecionado(tipoId);
    setViewMode('planos');
    loadPlanos(tipoId);
  };

  const voltarParaTipos = () => {
    setViewMode('tipos');
    setTipoSelecionado(null);
  };

  const handleEdit = (plano: Plano) => {
    setEditingPlano(plano);
    setShowModal(true);
  };

  const handleDelete = async (plano: Plano) => {
    if (!confirm(`Tem certeza que deseja excluir o plano "${plano.nome}"?`)) {
      return;
    }

    try {
      await excluirPlano(plano);
      alert('Plano excluído com sucesso!');
      if (tipoSelecionado) {
        loadPlanos(tipoSelecionado);
      }
    } catch (error: any) {
      alert(error.message);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingPlano(null);
  };

  const handleSuccess = () => {
    if (tipoSelecionado) {
      loadPlanos(tipoSelecionado);
    }
  };

  const tipoAtual = tipos.find(t => t.id === tipoSelecionado);
  const loading = loadingTipos || loadingPlanos;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <nav className="bg-purple-900 dark:bg-purple-950 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Planos de Assinatura</h1>
            </div>
            {viewMode === 'planos' && (
              <button
                onClick={() => setShowModal(true)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
              >
                + Novo Plano
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {loading ? (
            <div className="text-center py-12">Carregando...</div>
          ) : viewMode === 'tipos' ? (
            /* Visualização de Tipos de App */
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Selecione um Tipo de App
                </h2>
                <p className="text-gray-600">
                  Escolha um tipo de app para visualizar e gerenciar seus planos de assinatura
                </p>
              </div>

              {tipos.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <p className="text-gray-500 mb-4">Nenhum tipo de app cadastrado ainda.</p>
                  <a
                    href="/superadmin/tipos-app"
                    className="inline-block px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Criar Tipos de App
                  </a>
                </div>
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                          <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Tipo de App</th>
                          <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Lojas</th>
                          <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ação</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tipos.map((tipo) => (
                          <tr key={tipo.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer" onClick={() => handleSelectTipo(tipo.id)}>
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: tipo.cor_primaria || '#6b21a8' }} />
                                <span className="font-medium text-gray-900 dark:text-white">{tipo.nome}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">{tipo.total_lojas}</span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${tipo.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'}`}>
                                {tipo.is_active ? 'Ativo' : 'Inativo'}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <button className="px-3 py-1 text-sm bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded hover:bg-purple-200 dark:hover:bg-purple-900/50">Ver Planos →</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Visualização de Planos */
            <div className="space-y-6">
              {/* Header com breadcrumb */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <button
                      onClick={voltarParaTipos}
                      className="text-purple-600 hover:text-purple-800 mb-2 flex items-center space-x-2"
                    >
                      <span>←</span>
                      <span>Voltar para Tipos de App</span>
                    </button>
                    <h2 className="text-2xl font-bold text-gray-900">
                      {tipoAtual?.nome}
                    </h2>
                    <p className="text-gray-600 mt-1">
                      {planos.length} plano(s) disponível(is)
                    </p>
                  </div>
                </div>
              </div>

              {/* Lista de Planos */}
              {planos.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <p className="text-gray-500 mb-4">
                    Nenhum plano disponível para este tipo de app.
                  </p>
                  <button
                    onClick={() => setShowModal(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Criar Primeiro Plano
                  </button>
                </div>
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                          <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Plano</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Mensal</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Anual</th>
                          <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Lojas</th>
                          <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ações</th>
                        </tr>
                      </thead>
                      <tbody>
                        {planos.map((plano) => (
                          <tr key={plano.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                            <td className="py-3 px-4">
                              <span className="font-medium text-gray-900 dark:text-white">{plano.nome}</span>
                              {plano.descricao && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate max-w-xs">{plano.descricao}</p>}
                            </td>
                            <td className="py-3 px-4 text-right font-medium text-gray-900 dark:text-white">
                              {parseFloat(plano.preco_mensal).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                            </td>
                            <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                              {parseFloat(plano.preco_anual).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">{plano.total_lojas}</span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${plano.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'}`}>
                                {plano.is_active ? 'Ativo' : 'Inativo'}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex justify-end gap-1">
                                <button onClick={() => handleEdit(plano)} className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50">Editar</button>
                                <button onClick={() => handleDelete(plano)} className="px-3 py-1 text-sm bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/50">Excluir</button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Modal Novo Plano */}
      {showModal && (
        <ModalNovoPlano 
          onClose={handleCloseModal} 
          onSuccess={handleSuccess}
          editingPlano={editingPlano}
          tipoLojaId={tipoSelecionado}
        />
      )}
    </div>
  );
}
