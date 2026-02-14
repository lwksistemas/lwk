'use client';

import { useState } from 'react';
import apiClient from '@/lib/api-client';

interface Loja {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  plano_nome: string;
  owner_username: string;
  owner_email: string;
  owner_telefone?: string;
  is_active: boolean;
  is_trial: boolean;
  database_created: boolean;
  login_page_url: string;
}

interface ModalEditarLojaProps {
  loja: Loja;
  onClose: () => void;
  onSuccess: () => void;
}

export function ModalEditarLoja({ loja, onClose, onSuccess }: ModalEditarLojaProps) {
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

          {/* Informações Somente Leitura — administrador da loja não pode ser editado nem excluído */}
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Informações (Somente Leitura)</h4>
            <div className="bg-gray-50 p-4 rounded-md space-y-2 text-sm">
              <p><strong>Slug:</strong> {loja.slug}</p>
              <p><strong>Tipo:</strong> {loja.tipo_loja_nome}</p>
              <p><strong>Plano:</strong> {loja.plano_nome}</p>
              <p><strong>Usuário Administrador da Loja:</strong> {loja.owner_username} ({loja.owner_email}){loja.owner_telefone ? ` · Tel: ${loja.owner_telefone}` : ''}</p>
              <p className="text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded mt-1">O administrador vinculado à loja não pode ser editado nem excluído.</p>
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
