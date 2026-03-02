/**
 * Página de Gerenciamento de Lojas
 * ✅ REFATORADO v775: Layout em cards, hooks e componentes modulares
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { useLojaList, Loja } from '@/hooks/useLojaList';
import { useLojaActions } from '@/hooks/useLojaActions';
import { useLojaInfo } from '@/hooks/useLojaInfo';
import { 
  ModalNovaLoja, 
  ModalEditarLoja, 
  ModalExcluirLoja,
  LojaCard,
  LojaInfoModal 
} from '@/components/superadmin/lojas';

type ModalType = 'create' | 'edit' | 'delete' | 'info' | null;

export default function GerenciarLojasPage() {
  const router = useRouter();
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [selectedLoja, setSelectedLoja] = useState<Loja | null>(null);

  const { lojas, loading, reload } = useLojaList();
  const { excluirLoja, reenviarSenha, criarBanco, loading: actionLoading } = useLojaActions();
  const { lojaInfo, loading: infoLoading, loadLojaInfo } = useLojaInfo();

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
    }
  }, [router]);

  const handleCriarBanco = async (lojaId: number) => {
    if (!confirm('Deseja criar o banco de dados isolado para esta loja?')) return;
    const result = await criarBanco(lojaId);
    alert(result.message);
    if (result.success) reload();
  };

  const handleReenviarSenha = async (loja: Loja) => {
    if (!loja.senha_provisoria) {
      alert('❌ Esta loja não possui senha provisória cadastrada.');
      return;
    }
    if (!confirm(`Reenviar senha provisória para ${loja.owner_email}?`)) return;
    const result = await reenviarSenha(loja);
    alert(result.message);
  };

  const handleAbrirInfo = async (loja: Loja) => {
    setSelectedLoja(loja);
    setActiveModal('info');
    await loadLojaInfo(loja.id);
  };

  const handleEdit = (loja: Loja) => {
    setSelectedLoja(loja);
    setActiveModal('edit');
  };

  const handleDelete = (loja: Loja) => {
    setSelectedLoja(loja);
    setActiveModal('delete');
  };

  const handleConfirmarExclusao = async () => {
    if (!selectedLoja) return;
    const result = await excluirLoja(selectedLoja);
    alert(result.message);
    if (result.success) {
      setActiveModal(null);
      setSelectedLoja(null);
      reload();
    }
  };

  const handleCloseModal = () => {
    setActiveModal(null);
    setSelectedLoja(null);
  };

  const handleSuccessModal = () => {
    setActiveModal(null);
    setSelectedLoja(null);
    reload();
  };

  // Estatísticas
  const stats = {
    total: lojas.length,
    ativas: lojas.filter(l => l.is_active).length,
    trial: lojas.filter(l => l.is_trial).length,
    comBanco: lojas.filter(l => l.database_created).length,
  };

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
              <h1 className="text-2xl font-bold">Gerenciar Lojas</h1>
            </div>
            <button
              onClick={() => setActiveModal('create')}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
            >
              + Nova Loja
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Estatísticas */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total de Lojas</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.total}</p>
                </div>
                <div className="text-3xl">🏪</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Lojas Ativas</p>
                  <p className="text-2xl font-bold text-green-600">{stats.ativas}</p>
                </div>
                <div className="text-3xl">✅</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Em Trial</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.trial}</p>
                </div>
                <div className="text-3xl">⏱️</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Com Banco</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.comBanco}</p>
                </div>
                <div className="text-3xl">💾</div>
              </div>
            </div>
          </div>

          {/* Lista de Lojas */}
          {loading ? (
            <div className="text-center py-12">Carregando...</div>
          ) : lojas.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500 mb-4">Nenhuma loja cadastrada ainda.</p>
              <button
                onClick={() => setActiveModal('create')}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
              >
                Criar Primeira Loja
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {lojas.map((loja) => (
                <LojaCard
                  key={loja.id}
                  loja={loja}
                  onInfo={handleAbrirInfo}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onCriarBanco={handleCriarBanco}
                  onReenviarSenha={handleReenviarSenha}
                  actionLoading={actionLoading}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
      {activeModal === 'create' && (
        <ModalNovaLoja onClose={handleCloseModal} onSuccess={handleSuccessModal} />
      )}
      
      {activeModal === 'edit' && selectedLoja && (
        <ModalEditarLoja 
          loja={selectedLoja}
          onClose={handleCloseModal}
          onSuccess={handleSuccessModal}
        />
      )}
      
      {activeModal === 'delete' && selectedLoja && (
        <ModalExcluirLoja 
          loja={selectedLoja}
          onClose={handleCloseModal}
          onConfirm={handleConfirmarExclusao}
        />
      )}

      {activeModal === 'info' && (
        <LojaInfoModal
          lojaInfo={lojaInfo}
          loading={infoLoading}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}
