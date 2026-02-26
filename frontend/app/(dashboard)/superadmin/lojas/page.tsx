'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { ModalNovaLoja, ModalEditarLoja, ModalExcluirLoja } from '@/components/superadmin/lojas';

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

export default function GerenciarLojasPage() {
  const router = useRouter();
  const [lojas, setLojas] = useState<Loja[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

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

  const criarBanco = async (lojaId: number) => {
    if (!confirm('Deseja criar o banco de dados isolado para esta loja?')) return;

    try {
      const response = await apiClient.post(`/superadmin/lojas/${lojaId}/criar_banco/`);
      alert(`Banco criado com sucesso!\n\nUsuário: ${response.data.admin_username}\nSenha: ${response.data.admin_password}`);
      loadLojas();
    } catch (error: any) {
      alert(`Erro: ${error.response?.data?.error || 'Erro ao criar banco'}`);
    }
  };

  const [lojaParaExcluir, setLojaParaExcluir] = useState<Loja | null>(null);
  const [showModalExcluir, setShowModalExcluir] = useState(false);
  const [lojaParaEditar, setLojaParaEditar] = useState<Loja | null>(null);
  const [showModalEditar, setShowModalEditar] = useState(false);
  const [showModalInfo, setShowModalInfo] = useState(false);
  const [lojaInfo, setLojaInfo] = useState<{
    nome: string;
    slug: string;
    tamanho_banco_mb: number | null;
    tamanho_banco_estimativa_mb: number;
    tamanho_banco_motivo: string | null;
    database_created: boolean;
    espaco_plano_gb: number | null;
    espaco_livre_gb: number | null;
    senha_provisoria: string;
    login_page_url: string;
    owner_username: string;
    owner_email: string;
    owner_telefone?: string;
  } | null>(null);
  const [loadingInfo, setLoadingInfo] = useState(false);

  const excluirLoja = async (loja: Loja) => {
    setLojaParaExcluir(loja);
    setShowModalExcluir(true);
  };

  const editarLoja = (loja: Loja) => {
    setLojaParaEditar(loja);
    setShowModalEditar(true);
  };

  const reenviarSenha = async (loja: Loja) => {
    if (!loja.senha_provisoria) {
      alert('❌ Esta loja não possui senha provisória cadastrada.');
      return;
    }

    if (!confirm(`Reenviar senha provisória para ${loja.owner_email}?`)) return;

    try {
      const response = await apiClient.post(`/superadmin/lojas/${loja.id}/reenviar_senha/`);
      alert(`✅ ${response.data.message}`);
    } catch (error: any) {
      console.error('Erro ao reenviar senha:', error);
      alert(`❌ Erro ao reenviar senha: ${error.response?.data?.error || 'Erro desconhecido'}`);
    }
  };

  const abrirInformacoesLoja = async (loja: Loja) => {
    setShowModalInfo(true);
    setLojaInfo(null);
    setLoadingInfo(true);
    try {
      const response = await apiClient.get(`/superadmin/lojas/${loja.id}/info_loja/`);
      setLojaInfo(response.data);
    } catch (error: any) {
      console.error('Erro ao carregar informações da loja:', error);
      alert(`Erro ao carregar informações: ${error.response?.data?.error || 'Erro desconhecido'}`);
      setShowModalInfo(false);
    } finally {
      setLoadingInfo(false);
    }
  };

  const confirmarExclusao = async () => {
    if (!lojaParaExcluir) return;

    try {
      const response = await apiClient.delete(`/superadmin/lojas/${lojaParaExcluir.id}/`);
      
      // Verificar se a resposta tem a estrutura esperada
      if (!response.data || !response.data.detalhes) {
        // Exclusão bem-sucedida mas sem detalhes - mostrar mensagem simples
        alert(`✅ Loja "${lojaParaExcluir.nome}" foi removida com sucesso!`);
        setShowModalExcluir(false);
        setLojaParaExcluir(null);
        loadLojas();
        return;
      }
      
      // Mostrar detalhes da exclusão
      const detalhes = response.data.detalhes;
      const lojaNome = detalhes.loja_nome || lojaParaExcluir.nome;
      let mensagem = `✅ Loja "${lojaNome}" foi completamente removida!\n\n`;
      
      mensagem += `📋 Detalhes da limpeza:\n`;
      mensagem += `• Loja: ✅ Removida\n`;
      
      if (detalhes.banco_dados?.existia) {
        mensagem += `• Banco de dados: ✅ Arquivo removido (${detalhes.banco_dados.nome})\n`;
        mensagem += `• Configurações: ✅ Removidas do sistema\n`;
      } else {
        mensagem += `• Banco de dados: ℹ️ Não havia banco criado\n`;
      }
      
      if (detalhes.dados_financeiros?.financeiro_removido) {
        mensagem += `• Dados financeiros: ✅ Removidos\n`;
      }
      
      if (detalhes.dados_financeiros?.pagamentos_removidos > 0) {
        mensagem += `• Histórico de pagamentos: ✅ ${detalhes.dados_financeiros.pagamentos_removidos} registro(s) removido(s)\n`;
      }
      
      if (detalhes.usuario_proprietario?.removido) {
        mensagem += `• Usuário proprietário: ✅ Removido (${detalhes.usuario_proprietario.username})\n`;
      } else if (detalhes.usuario_proprietario?.username) {
        const motivo = detalhes.usuario_proprietario.motivo_nao_removido || 'Mantido no sistema';
        mensagem += `• Usuário proprietário: ℹ️ ${motivo} (${detalhes.usuario_proprietario.username})\n`;
      }
      
      mensagem += `\n🎯 Limpeza 100% completa!`;
      
      alert(mensagem);
      setShowModalExcluir(false);
      setLojaParaExcluir(null);
      loadLojas();
    } catch (error: any) {
      console.error('Erro ao excluir loja:', error);

      // 404 = loja já foi excluída ou não existe (ex.: lista desatualizada)
      if (error.response?.status === 404) {
        setShowModalExcluir(false);
        setLojaParaExcluir(null);
        loadLojas();
        alert('ℹ️ Esta loja já foi excluída ou não existe. A lista foi atualizada.');
        return;
      }
      
      let mensagemErro = '❌ Erro ao excluir loja:\n\n';
      
      if (error.response?.data?.error) {
        mensagemErro += error.response.data.error;
      } else if (error.message) {
        mensagemErro += error.message;
      } else {
        mensagemErro += 'Erro desconhecido';
      }
      
      if (error.response?.data?.detalhes) {
        mensagemErro += '\n\n' + error.response.data.detalhes;
      }
      
      alert(mensagemErro);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-purple-900 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a href="/superadmin/dashboard" className="text-purple-200 hover:text-white">
                ← Voltar
              </a>
              <h1 className="text-2xl font-bold">Gerenciar Lojas</h1>
            </div>
            <button
              onClick={() => setShowModal(true)}
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
                onClick={() => setShowModal(true)}
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
                            onClick={() => criarBanco(loja.id)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            Criar Banco
                          </button>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {loja.senha_provisoria ? (
                          <button
                            onClick={() => reenviarSenha(loja)}
                            className="text-xs text-blue-600 hover:text-blue-800"
                            title="Reenviar senha por email"
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
                          onClick={() => abrirInformacoesLoja(loja)}
                          className="text-purple-600 hover:text-purple-800 font-medium"
                          title="Ver informações da loja"
                        >
                          Informações da Loja
                        </button>
                        <button 
                          onClick={() => editarLoja(loja)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          Editar
                        </button>
                        <button 
                          onClick={() => excluirLoja(loja)}
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
      {showModal && <ModalNovaLoja onClose={() => setShowModal(false)} onSuccess={loadLojas} />}
      
      {/* Modal Editar Loja */}
      {showModalEditar && lojaParaEditar && (
        <ModalEditarLoja 
          loja={lojaParaEditar}
          onClose={() => {
            setShowModalEditar(false);
            setLojaParaEditar(null);
          }}
          onSuccess={() => {
            setShowModalEditar(false);
            setLojaParaEditar(null);
            loadLojas();
          }}
        />
      )}
      
      {/* Modal Excluir Loja */}
      {showModalExcluir && lojaParaExcluir && (
        <ModalExcluirLoja 
          loja={lojaParaExcluir}
          onClose={() => {
            setShowModalExcluir(false);
            setLojaParaExcluir(null);
          }}
          onConfirm={confirmarExclusao}
        />
      )}

      {/* Modal Informações da Loja */}
      {showModalInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowModalInfo(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="bg-purple-900 text-white px-6 py-4">
              <h2 className="text-xl font-bold">Informações da Loja</h2>
            </div>
            <div className="p-6">
              {loadingInfo ? (
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
                onClick={() => setShowModalInfo(false)}
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

