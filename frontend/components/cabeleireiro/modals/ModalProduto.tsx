'use client';

import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';
import { LojaInfo } from '@/types/dashboard';
import { ensureArray } from '@/lib/array-helpers';
import apiClient from '@/lib/api-client';

interface Produto {
  id: number;
  nome: string;
  descricao?: string;
  categoria: string;
  marca?: string;
  preco_custo: number;
  preco_venda: number;
  estoque_atual: number;
  estoque_minimo: number;
  is_active: boolean;
}

export function ModalProduto({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Produto | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    descricao: '',
    categoria: 'shampoo',
    marca: '',
    preco_custo: '',
    preco_venda: '',
    estoque_atual: '0',
    estoque_minimo: '0'
  });

  const categorias = [
    { value: 'shampoo', label: 'Shampoo' },
    { value: 'condicionador', label: 'Condicionador' },
    { value: 'mascara', label: 'Máscara' },
    { value: 'finalizador', label: 'Finalizador' },
    { value: 'coloracao', label: 'Coloração' },
    { value: 'tratamento', label: 'Tratamento' },
    { value: 'acessorio', label: 'Acessório' },
    { value: 'outros', label: 'Outros' }
  ];

  useEffect(() => {
    carregarProdutos();
  }, []);

  const carregarProdutos = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/produtos/');
      setProdutos(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar produtos:', error);
      toast.error('Erro ao carregar produtos');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        preco_custo: parseFloat(formData.preco_custo),
        preco_venda: parseFloat(formData.preco_venda),
        estoque_atual: parseInt(formData.estoque_atual),
        estoque_minimo: parseInt(formData.estoque_minimo)
      };

      if (editando) {
        await apiClient.put(`/cabeleireiro/produtos/${editando.id}/`, data);
        toast.success('Produto atualizado!');
      } else {
        await apiClient.post('/cabeleireiro/produtos/', data);
        toast.success('Produto cadastrado!');
      }
      resetForm();
      carregarProdutos();
    } catch (error) {
      console.error('Erro ao salvar produto:', error);
      toast.error('Erro ao salvar produto');
    }
  };

  const handleEditar = (produto: Produto) => {
    setEditando(produto);
    setFormData({
      nome: produto.nome,
      descricao: produto.descricao || '',
      categoria: produto.categoria,
      marca: produto.marca || '',
      preco_custo: produto.preco_custo.toString(),
      preco_venda: produto.preco_venda.toString(),
      estoque_atual: produto.estoque_atual.toString(),
      estoque_minimo: produto.estoque_minimo.toString()
    });
    setShowForm(true);
  };

  const handleExcluir = async (produto: Produto) => {
    if (!confirm(`Deseja realmente excluir o produto "${produto.nome}"?`)) return;
    try {
      await apiClient.delete(`/cabeleireiro/produtos/${produto.id}/`);
      toast.success('Produto excluído!');
      carregarProdutos();
    } catch (error) {
      console.error('Erro ao excluir produto:', error);
      toast.error('Erro ao excluir produto');
    }
  };

  const resetForm = () => {
    setFormData({
      nome: '',
      descricao: '',
      categoria: 'shampoo',
      marca: '',
      preco_custo: '',
      preco_venda: '',
      estoque_atual: '0',
      estoque_minimo: '0'
    });
    setEditando(null);
    setShowForm(false);
  };

  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="3xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {editando ? '✏️ Editar Produto' : '🧴 Novo Produto'}
            </h3>
            <button onClick={resetForm} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Nome *</label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  required
                  placeholder="Ex: Shampoo Hidratante"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Categoria *</label>
                <select
                  value={formData.categoria}
                  onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  {categorias.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Marca</label>
                <input
                  type="text"
                  value={formData.marca}
                  onChange={(e) => setFormData({ ...formData, marca: e.target.value })}
                  placeholder="Ex: L'Oréal"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Preço de Custo *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.preco_custo}
                  onChange={(e) => setFormData({ ...formData, preco_custo: e.target.value })}
                  required
                  placeholder="0.00"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Preço de Venda *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.preco_venda}
                  onChange={(e) => setFormData({ ...formData, preco_venda: e.target.value })}
                  required
                  placeholder="0.00"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Estoque Atual</label>
                <input
                  type="number"
                  value={formData.estoque_atual}
                  onChange={(e) => setFormData({ ...formData, estoque_atual: e.target.value })}
                  placeholder="0"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Estoque Mínimo</label>
                <input
                  type="number"
                  value={formData.estoque_minimo}
                  onChange={(e) => setFormData({ ...formData, estoque_minimo: e.target.value })}
                  placeholder="0"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Descrição</label>
                <textarea
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  placeholder="Descrição do produto..."
                  rows={3}
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button type="button" onClick={resetForm} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Cancelar
              </button>
              <button type="submit" className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>
                {editando ? 'Atualizar' : 'Cadastrar'}
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
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">🧴 Gerenciar Produtos</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {loading ? (
          <p className="text-center text-gray-500 py-8">Carregando produtos...</p>
        ) : produtos.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-4">Nenhum produto cadastrado</p>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-3 rounded-lg text-white" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Cadastrar Produto
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-3 mb-6 max-h-96 overflow-y-auto">
              {produtos.map((produto) => (
                <div key={produto.id} className="flex items-center justify-between p-4 border rounded-lg bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-lg dark:text-white">{produto.nome}</p>
                      {produto.estoque_atual <= produto.estoque_minimo && (
                        <span className="px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-xs font-semibold rounded-full">
                          ⚠️ Estoque Baixo
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {categorias.find(c => c.value === produto.categoria)?.label} 
                      {produto.marca && ` • ${produto.marca}`}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      💰 R$ {produto.preco_venda.toFixed(2)} • 📦 Estoque: {produto.estoque_atual}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleEditar(produto)} 
                      className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                    >
                      ✏️ Editar
                    </button>
                    <button 
                      onClick={() => handleExcluir(produto)} 
                      className="px-4 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600"
                    >
                      🗑️ Excluir
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Fechar
              </button>
              <button 
                onClick={() => setShowForm(true)} 
                className="px-6 py-2 text-white rounded-lg" 
                style={{ backgroundColor: loja.cor_primaria }}
              >
                + Novo Produto
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
