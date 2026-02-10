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

interface Servico {
  id: number;
  nome: string;
  descricao?: string;
  categoria: string;
  duracao_minutos: number;
  preco: string;
  is_active: boolean;
}

export function ModalServicos({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [servicos, setServicos] = useState<Servico[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Servico | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    descricao: '',
    categoria: '',
    duracao_minutos: '',
    preco: '',
    is_active: true
  });

  useEffect(() => {
    carregarServicos();
  }, []);

  const carregarServicos = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/servicos/');
      const data = extractArrayData<Servico>(response);
      setServicos(data);
    } catch (error) {
      console.error('Erro ao carregar serviços:', error);
      alert(formatApiError(error));
      setServicos([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const payload = {
        nome: formData.nome,
        descricao: formData.descricao || null,
        categoria: formData.categoria,
        duracao_minutos: parseInt(formData.duracao_minutos),
        preco: parseFloat(formData.preco),
        is_active: formData.is_active
      };

      if (editando) {
        await apiClient.put(`/cabeleireiro/servicos/${editando.id}/`, payload);
      } else {
        await apiClient.post('/cabeleireiro/servicos/', payload);
      }
      
      await carregarServicos();
      setFormData({ nome: '', descricao: '', categoria: '', duracao_minutos: '', preco: '', is_active: true });
      setEditando(null);
      setShowForm(false);
    } catch (error) {
      console.error('Erro ao salvar serviço:', error);
      alert(formatApiError(error));
    }
  };

  const handleEditar = (servico: Servico) => {
    setFormData({
      nome: servico.nome,
      descricao: servico.descricao || '',
      categoria: servico.categoria || '',
      duracao_minutos: servico.duracao_minutos?.toString() || '',
      preco: servico.preco,
      is_active: servico.is_active
    });
    setEditando(servico);
    setShowForm(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Deseja excluir o serviço "${nome}"?`)) return;
    
    try {
      await apiClient.delete(`/cabeleireiro/servicos/${id}/`);
      await carregarServicos();
    } catch (error) {
      console.error('Erro ao excluir serviço:', error);
      alert(formatApiError(error));
    }
  };

  const handleNovo = () => {
    setFormData({ nome: '', descricao: '', categoria: '', duracao_minutos: '', preco: '', is_active: true });
    setEditando(null);
    setShowForm(true);
  };

  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="2xl">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ color: loja.cor_primaria }}>
            ✂️ {editando ? 'Editar Serviço' : 'Novo Serviço'}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome do Serviço *
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
                  Categoria *
                </label>
                <select
                  value={formData.categoria}
                  onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  required
                >
                  <option value="">Selecione...</option>
                  <option value="corte">Corte</option>
                  <option value="coloracao">Coloração</option>
                  <option value="tratamento">Tratamento</option>
                  <option value="penteado">Penteado</option>
                  <option value="manicure">Manicure/Pedicure</option>
                  <option value="barba">Barba</option>
                  <option value="depilacao">Depilação</option>
                  <option value="maquiagem">Maquiagem</option>
                  <option value="outros">Outros</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Duração (minutos) *
                </label>
                <input
                  type="number"
                  value={formData.duracao_minutos}
                  onChange={(e) => setFormData({ ...formData, duracao_minutos: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  required
                  min="1"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Preço (R$) *
                </label>
                <input
                  type="number"
                  value={formData.preco}
                  onChange={(e) => setFormData({ ...formData, preco: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  required
                  min="0"
                  step="0.01"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Descrição
                </label>
                <textarea
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  rows={3}
                />
              </div>

              <div className="md:col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Serviço ativo</span>
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
            ✂️ Gerenciar Serviços
          </h2>
          <button
            onClick={handleNovo}
            className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo Serviço
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : servicos.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-3xl">✂️</span>
            </div>
            <p className="text-lg mb-2 text-gray-700 dark:text-gray-300">Nenhum serviço cadastrado</p>
            <p className="text-sm mb-4 text-gray-500 dark:text-gray-400">Comece adicionando seu primeiro serviço</p>
            <button
              onClick={handleNovo}
              className="px-6 py-3 text-white rounded-lg hover:opacity-90 min-h-[44px]"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Adicionar Primeiro Serviço
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-3 mb-6 max-h-[60vh] overflow-y-auto">
              {servicos.map((servico) => (
                <div key={servico.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-lg text-gray-900 dark:text-white">{servico.nome}</p>
                      {servico.is_active ? (
                        <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs font-semibold rounded-full">Ativo</span>
                      ) : (
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 text-xs font-semibold rounded-full">Inativo</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      ⏱️ {servico.duracao_minutos} min • 💰 R$ {parseFloat(servico.preco).toFixed(2)}
                    </p>
                    {servico.descricao && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{servico.descricao}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleEditar(servico)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                    <button onClick={() => handleExcluir(servico.id, servico.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
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
