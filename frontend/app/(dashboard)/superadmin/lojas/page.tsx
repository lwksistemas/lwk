/**
 * Página de Gerenciamento de Lojas
 * ✅ REFATORADO v775: Layout em cards, hooks e componentes modulares
 * ✅ v1459: Adicionado modo de visualização em lista
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
import { LayoutGrid, List } from 'lucide-react';

type ModalType = 'create' | 'edit' | 'delete' | 'info' | null;
type ViewMode = 'cards' | 'list';

export default function GerenciarLojasPage() {
  const router = useRouter();
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [selectedLoja, setSelectedLoja] = useState<Loja | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');

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
    inativas: lojas.filter(l => !l.is_active).length,
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
            <div className="flex items-center gap-3">
              {/* Botões de visualização */}
              <div className="flex bg-purple-800 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('cards')}
                  className={`p-2 rounded transition-colors ${
                    viewMode === 'cards' 
                      ? 'bg-purple-600 text-white' 
                      : 'text-purple-200 hover:text-white'
                  }`}
                  title="Visualização em Cards"
                >
                  <LayoutGrid className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded transition-colors ${
                    viewMode === 'list' 
                      ? 'bg-purple-600 text-white' 
                      : 'text-purple-200 hover:text-white'
                  }`}
                  title="Visualização em Lista"
                >
                  <List className="w-5 h-5" />
                </button>
              </div>
              <button
                onClick={() => setActiveModal('create')}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
              >
                + Nova Loja
              </button>
            </div>
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
                  <p className="text-sm text-gray-600">Lojas Inativas</p>
                  <p className="text-2xl font-bold text-red-600">{stats.inativas}</p>
                </div>
                <div className="text-3xl">❌</div>
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
          ) : viewMode === 'cards' ? (
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
          ) : (
            /* Visualização em Lista */
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Loja
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tipo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        CPF/CNPJ
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Atalho
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Banco
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ações
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {lojas.map((loja) => (
                      <tr key={loja.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10">
                              {loja.logo ? (
                                <img className="h-10 w-10 rounded-full object-cover" src={loja.logo} alt="" />
                              ) : (
                                <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
                                  <span className="text-purple-600 font-semibold text-lg">
                                    {loja.nome.charAt(0).toUpperCase()}
                                  </span>
                                </div>
                              )}
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">{loja.nome}</div>
                              <div className="text-sm text-gray-500">{loja.owner_email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                            {loja.tipo_app_display}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {loja.cpf_cnpj}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {loja.atalho ? (
                            <span className="text-purple-600 font-mono">/{loja.atalho}</span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {loja.is_active ? (
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                              Ativa
                            </span>
                          ) : (
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                              Inativa
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {loja.database_created ? (
                            <span className="text-green-600">✓ Criado</span>
                          ) : (
                            <button
                              onClick={() => handleCriarBanco(loja.id)}
                              disabled={actionLoading}
                              className="text-blue-600 hover:text-blue-800 text-sm"
                            >
                              Criar Banco
                            </button>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleAbrirInfo(loja)}
                              className="text-blue-600 hover:text-blue-900"
                              title="Ver Informações"
                            >
                              👁️
                            </button>
                            <button
                              onClick={() => handleEdit(loja)}
                              className="text-yellow-600 hover:text-yellow-900"
                              title="Editar"
                            >
                              ✏️
                            </button>
                            {loja.senha_provisoria && (
                              <button
                                onClick={() => handleReenviarSenha(loja)}
                                disabled={actionLoading}
                                className="text-green-600 hover:text-green-900"
                                title="Reenviar Senha"
                              >
                                📧
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(loja)}
                              className="text-red-600 hover:text-red-900"
                              title="Excluir"
                            >
                              🗑️
                            </button>
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
