'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { useTipoLojaList } from '@/hooks/useTipoLojaList';
import { usePlanoList } from '@/hooks/usePlanoList';
import { usePlanoActions, Plano } from '@/hooks/usePlanoActions';
import { ModalNovoPlano, PlanoCard, TipoLojaCard } from '@/components/superadmin/planos';

export default function PlanosPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<'tipos' | 'planos'>('tipos');
  const [tipoSelecionado, setTipoSelecionado] = useState<number | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingPlano, setEditingPlano] = useState<Plano | null>(null);

  const { tipos, loading: loadingTipos } = useTipoLojaList();
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
            /* Visualização de Tipos de Loja */
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Selecione um Tipo de Loja
                </h2>
                <p className="text-gray-600">
                  Escolha um tipo de loja para visualizar e gerenciar seus planos de assinatura
                </p>
              </div>

              {tipos.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <p className="text-gray-500 mb-4">Nenhum tipo de app cadastrado ainda.</p>
                  <a
                    href="/superadmin/tipos-app"
                    className="inline-block px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Criar Tipos de Loja
                  </a>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {tipos.map((tipo) => (
                    <TipoLojaCard
                      key={tipo.id}
                      tipo={tipo}
                      onClick={() => handleSelectTipo(tipo.id)}
                    />
                  ))}
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
                      <span>Voltar para Tipos de Loja</span>
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
                    Nenhum plano disponível para este tipo de loja.
                  </p>
                  <button
                    onClick={() => setShowModal(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Criar Primeiro Plano
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {planos.map((plano) => (
                    <PlanoCard
                      key={plano.id}
                      plano={plano}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                    />
                  ))}
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
