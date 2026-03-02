'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { useUsuarioList } from '@/hooks/useUsuarioList';
import { useUsuarioActions, Usuario } from '@/hooks/useUsuarioActions';
import { UsuarioCard, UsuarioModal } from '@/components/superadmin/usuarios';

export default function UsuariosPage() {
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);
  const [editandoUsuario, setEditandoUsuario] = useState<Usuario | null>(null);
  const [filtroTipo, setFiltroTipo] = useState<string>('todos');

  const { usuarios, loading, reload } = useUsuarioList();
  const { criarUsuario, atualizarUsuario, excluirUsuario, toggleStatus, loading: actionLoading } = useUsuarioActions();

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
    }
  }, [router]);

  const handleEdit = (usuario: Usuario) => {
    setEditandoUsuario(usuario);
    setShowModal(true);
  };

  const handleDelete = async (usuario: Usuario) => {
    if (!confirm(`⚠️ ATENÇÃO!\n\nDeseja realmente EXCLUIR o usuário ${usuario.user.username}?\n\nEsta ação NÃO pode ser desfeita!`)) {
      return;
    }

    try {
      await excluirUsuario(usuario);
      alert('✅ Usuário excluído com sucesso!');
      reload();
    } catch (error: any) {
      alert(`❌ ${error.message}`);
    }
  };

  const handleToggleStatus = async (usuario: Usuario) => {
    const novoStatus = !usuario.is_active;
    const acao = novoStatus ? 'ativar' : 'desativar';
    
    if (!confirm(`Deseja ${acao} o usuário ${usuario.user.username}?`)) {
      return;
    }

    try {
      await toggleStatus(usuario);
      alert(`✅ Usuário ${novoStatus ? 'ativado' : 'desativado'} com sucesso!`);
      reload();
    } catch (error: any) {
      alert(`❌ ${error.message}`);
    }
  };

  const handleSubmit = async (data: any) => {
    try {
      if (editandoUsuario) {
        await atualizarUsuario(editandoUsuario.id, data);
        alert('✅ Usuário atualizado com sucesso!');
      } else {
        const response = await criarUsuario(data);
        const senhaProvisoria = response.senha_provisoria;
        alert(`✅ Usuário criado com sucesso!\n\n📧 Senha provisória enviada para: ${data.email}\n🔐 Senha: ${senhaProvisoria}\n\n⚠️ O usuário deverá trocar a senha no primeiro acesso.`);
      }
      reload();
      setShowModal(false);
      setEditandoUsuario(null);
    } catch (error: any) {
      alert(`❌ ${error.message}`);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditandoUsuario(null);
  };

  const usuariosFiltrados = filtroTipo === 'todos' 
    ? usuarios 
    : usuarios.filter(u => u.tipo === filtroTipo);

  const stats = {
    total: usuarios.length,
    superadmins: usuarios.filter(u => u.tipo === 'superadmin').length,
    suporte: usuarios.filter(u => u.tipo === 'suporte').length,
    ativos: usuarios.filter(u => u.is_active).length,
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
                  <p className="text-2xl font-bold text-purple-600">{stats.total}</p>
                </div>
                <div className="text-3xl">👥</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Super Admins</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.superadmins}</p>
                </div>
                <div className="text-3xl">👑</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Suporte</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.suporte}</p>
                </div>
                <div className="text-3xl">🛠️</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Ativos</p>
                  <p className="text-2xl font-bold text-green-600">{stats.ativos}</p>
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

          {/* Lista de Usuários */}
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {usuariosFiltrados.map((usuario) => (
                <UsuarioCard
                  key={usuario.id}
                  usuario={usuario}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onToggleStatus={handleToggleStatus}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Modal */}
      {showModal && (
        <UsuarioModal
          usuario={editandoUsuario}
          onClose={handleCloseModal}
          onSubmit={handleSubmit}
          loading={actionLoading}
        />
      )}
    </div>
  );
}
