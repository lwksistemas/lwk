'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { ModalNovaLoja, ModalEditarLoja, ModalExcluirLoja } from '@/components/superadmin/lojas';
import { useLojaActions } from '@/hooks/useLojaActions';
import { useLojaInfo } from '@/hooks/useLojaInfo';

interface Loja {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  plano_nome: string;
  owner_username: string;
  owner_email: string;
  owner_telefone?: string;
  senha_provisoria: string;
  is_active: boolean;
  is_trial: boolean;
  database_created: boolean;
  login_page_url: string;
  created_at: string;
}

type ModalType = 'create' | 'edit' | 'delete' | 'info' | null;

export default function GerenciarLojasPage() {
  const router = useRouter();
  const [lojas, setLojas] = useState<Loja[]>([]);
  const [loading, setLoading] = useState(true);
  
  // ✅ REFATORAÇÃO v765: Estado único para modais
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [selectedLoja, setSelectedLoja] = useState<Loja | null>(null);
  
  // ✅ REFATORAÇÃO v765: Hooks customizados
  const { excluirLoja, reenviarSenha, criarBanco, loading: actionLoading } = useLojaActions();
  const { lojaInfo, loading: infoLoading, loadLojaInfo } = useLojaInfo();

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadLojas();
  }, [router]);

  const loadLojas = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/superadmin/lojas/');
      // A API retorna {count, results} ou um array direto
      const data = response.data.results || response.data;
      setLojas(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Erro ao carregar lojas:', error);
      setLojas([]);
    } finally {
      setLoading(false);
    }
  };

  // ✅ REFATORAÇÃO v765: Funções simplificadas usando hooks
  const handleCriarBanco = async (lojaId: number) => {
    if (!confirm('Deseja criar o banco de dados isolado para esta loja?')) return;
    const result = await criarBanco(lojaId);
    alert(result.message);
    if (result.success) loadLojas();
  };

  const handleExcluirLoja = (loja: Loja) => {
    setSelectedLoja(loja);
    setActiveModal('delete');
  };

  const handleEditarLoja = (loja: Loja) => {
    setSelectedLoja(loja);
    setActiveModal('edit');
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

  const handleConfirmarExclusao = async () => {
    if (!selectedLoja) return;
    const result = await excluirLoja(selectedLoja);
    alert(result.message);
    if (result.success) {
      setActiveModal(null);
      setSelectedLoja(null);
      loadLojas();
    }
  };

  const handleCloseModal = () => {
    setActiveModal(null);
    setSelectedLoja(null);
  };

  const handleSuccessModal = () => {
    setActiveModal(null);
    setSelectedLoja(null);
    loadLojas();
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
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Loja
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Plano
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Banco
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Acesso
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {Array.isArray(lojas) && lojas.map((loja) => (
                    <tr key={loja.id}>
                      <td className="px-6 py-4">
                        <div>
                          <div className="font-medium text-gray-900">{loja.nome}</div>
                          <div className="text-sm text-gray-500">{loja.owner_username}</div>
                          <div className="text-xs text-gray-400">{loja.owner_email}</div>
                          {loja.owner_telefone ? <div className="text-xs text-gray-400">Tel: {loja.owner_telefone}</div> : null}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm">{loja.tipo_loja_nome}</td>
                      <td className="px-6 py-4 text-sm">{loja.plano_nome}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            loja.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {loja.is_active ? 'Ativa' : 'Inativa'}
                        </span>
                        {loja.is_trial && (
                          <span className="ml-2 px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">
                            Trial
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {loja.database_created ? (
                          <span className="text-green-600">✓ Criado</span>
                        ) : (
                          <button
                            onClick={() => handleCriarBanco(loja.id)}
                            className="text-blue-600 hover:text-blue-800"
                            disabled={actionLoading}
                          >
                            Criar Banco
                          </button>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {loja.senha_provisoria ? (
                          <button
                            onClick={() => handleReenviarSenha(loja)}
                            className="text-xs text-blue-600 hover:text-blue-800"
                            title="Reenviar senha por email"
                            disabled={actionLoading}
                          >
                            📧 Reenviar senha
                          </button>
                        ) : (
                          <span className="text-xs text-gray-400">Sem senha provisória</span>
                        )}
                        <p className="text-xs text-gray-500 mt-1">Senha em Informações da Loja</p>
                      </td>
                      <td className="px-6 py-4 text-sm space-x-2">
                        <button
                          onClick={() => handleAbrirInfo(loja)}
                          className="text-purple-600 hover:text-purple-800 font-medium"
                          title="Ver informações da loja"
                        >
                          Informações da Loja
                        </button>
                        <button 
                          onClick={() => handleEditarLoja(loja)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          Editar
                        </button>
                        <button 
                          onClick={() => handleExcluirLoja(loja)}
                          className="text-red-600 hover:text-red-800"
                          title={loja.database_created ? 'Não é possível excluir - banco criado' : 'Excluir loja'}
                        >
                          Excluir
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Modal Nova Loja */}
      {activeModal === 'create' && (
        <ModalNovaLoja onClose={handleCloseModal} onSuccess={handleSuccessModal} />
      )}
      
      {/* Modal Editar Loja */}
      {activeModal === 'edit' && selectedLoja && (
        <ModalEditarLoja 
          loja={selectedLoja}
          onClose={handleCloseModal}
          onSuccess={handleSuccessModal}
        />
      )}
      
      {/* Modal Excluir Loja */}
      {activeModal === 'delete' && selectedLoja && (
        <ModalExcluirLoja 
          loja={selectedLoja}
          onClose={handleCloseModal}
          onConfirm={handleConfirmarExclusao}
        />
      )}

      {/* Modal Informações da Loja */}
      {activeModal === 'info' && selectedLoja && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={handleCloseModal}>
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="bg-purple-900 text-white px-6 py-4">
              <h2 className="text-xl font-bold">Informações da Loja</h2>
            </div>
            <div className="p-6">
              {infoLoading ? (
                <div className="text-center py-8 text-gray-500">Carregando...</div>
              ) : lojaInfo ? (
                <div className="space-y-4 text-sm">
                  <div>
                    <span className="font-semibold text-gray-500 block mb-1">Loja</span>
                    <p className="font-medium text-gray-900">{lojaInfo.nome}</p>
                  </div>
                  {/* ✅ ATUALIZADO v742: Exibir dados reais do monitoramento de storage */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <span className="font-semibold text-gray-500 block mb-1">Storage usado</span>
                      <p className="text-gray-900">
                        {lojaInfo.storage_usado_mb != null
                          ? `${lojaInfo.storage_usado_mb.toFixed(2)} MB`
                          : '0.00 MB'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {lojaInfo.storage_percentual != null
                          ? `${lojaInfo.storage_percentual.toFixed(1)}% do limite`
                          : 'Aguardando verificação'}
                      </p>
                    </div>
                    <div>
                      <span className="font-semibold text-gray-500 block mb-1">Storage disponível</span>
                      <p className="text-gray-900">
                        {lojaInfo.storage_livre_gb != null 
                          ? `${lojaInfo.storage_livre_gb} GB` 
                          : lojaInfo.espaco_plano_gb != null 
                          ? `${lojaInfo.espaco_plano_gb} GB (plano)` 
                          : '—'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Limite: {lojaInfo.storage_limite_mb != null 
                          ? `${(lojaInfo.storage_limite_mb / 1024).toFixed(0)} GB` 
                          : '5 GB'}
                      </p>
                    </div>
                  </div>
                  
                  {/* ✅ NOVO v742: Status do storage com cores */}
                  {lojaInfo.storage_status && (
                    <div className={`p-3 rounded-lg ${
                      lojaInfo.storage_status === 'critical' 
                        ? 'bg-red-50 border border-red-200' 
                        : lojaInfo.storage_status === 'warning'
                        ? 'bg-yellow-50 border border-yellow-200'
                        : 'bg-green-50 border border-green-200'
                    }`}>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${
                          lojaInfo.storage_status === 'critical'
                            ? 'text-red-700'
                            : lojaInfo.storage_status === 'warning'
                            ? 'text-yellow-700'
                            : 'text-green-700'
                        }`}>
                          {lojaInfo.storage_status === 'critical' && '🚫'}
                          {lojaInfo.storage_status === 'warning' && '⚠️'}
                          {lojaInfo.storage_status === 'ok' && '✅'}
                          {' '}
                          {lojaInfo.storage_status_texto}
                        </span>
                      </div>
                      {lojaInfo.storage_ultima_verificacao && (
                        <p className="text-xs text-gray-600 mt-1">
                          Última verificação: {lojaInfo.storage_horas_desde_verificacao != null 
                            ? `há ${lojaInfo.storage_horas_desde_verificacao}h` 
                            : 'recente'}
                        </p>
                      )}
                    </div>
                  )}
                  <div>
                    <span className="font-semibold text-gray-500 block mb-1">Senha de acesso</span>
                    <p className="text-gray-900 font-mono bg-gray-100 px-2 py-1 rounded break-all">
                      {lojaInfo.senha_provisoria || '—'}
                    </p>
                  </div>
                  <div>
                    <span className="font-semibold text-gray-500 block mb-1">Página de login da loja</span>
                    <p className="text-gray-900 break-all">
                      {lojaInfo.login_page_url ? (
                        <a
                          href={typeof window !== 'undefined' ? `${window.location.origin}${lojaInfo.login_page_url}` : lojaInfo.login_page_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-purple-600 hover:text-purple-800 underline"
                        >
                          {typeof window !== 'undefined' ? `${window.location.origin}${lojaInfo.login_page_url}` : lojaInfo.login_page_url}
                        </a>
                      ) : '—'}
                    </p>
                  </div>
                  <div className="pt-2 border-t border-gray-200">
                    <span className="font-semibold text-gray-500 block mb-1">Usuário / E-mail</span>
                    <p className="text-gray-900">{lojaInfo.owner_username} — {lojaInfo.owner_email}</p>
                    {lojaInfo.owner_telefone ? <p className="text-gray-600 text-sm mt-1">Tel: {lojaInfo.owner_telefone}</p> : null}
                  </div>
                </div>
              ) : null}
            </div>
            <div className="px-6 py-4 bg-gray-50 border-t flex justify-end">
              <button
                onClick={handleCloseModal}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-md"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

