'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import apiClient from '@/lib/api-client';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface Funcionario {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  cargo: string;
  funcao: string;
  funcao_display?: string;
  especialidade?: string;
  is_active: boolean;
  is_admin?: boolean;
}

interface ModalFuncionariosProps {
  loja: LojaInfo;
  onClose: () => void;
}

export function ModalFuncionarios({ loja, onClose }: ModalFuncionariosProps) {
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Funcionario | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    telefone: '',
    email: '',
    cargo: '',
    funcao: 'atendente',
    is_active: true
  });

  useEffect(() => {
    carregarFuncionarios();
  }, []);

  const carregarFuncionarios = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/clinica/funcionarios/');
      const data = extractArrayData<Funcionario>(response);
      console.log('Funcionários carregados:', data);
      setFuncionarios(data);
    } catch (error) {
      console.error('Erro ao carregar funcionários:', error);
      alert(formatApiError(error));
      setFuncionarios([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const payload = {
        nome: formData.nome,
        telefone: formData.telefone,
        email: formData.email || null,
        cargo: formData.cargo,
        funcao: formData.funcao,
        data_admissao: new Date().toISOString().split('T')[0],
        is_active: formData.is_active
      };

      if (editando) {
        await apiClient.put(`/clinica/funcionarios/${editando.id}/`, payload);
      } else {
        await apiClient.post('/clinica/funcionarios/', payload);
      }
      
      await carregarFuncionarios();
      setFormData({ nome: '', telefone: '', email: '', cargo: '', funcao: 'atendente', is_active: true });
      setEditando(null);
      setShowForm(false);
    } catch (error) {
      console.error('Erro ao salvar funcionário:', error);
      alert(formatApiError(error));
    }
  };

  const handleEditar = (funcionario: Funcionario) => {
    // 🛡️ PROTEÇÃO: Não permitir editar administrador
    if (funcionario.is_admin) {
      alert('⚠️ O administrador da loja não pode ser editado por aqui.\n\nPara alterar dados do administrador, acesse as configurações da loja no painel do SuperAdmin.');
      return;
    }
    
    setFormData({
      nome: funcionario.nome,
      telefone: funcionario.telefone,
      email: funcionario.email || '',
      cargo: funcionario.cargo || '',
      funcao: funcionario.funcao || 'atendente',
      is_active: funcionario.is_active
    });
    setEditando(funcionario);
    setShowForm(true);
  };

  const handleExcluir = async (id: number, nome: string, is_admin?: boolean) => {
    // 🛡️ PROTEÇÃO: Não permitir excluir administrador
    if (is_admin) {
      alert('⚠️ O administrador da loja não pode ser excluído.\n\nO administrador é vinculado automaticamente ao criar a loja.');
      return;
    }
    
    if (!confirm(`Deseja excluir o funcionário "${nome}"?`)) return;
    
    try {
      await apiClient.delete(`/clinica/funcionarios/${id}/`);
      await carregarFuncionarios();
    } catch (error) {
      console.error('Erro ao excluir funcionário:', error);
      alert(formatApiError(error));
    }
  };

  const handleNovo = () => {
    setFormData({ nome: '', telefone: '', email: '', cargo: '', funcao: 'atendente', is_active: true });
    setEditando(null);
    setShowForm(true);
  };

  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="2xl">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ color: loja.cor_primaria }}>
            👥 {editando ? 'Editar Funcionário' : 'Novo Funcionário'}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome Completo *
                </label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Telefone *
                </label>
                <input
                  type="tel"
                  value={formData.telefone}
                  onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Cargo *
                </label>
                <input
                  type="text"
                  value={formData.cargo}
                  onChange={(e) => setFormData({ ...formData, cargo: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  placeholder="Ex: Gerente, Recepcionista, Caixa..."
                  required
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  ⚠️ Não cadastre profissionais aqui (use o botão "Profissional")
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Função/Permissão *
                </label>
                <select
                  value={formData.funcao}
                  onChange={(e) => setFormData({ ...formData, funcao: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  required
                >
                  <option value="administrador">Administrador</option>
                  <option value="gerente">Gerente</option>
                  <option value="atendente">Atendente/Recepcionista</option>
                  <option value="caixa">Caixa</option>
                  <option value="visualizador">Visualizador</option>
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  💡 Para cadastrar profissionais (esteticistas), use o botão "Profissional"
                </p>
              </div>

              <div className="md:col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Funcionário ativo</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => { setShowForm(false); setEditando(null); }}
                className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]"
                style={{ backgroundColor: loja.cor_primaria }}
              >
                {editando ? 'Atualizar' : 'Criar'}
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: loja.cor_primaria }}>
            👥 Gerenciar Funcionários
          </h2>
          <button
            onClick={handleNovo}
            className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo Funcionário
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : funcionarios.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-3xl">👥</span>
            </div>
            <p className="text-lg mb-2 text-gray-700 dark:text-gray-300">Nenhum funcionário cadastrado</p>
            <p className="text-sm mb-4 text-gray-500 dark:text-gray-400">Comece adicionando seu primeiro funcionário</p>
            <button
              onClick={handleNovo}
              className="px-6 py-3 text-white rounded-lg hover:opacity-90 min-h-[44px]"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Adicionar Primeiro Funcionário
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-3 mb-6 max-h-[60vh] overflow-y-auto">
              {funcionarios.map((funcionario) => (
                <div key={funcionario.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-lg text-gray-900 dark:text-white">{funcionario.nome}</p>
                      {funcionario.is_active ? (
                        <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs font-semibold rounded-full">Ativo</span>
                      ) : (
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 text-xs font-semibold rounded-full">Inativo</span>
                      )}
                      {funcionario.is_admin && (
                        <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">Admin</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      💼 {funcionario.cargo} • 🔑 {funcionario.funcao_display || funcionario.funcao}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      📱 {funcionario.telefone || 'Sem telefone'} {funcionario.email && `• ✉️ ${funcionario.email}`}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleEditar(funcionario)} 
                      className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px] disabled:opacity-50 disabled:cursor-not-allowed" 
                      style={{ backgroundColor: loja.cor_primaria }}
                      disabled={funcionario.is_admin}
                    >
                      ✏️ Editar
                    </button>
                    <button 
                      onClick={() => handleExcluir(funcionario.id, funcionario.nome, funcionario.is_admin)} 
                      className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px] disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={funcionario.is_admin}
                    >
                      🗑️ Excluir
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
              <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Fechar</button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
