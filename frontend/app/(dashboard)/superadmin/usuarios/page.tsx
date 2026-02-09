'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface Usuario {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
  };
  tipo: string;
  tipo_display: string;
  cpf: string;
  telefone: string;
  foto: string;
  pode_criar_lojas: boolean;
  pode_gerenciar_financeiro: boolean;
  pode_acessar_todas_lojas: boolean;
  is_active: boolean;
  created_at: string;
}

export default function UsuariosPage() {
  const router = useRouter();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editandoUsuario, setEditandoUsuario] = useState<Usuario | null>(null);
  const [filtroTipo, setFiltroTipo] = useState<string>('todos');

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadUsuarios();
  }, [router]);

  const loadUsuarios = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/superadmin/usuarios/');
      const data = response.data.results || response.data;
      setUsuarios(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Erro ao carregar usuários:', error);
      setUsuarios([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleUsuarioStatus = async (usuario: Usuario) => {
    const novoStatus = !usuario.is_active;
    const acao = novoStatus ? 'ativar' : 'desativar';
    
    if (!confirm(`Deseja ${acao} o usuário ${usuario.user.username}?`)) return;

    try {
      await apiClient.patch(`/superadmin/usuarios/${usuario.id}/`, {
        is_active: novoStatus
      });
      alert(`✅ Usuário ${novoStatus ? 'ativado' : 'desativado'} com sucesso!`);
      loadUsuarios();
    } catch (error: any) {
      console.error('Erro ao alterar status:', error);
      alert(`❌ Erro: ${error.response?.data?.error || 'Erro ao alterar status'}`);
    }
  };

  const handleEditar = (usuario: Usuario) => {
    setEditandoUsuario(usuario);
    setShowModal(true);
  };

  const handleExcluir = async (usuario: Usuario) => {
    if (!confirm(`⚠️ ATENÇÃO!\n\nDeseja realmente EXCLUIR o usuário ${usuario.user.username}?\n\nEsta ação NÃO pode ser desfeita!`)) return;

    try {
      await apiClient.delete(`/superadmin/usuarios/${usuario.id}/`);
      alert('✅ Usuário excluído com sucesso!');
      loadUsuarios();
    } catch (error: any) {
      console.error('Erro ao excluir usuário:', error);
      alert(`❌ Erro: ${error.response?.data?.error || 'Erro ao excluir usuário'}`);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getTipoColor = (tipo: string) => {
    return tipo === 'superadmin' 
      ? 'bg-purple-100 text-purple-800' 
      : 'bg-blue-100 text-blue-800';
  };

  const getTipoIcon = (tipo: string) => {
    return tipo === 'superadmin' ? '👑' : '🛠️';
  };

  const usuariosFiltrados = filtroTipo === 'todos' 
    ? usuarios 
    : usuarios.filter(u => u.tipo === filtroTipo);

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
              <h1 className="text-2xl font-bold">Usuários do Sistema</h1>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
            >
              + Novo Usuário
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
                  <p className="text-sm text-gray-600">Total de Usuários</p>
                  <p className="text-2xl font-bold text-purple-600">{usuarios.length}</p>
                </div>
                <div className="text-3xl">👥</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Super Admins</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {usuarios.filter(u => u.tipo === 'superadmin').length}
                  </p>
                </div>
                <div className="text-3xl">👑</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Suporte</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {usuarios.filter(u => u.tipo === 'suporte').length}
                  </p>
                </div>
                <div className="text-3xl">🛠️</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Ativos</p>
                  <p className="text-2xl font-bold text-green-600">
                    {usuarios.filter(u => u.is_active).length}
                  </p>
                </div>
                <div className="text-3xl">✅</div>
              </div>
            </div>
          </div>

          {/* Filtros */}
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-700">Filtrar por tipo:</span>
              <div className="flex space-x-2">
                {['todos', 'superadmin', 'suporte'].map((tipo) => (
                  <button
                    key={tipo}
                    onClick={() => setFiltroTipo(tipo)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      filtroTipo === tipo
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {tipo === 'todos' ? 'Todos' : tipo === 'superadmin' ? 'Super Admin' : 'Suporte'}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Tabela de Usuários */}
          {loading ? (
            <div className="text-center py-12">Carregando...</div>
          ) : usuariosFiltrados.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500 mb-4">
                {filtroTipo === 'todos' 
                  ? 'Nenhum usuário cadastrado ainda.' 
                  : `Nenhum usuário do tipo "${filtroTipo}".`
                }
              </p>
              <button
                onClick={() => setShowModal(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
              >
                Criar Primeiro Usuário
              </button>
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Usuário
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Permissões
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Cadastro
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {usuariosFiltrados.map((usuario) => (
                    <tr key={usuario.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
                              <span className="text-purple-600 font-medium text-lg">
                                {usuario.user.username.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="font-medium text-gray-900">
                              {usuario.user.first_name || usuario.user.username}
                            </div>
                            <div className="text-sm text-gray-500">{usuario.user.email}</div>
                            {usuario.telefone && (
                              <div className="text-xs text-gray-400">{usuario.telefone}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTipoColor(usuario.tipo)}`}>
                          <span className="mr-1">{getTipoIcon(usuario.tipo)}</span>
                          {usuario.tipo_display}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {usuario.pode_criar_lojas && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              Criar Lojas
                            </span>
                          )}
                          {usuario.pode_gerenciar_financeiro && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                              Financeiro
                            </span>
                          )}
                          {usuario.pode_acessar_todas_lojas && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                              Todas Lojas
                            </span>
                          )}
                          {!usuario.pode_criar_lojas && !usuario.pode_gerenciar_financeiro && !usuario.pode_acessar_todas_lojas && (
                            <span className="text-xs text-gray-400">Sem permissões extras</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            usuario.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {usuario.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDate(usuario.created_at)}
                      </td>
                      <td className="px-6 py-4 text-sm space-x-2">
                        <button 
                          onClick={() => handleEditar(usuario)}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          ✏️ Editar
                        </button>
                        <button
                          onClick={() => toggleUsuarioStatus(usuario)}
                          className={`font-medium ${usuario.is_active ? 'text-orange-600 hover:text-orange-800' : 'text-green-600 hover:text-green-800'}`}
                        >
                          {usuario.is_active ? '⏸️ Desativar' : '▶️ Ativar'}
                        </button>
                        <button
                          onClick={() => handleExcluir(usuario)}
                          className="text-red-600 hover:text-red-800 font-medium"
                        >
                          🗑️ Excluir
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

      {/* Modal Novo/Editar Usuário */}
      {showModal && (
        <NovoUsuarioModal 
          usuario={editandoUsuario}
          onClose={() => {
            setShowModal(false);
            setEditandoUsuario(null);
          }} 
          onSuccess={() => {
            loadUsuarios();
            setEditandoUsuario(null);
          }} 
        />
      )}
    </div>
  );
}

// Modal de Novo/Editar Usuário
function NovoUsuarioModal({ usuario, onClose, onSuccess }: { usuario?: Usuario | null; onClose: () => void; onSuccess: () => void }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: usuario?.user.username || '',
    email: usuario?.user.email || '',
    password: '', // Só usado ao editar
    first_name: usuario?.user.first_name || '',
    last_name: usuario?.user.last_name || '',
    tipo: usuario?.tipo || 'suporte',
    cpf: usuario?.cpf || '',
    telefone: usuario?.telefone || '',
    pode_criar_lojas: usuario?.pode_criar_lojas || false,
    pode_gerenciar_financeiro: usuario?.pode_gerenciar_financeiro || false,
    pode_acessar_todas_lojas: usuario?.pode_acessar_todas_lojas || false,
  });

  const isEditing = !!usuario;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Função para formatar CPF automaticamente
  const formatarCpf = (valor: string) => {
    const numeros = valor.replace(/\D/g, '');
    const limitado = numeros.slice(0, 11);
    return limitado
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  };

  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const valorFormatado = formatarCpf(e.target.value);
    setFormData(prev => ({ ...prev, cpf: valorFormatado }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload: any = {
        tipo: formData.tipo,
        cpf: formData.cpf,
        telefone: formData.telefone,
        pode_criar_lojas: formData.pode_criar_lojas,
        pode_gerenciar_financeiro: formData.pode_gerenciar_financeiro,
        pode_acessar_todas_lojas: formData.pode_acessar_todas_lojas,
      };

      // Dados do usuário Django
      const userData: any = {
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
      };

      // Ao criar: incluir username (obrigatório)
      if (!isEditing) {
        userData.username = formData.username;
      }

      // Ao editar: só incluir senha se foi preenchida
      if (isEditing && formData.password) {
        userData.password = formData.password;
      }

      payload.user = userData;

      if (isEditing && usuario) {
        // Atualizar usuário existente
        await apiClient.put(`/superadmin/usuarios/${usuario.id}/`, payload);
        alert('✅ Usuário atualizado com sucesso!');
      } else {
        // Criar novo usuário (senha provisória gerada automaticamente)
        const response = await apiClient.post('/superadmin/usuarios/', payload);
        const senhaProvisoria = response.data.senha_provisoria;
        alert(`✅ Usuário criado com sucesso!\n\n📧 Senha provisória enviada para: ${formData.email}\n🔐 Senha: ${senhaProvisoria}\n\n⚠️ O usuário deverá trocar a senha no primeiro acesso.`);
      }

      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Erro ao salvar usuário:', error);
      alert(`❌ Erro: ${error.response?.data?.error || JSON.stringify(error.response?.data) || 'Erro ao salvar usuário'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6 text-purple-900">
          {isEditing ? '✏️ Editar Usuário' : '➕ Novo Usuário do Sistema'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Informações Básicas */}
          <div className="border-b pb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Informações Básicas</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome de Usuário *
                </label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  disabled={isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  placeholder="usuario123"
                />
                {isEditing && (
                  <p className="text-xs text-gray-500 mt-1">Nome de usuário não pode ser alterado</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="usuario@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome
                </label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="João"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sobrenome
                </label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Silva"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CPF *
                </label>
                <input
                  type="text"
                  name="cpf"
                  value={formData.cpf}
                  onChange={handleCpfChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="000.000.000-00"
                  maxLength={14}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone
                </label>
                <input
                  type="text"
                  name="telefone"
                  value={formData.telefone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="(11) 99999-9999"
                />
              </div>

              {/* Campo de senha só aparece ao editar */}
              {isEditing && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nova Senha (opcional)
                  </label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    minLength={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Deixe em branco para manter a atual"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Deixe em branco para não alterar a senha
                  </p>
                </div>
              )}
            </div>

            {/* Aviso sobre senha provisória ao criar */}
            {!isEditing && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>ℹ️ Senha Provisória:</strong> Uma senha será gerada automaticamente e enviada para o email do usuário. O usuário deverá trocar a senha no primeiro acesso.
                </p>
              </div>
            )}
          </div>

          {/* Tipo e Permissões */}
          <div className="border-b pb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Tipo e Permissões</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Usuário *
              </label>
              <select
                name="tipo"
                value={formData.tipo}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="suporte">Suporte</option>
                <option value="superadmin">Super Admin</option>
              </select>
            </div>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="pode_criar_lojas"
                  checked={formData.pode_criar_lojas}
                  onChange={handleChange}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Pode criar lojas</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="pode_gerenciar_financeiro"
                  checked={formData.pode_gerenciar_financeiro}
                  onChange={handleChange}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Pode gerenciar financeiro</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="pode_acessar_todas_lojas"
                  checked={formData.pode_acessar_todas_lojas}
                  onChange={handleChange}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Pode acessar todas as lojas</span>
              </label>
            </div>
          </div>

          {/* Botões */}
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
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (isEditing ? 'Atualizando...' : 'Criando...') : (isEditing ? 'Atualizar Usuário' : 'Criar Usuário')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
