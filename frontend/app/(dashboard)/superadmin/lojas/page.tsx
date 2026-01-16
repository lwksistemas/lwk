'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface Loja {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  plano_nome: string;
  owner_username: string;
  owner_email: string;
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

  const mostrarSenha = (loja: Loja) => {
    if (!loja.senha_provisoria) {
      alert('❌ Esta loja não possui senha provisória cadastrada.');
      return;
    }

    const mensagem = `🔐 DADOS DE ACESSO - ${loja.nome}\n\n` +
      `• URL: http://localhost:3000${loja.login_page_url}\n` +
      `• Usuário: ${loja.owner_username}\n` +
      `• Email: ${loja.owner_email}\n` +
      `• Senha Provisória: ${loja.senha_provisoria}\n\n` +
      `⚠️ Esta senha foi enviada por email para o proprietário.`;
    
    alert(mensagem);
  };

  const confirmarExclusao = async () => {
    if (!lojaParaExcluir) return;

    try {
      const response = await apiClient.delete(`/superadmin/lojas/${lojaParaExcluir.id}/`);
      
      // Mostrar detalhes da exclusão
      const detalhes = response.data.detalhes;
      let mensagem = `✅ Loja "${response.data.detalhes.loja_nome}" foi completamente removida!\n\n`;
      
      mensagem += `📋 Detalhes da limpeza:\n`;
      mensagem += `• Loja: ✅ Removida\n`;
      
      if (detalhes.banco_dados.existia) {
        mensagem += `• Banco de dados: ✅ Arquivo removido (${detalhes.banco_dados.nome})\n`;
        mensagem += `• Configurações: ✅ Removidas do sistema\n`;
      } else {
        mensagem += `• Banco de dados: ℹ️ Não havia banco criado\n`;
      }
      
      if (detalhes.dados_financeiros.financeiro_removido) {
        mensagem += `• Dados financeiros: ✅ Removidos\n`;
      }
      
      if (detalhes.dados_financeiros.pagamentos_removidos > 0) {
        mensagem += `• Histórico de pagamentos: ✅ ${detalhes.dados_financeiros.pagamentos_removidos} registro(s) removido(s)\n`;
      }
      
      if (detalhes.usuario_proprietario.removido) {
        mensagem += `• Usuário proprietário: ✅ Removido (${detalhes.usuario_proprietario.username})\n`;
      } else {
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
      
      let mensagemErro = '❌ Erro ao excluir loja:\n\n';
      
      if (error.response?.data?.error) {
        mensagemErro += error.response.data.error;
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
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
                          <div className="space-y-1">
                            <button
                              onClick={() => mostrarSenha(loja)}
                              className="block text-xs text-purple-600 hover:text-purple-800"
                              title="Ver dados de acesso"
                            >
                              🔐 Ver Senha
                            </button>
                            <button
                              onClick={() => reenviarSenha(loja)}
                              className="block text-xs text-blue-600 hover:text-blue-800"
                              title="Reenviar senha por email"
                            >
                              📧 Reenviar
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">Sem senha provisória</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm space-x-2">
                        <a
                          href={loja.login_page_url}
                          target="_blank"
                          className="text-purple-600 hover:text-purple-800"
                        >
                          Acessar
                        </a>
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
      {showModal && <NovaLojaModal onClose={() => setShowModal(false)} onSuccess={loadLojas} />}
      
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
    </div>
  );
}

// Componente do Modal
function NovaLojaModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [loading, setLoading] = useState(false);
  const [tipos, setTipos] = useState<any[]>([]);
  const [planos, setPlanos] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    nome: '',
    slug: '',
    descricao: '',
    cpf_cnpj: '',
    tipo_loja: '',
    plano: '',
    tipo_assinatura: 'mensal',
    dia_vencimento: 10,
    owner_username: '',
    owner_password: '',
    owner_email: '',
  });

  useEffect(() => {
    loadTiposEPlanos();
    gerarSenhaProvisoria(); // Gerar senha ao abrir o modal
  }, []);

  const gerarSenhaProvisoria = () => {
    // Gerar senha segura: 8 caracteres com letras, números e símbolos
    const letras = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numeros = '0123456789';
    const simbolos = '!@#$%&*';
    const todos = letras + numeros + simbolos;
    
    let senha = '';
    // Garantir pelo menos 1 letra, 1 número e 1 símbolo
    senha += letras[Math.floor(Math.random() * letras.length)];
    senha += numeros[Math.floor(Math.random() * numeros.length)];
    senha += simbolos[Math.floor(Math.random() * simbolos.length)];
    
    // Completar com caracteres aleatórios até 8 caracteres
    for (let i = 3; i < 8; i++) {
      senha += todos[Math.floor(Math.random() * todos.length)];
    }
    
    // Embaralhar a senha
    senha = senha.split('').sort(() => Math.random() - 0.5).join('');
    
    setFormData(prev => ({ ...prev, owner_password: senha }));
  };

  const loadTiposEPlanos = async () => {
    try {
      const tiposRes = await apiClient.get('/superadmin/tipos-loja/');
      setTipos(tiposRes.data.results || tiposRes.data);
      
      // Carregar todos os planos inicialmente
      const planosRes = await apiClient.get('/superadmin/planos/');
      setPlanos(planosRes.data.results || planosRes.data);
    } catch (error) {
      console.error('Erro ao carregar tipos e planos:', error);
    }
  };

  // Função para carregar planos por tipo
  const loadPlanosPorTipo = async (tipoId: string) => {
    if (!tipoId) {
      setPlanos([]);
      return;
    }
    
    try {
      const response = await apiClient.get(`/superadmin/planos/por_tipo/?tipo_id=${tipoId}`);
      setPlanos(response.data);
    } catch (error) {
      console.error('Erro ao carregar planos por tipo:', error);
      setPlanos([]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Auto-gerar slug a partir do nome
    if (name === 'nome') {
      const slug = value.toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '');
      setFormData(prev => ({ ...prev, slug }));
    }
    
    // Carregar planos quando tipo de loja for selecionado
    if (name === 'tipo_loja' && value) {
      loadPlanosPorTipo(value);
      // Limpar plano selecionado
      setFormData(prev => ({ ...prev, plano: '' }));
    }
  };

  const formatCpfCnpj = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 11) {
      // CPF: 000.000.000-00
      return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    } else {
      // CNPJ: 00.000.000/0000-00
      return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
  };

  const handleCpfCnpjChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCpfCnpj(e.target.value);
    setFormData(prev => ({ ...prev, cpf_cnpj: formatted }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('Dados enviados:', formData);
      
      // Criar loja (banco será criado automaticamente no backend se necessário)
      const response = await apiClient.post('/superadmin/lojas/', formData);
      
      // Mostrar informações da loja criada
      const loja = response.data;
      let mensagem = `✅ Loja "${loja.nome}" criada com sucesso!\n\n`;
      
      mensagem += `📋 Informações importantes:\n`;
      mensagem += `• Email enviado para: ${formData.owner_email}\n`;
      
      if (loja.senha_provisoria || loja._senha_provisoria) {
        const senha = loja.senha_provisoria || loja._senha_provisoria;
        mensagem += `• Senha provisória gerada: ${senha}\n`;
      }
      
      mensagem += `\n🔐 Dados de acesso enviados por email:\n`;
      mensagem += `• URL: http://localhost:3000${loja.login_page_url}\n`;
      mensagem += `• Usuário: ${formData.owner_username}\n`;
      mensagem += `• Email: ${formData.owner_email}\n`;
      
      mensagem += `\n💡 O proprietário pode alterar a senha no primeiro acesso.`;
      mensagem += `\n\n⚠️ IMPORTANTE: Use o botão "Criar Banco" na lista de lojas para criar o banco de dados isolado.`;
      
      alert(mensagem);
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Erro completo ao criar loja:', error);
      console.error('Response data:', error.response?.data);
      
      let mensagemErro = '❌ Erro ao criar loja:\n\n';
      
      if (error.response?.data) {
        // Se for um objeto com erros de validação
        if (typeof error.response.data === 'object') {
          Object.entries(error.response.data).forEach(([campo, erros]: [string, any]) => {
            if (Array.isArray(erros)) {
              mensagemErro += `• ${campo}: ${erros.join(', ')}\n`;
            } else {
              mensagemErro += `• ${campo}: ${erros}\n`;
            }
          });
        } else {
          mensagemErro += error.response.data;
        }
      } else {
        mensagemErro += 'Erro desconhecido ao criar loja';
      }
      
      alert(mensagemErro);
    } finally {
      setLoading(false);
    }
  };

  const planoSelecionado = planos.find(p => p.id === parseInt(formData.plano));
  const valorAssinatura = planoSelecionado 
    ? (formData.tipo_assinatura === 'anual' 
        ? planoSelecionado.preco_anual 
        : planoSelecionado.preco_mensal)
    : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full h-full max-w-7xl max-h-[95vh] flex flex-col">
        {/* Header fixo */}
        <div className="flex items-center justify-between p-6 border-b bg-purple-900 text-white rounded-t-lg">
          <h2 className="text-2xl font-bold">Nova Loja</h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-2xl font-bold"
          >
            ×
          </button>
        </div>
        
        {/* Conteúdo com scroll */}
        <div className="flex-1 overflow-y-auto p-6">
          <form id="form-nova-loja" onSubmit={handleSubmit} className="space-y-6">
            {/* Seção 1: Informações Básicas */}
            <div className="border-b pb-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-700">1. Informações Básicas</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome da Loja *
                  </label>
                  <input
                    type="text"
                    name="nome"
                    value={formData.nome}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Ex: Minha Loja Tech"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Slug (URL) *
                  </label>
                  <input
                    type="text"
                    name="slug"
                    value={formData.slug}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="minha-loja-tech"
                  />
                  <p className="text-xs text-gray-500 mt-1">URL: /loja/{formData.slug}/login</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CPF ou CNPJ *
                  </label>
                  <input
                    type="text"
                    name="cpf_cnpj"
                    value={formData.cpf_cnpj}
                    onChange={handleCpfCnpjChange}
                    required
                    maxLength={18}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="000.000.000-00 ou 00.000.000/0000-00"
                  />
                </div>

                <div className="md:col-span-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Descrição
                  </label>
                  <textarea
                    name="descricao"
                    value={formData.descricao}
                    onChange={handleChange}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Descrição da loja..."
                  />
                </div>
              </div>
            </div>

            {/* Seção 2: Tipo de Loja */}
            <div className="border-b pb-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-700">2. Tipo de Loja</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selecione o tipo *
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {tipos.map((tipo) => (
                  <label
                    key={tipo.id}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                      formData.tipo_loja === tipo.id.toString()
                        ? 'border-purple-600 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="tipo_loja"
                      value={tipo.id}
                      checked={formData.tipo_loja === tipo.id.toString()}
                      onChange={handleChange}
                      className="sr-only"
                    />
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">{tipo.nome}</span>
                      <div
                        className="w-6 h-6 rounded-full"
                        style={{ backgroundColor: tipo.cor_primaria }}
                      />
                    </div>
                    <p className="text-sm text-gray-600">{tipo.descricao}</p>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Seção 3: Plano e Assinatura */}
          <div className="border-b pb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">3. Plano e Assinatura</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Selecione o plano *
                </label>
                {!formData.tipo_loja ? (
                  <div className="text-center py-8 text-gray-500">
                    Selecione um tipo de loja primeiro para ver os planos disponíveis
                  </div>
                ) : planos.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    Nenhum plano disponível para este tipo de loja
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {planos.map((plano) => (
                      <label
                        key={plano.id}
                        className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                          formData.plano === plano.id.toString()
                            ? 'border-purple-600 bg-purple-50'
                            : 'border-gray-200 hover:border-purple-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="plano"
                          value={plano.id}
                          checked={formData.plano === plano.id.toString()}
                          onChange={handleChange}
                          className="sr-only"
                        />
                        <div className="text-center">
                          <h4 className="font-bold text-lg mb-2">{plano.nome}</h4>
                          <p className="text-2xl font-bold text-purple-600 mb-2">
                            R$ {plano.preco_mensal}
                          </p>
                          <p className="text-sm text-gray-600">por mês</p>
                          {plano.preco_anual && (
                            <p className="text-xs text-gray-500 mt-1">
                              ou R$ {plano.preco_anual}/ano
                            </p>
                          )}
                          <p className="text-xs text-gray-600 mt-2 line-clamp-2">
                            {plano.descricao}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Assinatura *
                  </label>
                  <select
                    name="tipo_assinatura"
                    value={formData.tipo_assinatura}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  >
                    <option value="mensal">Mensal</option>
                    <option value="anual">Anual</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dia de Vencimento *
                  </label>
                  <select
                    name="dia_vencimento"
                    value={formData.dia_vencimento}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  >
                    {Array.from({ length: 28 }, (_, i) => i + 1).map(dia => (
                      <option key={dia} value={dia}>Dia {dia}</option>
                    ))}
                  </select>
                </div>
              </div>

              {valorAssinatura > 0 && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-purple-900">
                    Valor da assinatura: <span className="text-xl">R$ {valorAssinatura}</span>
                    {formData.tipo_assinatura === 'anual' && ' (pagamento anual)'}
                  </p>
                  <p className="text-xs text-purple-700 mt-1">
                    Vencimento todo dia {formData.dia_vencimento} do mês
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Seção 4: Usuário Administrador */}
          <div className="border-b pb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">4. Usuário Administrador da Loja</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome de Usuário *
                </label>
                <input
                  type="text"
                  name="owner_username"
                  value={formData.owner_username}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="admin_loja"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Senha Provisória *
                </label>
                <div className="flex gap-2">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      name="owner_password"
                      value={formData.owner_password}
                      onChange={handleChange}
                      required
                      minLength={6}
                      readOnly
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md bg-gray-50 focus:ring-purple-500 focus:border-purple-500 font-mono"
                      placeholder="Gerando..."
                    />
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(formData.owner_password);
                        alert('✅ Senha copiada para a área de transferência!');
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-purple-600"
                      title="Copiar senha"
                    >
                      📋
                    </button>
                  </div>
                  <button
                    type="button"
                    onClick={gerarSenhaProvisoria}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 whitespace-nowrap"
                    title="Gerar nova senha"
                  >
                    🔄 Gerar Nova
                  </button>
                </div>
                <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
                  <span>✅</span>
                  <span>Esta senha será enviada por email para o proprietário</span>
                </p>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  E-mail *
                </label>
                <input
                  type="email"
                  name="owner_email"
                  value={formData.owner_email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="admin@loja.com"
                />
              </div>
            </div>
          </div>

          {/* Resumo */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-700">Resumo</h3>
            <div className="space-y-2 text-sm">
              <p>✅ <strong>Loja:</strong> {formData.nome || '(não informado)'}</p>
              <p>✅ <strong>Tipo:</strong> {tipos.find(t => t.id.toString() === formData.tipo_loja)?.nome || '(não selecionado)'}</p>
              <p>✅ <strong>Plano:</strong> {planos.find(p => p.id.toString() === formData.plano)?.nome || '(não selecionado)'}</p>
              <p>✅ <strong>Assinatura:</strong> {formData.tipo_assinatura === 'mensal' ? 'Mensal' : 'Anual'}</p>
              <p>✅ <strong>Vencimento:</strong> Dia {formData.dia_vencimento}</p>
              <p>✅ <strong>Email:</strong> {formData.owner_email || '(não informado)'}</p>
              <p>✅ <strong>Senha Provisória:</strong> {formData.owner_password ? <span className="font-mono text-purple-600">{formData.owner_password}</span> : 'Gerando...'}</p>
              <p>✅ <strong>Dashboard de Suporte:</strong> Vinculado automaticamente</p>
              <p>✅ <strong>Página de Login:</strong> /loja/{formData.slug}/login (personalizada)</p>
              <p>✅ <strong>Banco de Dados:</strong> Será criado automaticamente (isolado)</p>
              <p>✅ <strong>Email de Boas-vindas:</strong> Será enviado com dados de acesso</p>
            </div>
          </div>
        </form>
        </div>
        
        {/* Footer fixo */}
        <div className="border-t p-6 bg-gray-50">
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              form="form-nova-loja"
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Criando...' : 'Criar Loja'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Modal de Edição de Loja
function ModalEditarLoja({ 
  loja, 
  onClose, 
  onSuccess 
}: { 
  loja: Loja; 
  onClose: () => void; 
  onSuccess: () => void; 
}) {
  const [formData, setFormData] = useState({
    nome: loja.nome,
    is_active: loja.is_active,
    is_trial: loja.is_trial
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiClient.patch(`/superadmin/lojas/${loja.id}/`, formData);
      alert('✅ Loja atualizada com sucesso!');
      onSuccess();
    } catch (error: any) {
      console.error('Erro ao atualizar loja:', error);
      alert(`❌ Erro ao atualizar loja: ${error.response?.data?.error || 'Erro desconhecido'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6 text-purple-600">
          ✏️ Editar Loja - {loja.nome}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Informações Básicas */}
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Informações Básicas</h4>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome da Loja *
                </label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                    Loja Ativa
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_trial"
                    checked={formData.is_trial}
                    onChange={(e) => setFormData({ ...formData, is_trial: e.target.checked })}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_trial" className="ml-2 block text-sm text-gray-700">
                    Período Trial
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Informações Somente Leitura */}
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Informações (Somente Leitura)</h4>
            <div className="bg-gray-50 p-4 rounded-md space-y-2 text-sm">
              <p><strong>Slug:</strong> {loja.slug}</p>
              <p><strong>Tipo:</strong> {loja.tipo_loja_nome}</p>
              <p><strong>Plano:</strong> {loja.plano_nome}</p>
              <p><strong>Proprietário:</strong> {loja.owner_username} ({loja.owner_email})</p>
              <p><strong>Banco Criado:</strong> {loja.database_created ? '✅ Sim' : '❌ Não'}</p>
              <p><strong>URL Login:</strong> <a href={loja.login_page_url} target="_blank" className="text-purple-600 hover:underline">{loja.login_page_url}</a></p>
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
            >
              {loading ? 'Salvando...' : 'Salvar Alterações'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Modal de Confirmação de Exclusão
function ModalExcluirLoja({ 
  loja, 
  onClose, 
  onConfirm 
}: { 
  loja: Loja; 
  onClose: () => void; 
  onConfirm: () => void; 
}) {
  const [confirmacaoTexto, setConfirmacaoTexto] = useState('');
  const [loading, setLoading] = useState(false);

  const temBancoCriado = loja.database_created;
  const textoConfirmacao = 'EXCLUIR';
  const confirmacaoCorreta = confirmacaoTexto === textoConfirmacao;

  const handleConfirmar = async () => {
    if (!confirmacaoCorreta) return;
    
    setLoading(true);
    await onConfirm();
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <div className="text-center mb-6">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 15.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Excluir Loja
          </h3>
          <p className="text-sm text-gray-500">
            Você está prestes a excluir a loja <strong>"{loja.nome}"</strong>
          </p>
        </div>

        <div className="mb-6">
          <div className={`border rounded-md p-4 mb-4 ${temBancoCriado ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'}`}>
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className={`h-5 w-5 ${temBancoCriado ? 'text-red-400' : 'text-yellow-400'}`} viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className={`text-sm font-medium ${temBancoCriado ? 'text-red-800' : 'text-yellow-800'}`}>
                  {temBancoCriado ? '🔥 EXCLUSÃO TOTAL - Banco de Dados Será Deletado!' : '⚠️ EXCLUSÃO COMPLETA - Esta ação é irreversível'}
                </h3>
                <div className={`mt-2 text-sm ${temBancoCriado ? 'text-red-700' : 'text-yellow-700'}`}>
                  <p className="font-medium mb-2">Será removido PERMANENTEMENTE:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li><strong>Loja completa</strong> - Todos os dados e configurações</li>
                    {temBancoCriado && (
                      <>
                        <li className="text-red-800 font-bold">🗄️ Banco de dados isolado - Arquivo físico será DELETADO</li>
                        <li><strong>Usuários e funcionários</strong> - Todos os acessos da loja</li>
                        <li><strong>Produtos e serviços</strong> - Todo o catálogo</li>
                        <li><strong>Pedidos e vendas</strong> - Histórico completo</li>
                      </>
                    )}
                    <li><strong>Dados financeiros</strong> - Assinatura e pagamentos</li>
                    <li><strong>Usuário proprietário</strong> - Será removido se não tiver outras lojas</li>
                    <li><strong>Configurações personalizadas</strong> - Cores, logos, etc.</li>
                  </ul>
                  <p className="font-bold mt-3 text-red-800">
                    ⚠️ IMPOSSÍVEL RECUPERAR após a exclusão!
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Para confirmar, digite <strong className="text-red-600">{textoConfirmacao}</strong>:
            </label>
            <input
              type="text"
              value={confirmacaoTexto}
              onChange={(e) => setConfirmacaoTexto(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
              placeholder={textoConfirmacao}
              autoFocus
            />
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirmar}
            disabled={!confirmacaoCorreta || loading}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Excluindo...' : 'Excluir Loja Permanentemente'}
          </button>
        </div>
      </div>
    </div>
  );
}
