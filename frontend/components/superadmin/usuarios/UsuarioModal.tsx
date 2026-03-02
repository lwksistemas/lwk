'use client';

import { useState } from 'react';
import { Usuario, UsuarioFormData } from '@/hooks/useUsuarioActions';

interface UsuarioModalProps {
  usuario?: Usuario | null;
  onClose: () => void;
  onSubmit: (data: UsuarioFormData) => Promise<any>;
  loading: boolean;
}

export function UsuarioModal({ usuario, onClose, onSubmit, loading }: UsuarioModalProps) {
  const [formData, setFormData] = useState<UsuarioFormData>({
    username: usuario?.user.username || '',
    email: usuario?.user.email || '',
    password: '',
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
    await onSubmit(formData);
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
            </div>
          </div>

          {/* Tipo e Senha */}
          <div className="border-b pb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Acesso</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Usuário *
                </label>
                <select
                  name="tipo"
                  value={formData.tipo}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="suporte">🛠️ Suporte</option>
                  <option value="superadmin">👑 Super Admin</option>
                </select>
              </div>

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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Deixe em branco para manter"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Preencha apenas se quiser alterar a senha
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Permissões */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Permissões</h3>
            <div className="space-y-3">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  name="pode_criar_lojas"
                  checked={formData.pode_criar_lojas}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">🏪 Pode Criar Lojas</span>
                  <p className="text-xs text-gray-500">Permite criar novas lojas no sistema</p>
                </div>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  name="pode_gerenciar_financeiro"
                  checked={formData.pode_gerenciar_financeiro}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">💰 Pode Gerenciar Financeiro</span>
                  <p className="text-xs text-gray-500">Acesso ao módulo financeiro</p>
                </div>
              </label>

              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  name="pode_acessar_todas_lojas"
                  checked={formData.pode_acessar_todas_lojas}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">🌐 Pode Acessar Todas as Lojas</span>
                  <p className="text-xs text-gray-500">Acesso irrestrito a todas as lojas</p>
                </div>
              </label>
            </div>
          </div>

          {/* Botões */}
          <div className="flex justify-end space-x-4 pt-4">
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
              {loading ? (isEditing ? 'Salvando...' : 'Criando...') : (isEditing ? 'Salvar Alterações' : 'Criar Usuário')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
