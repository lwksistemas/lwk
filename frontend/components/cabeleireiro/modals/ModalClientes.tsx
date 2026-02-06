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

interface Cliente {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  data_nascimento?: string;
  observacoes?: string;
}

export function ModalClientes({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Cliente | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    telefone: '',
    email: '',
    data_nascimento: '',
    observacoes: ''
  });

  useEffect(() => {
    carregarClientes();
  }, []);

  const carregarClientes = async () => {
    try {
      setLoading(true);
      
      // Debug: verificar headers
      const lojaId = sessionStorage.getItem('current_loja_id');
      const lojaSlug = sessionStorage.getItem('loja_slug');
      console.log('🔍 DEBUG - Carregando clientes:');
      console.log('  - Loja ID:', lojaId);
      console.log('  - Loja Slug:', lojaSlug);
      console.log('  - Loja prop:', loja);
      
      const response = await apiClient.get('/cabeleireiro/clientes/');
      
      // Debug: verificar resposta completa
      console.log('📦 Resposta completa:', response);
      console.log('📦 response.data:', response.data);
      console.log('📦 Tipo de response.data:', typeof response.data);
      console.log('📦 É array?', Array.isArray(response.data));
      
      // Extrair array de forma segura
      const data = extractArrayData<Cliente>(response);
      console.log('✅ Clientes extraídos:', data);
      console.log('✅ Quantidade:', data.length);
      
      setClientes(data);
    } catch (error: any) {
      console.error('❌ Erro ao carregar clientes:', error);
      console.error('❌ Status:', error.response?.status);
      console.error('❌ Data:', error.response?.data);
      alert(formatApiError(error));
      setClientes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Preparar payload (transformar strings vazias em null)
      const payload = {
        nome: formData.nome,
        telefone: formData.telefone,
        email: formData.email || null,
        data_nascimento: formData.data_nascimento || null,
        observacoes: formData.observacoes || null
      };

      if (editando) {
        await apiClient.put(`/cabeleireiro/clientes/${editando.id}/`, payload);
      } else {
        await apiClient.post('/cabeleireiro/clientes/', payload);
      }
      
      // Recarregar lista
      await carregarClientes();
      
      // Resetar formulário
      setFormData({
        nome: '',
        telefone: '',
        email: '',
        data_nascimento: '',
        observacoes: ''
      });
      setEditando(null);
      setShowForm(false);
    } catch (error) {
      console.error('Erro ao salvar cliente:', error);
      alert(formatApiError(error));
    }
  };

  const handleEditar = (cliente: Cliente) => {
    setFormData({
      nome: cliente.nome,
      telefone: cliente.telefone,
      email: cliente.email || '',
      data_nascimento: cliente.data_nascimento || '',
      observacoes: cliente.observacoes || ''
    });
    setEditando(cliente);
    setShowForm(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Deseja excluir o cliente "${nome}"?`)) return;
    
    try {
      await apiClient.delete(`/cabeleireiro/clientes/${id}/`);
      await carregarClientes();
    } catch (error) {
      console.error('Erro ao excluir cliente:', error);
      alert(formatApiError(error));
    }
  };

  const handleNovo = () => {
    setFormData({
      nome: '',
      telefone: '',
      email: '',
      data_nascimento: '',
      observacoes: ''
    });
    setEditando(null);
    setShowForm(true);
  };

  // Formulário
  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="2xl">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ color: loja.cor_primaria }}>
            👤 {editando ? 'Editar Cliente' : 'Novo Cliente'}
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
                  Data de Nascimento
                </label>
                <input
                  type="date"
                  value={formData.data_nascimento}
                  onChange={(e) => setFormData({ ...formData, data_nascimento: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Observações
                </label>
                <textarea
                  value={formData.observacoes}
                  onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditando(null);
                }}
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

  // Lista
  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: loja.cor_primaria }}>
            👤 Gerenciar Clientes
          </h2>
          <button
            onClick={handleNovo}
            className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo Cliente
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            Carregando...
          </div>
        ) : clientes.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-3xl">👤</span>
            </div>
            <p className="text-lg mb-2 text-gray-700 dark:text-gray-300">Nenhum cliente cadastrado</p>
            <p className="text-sm mb-4 text-gray-500 dark:text-gray-400">Comece adicionando seu primeiro cliente</p>
            <button
              onClick={handleNovo}
              className="px-6 py-3 text-white rounded-lg hover:opacity-90 min-h-[44px]"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Adicionar Primeiro Cliente
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-3 mb-6 max-h-[60vh] overflow-y-auto">
              {clientes.map((cliente) => (
                <div
                  key={cliente.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3"
                >
                  <div className="flex-1">
                    <p className="font-semibold text-lg text-gray-900 dark:text-white">{cliente.nome}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      📱 {cliente.telefone || 'Sem telefone'} {cliente.email && `• ✉️ ${cliente.email}`}
                    </p>
                    {cliente.data_nascimento && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        🎂 {new Date(cliente.data_nascimento).toLocaleDateString('pt-BR')}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEditar(cliente)}
                      className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]"
                      style={{ backgroundColor: loja.cor_primaria }}
                    >
                      ✏️ Editar
                    </button>
                    <button
                      onClick={() => handleExcluir(cliente.id, cliente.nome)}
                      className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]"
                    >
                      🗑️ Excluir
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
              <button
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]"
              >
                Fechar
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
