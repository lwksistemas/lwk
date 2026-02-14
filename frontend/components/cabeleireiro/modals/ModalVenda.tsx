'use client';

import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';
import { LojaInfo } from '@/types/dashboard';
import { ensureArray } from '@/lib/array-helpers';
import apiClient from '@/lib/api-client';

interface Venda {
  id: number;
  cliente?: { id: number; nome: string };
  produto: { id: number; nome: string };
  quantidade: number;
  valor_unitario: number;
  valor_total: number;
  forma_pagamento: string;
  data_venda: string;
}

export function ModalVenda({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [vendas, setVendas] = useState<Venda[]>([]);
  const [produtos, setProdutos] = useState<any[]>([]);
  const [clientes, setClientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    cliente: '',
    produto: '',
    quantidade: '1',
    forma_pagamento: 'dinheiro',
    observacoes: ''
  });

  const formasPagamento = [
    { value: 'dinheiro', label: 'Dinheiro' },
    { value: 'debito', label: 'Débito' },
    { value: 'credito', label: 'Crédito' },
    { value: 'pix', label: 'PIX' },
    { value: 'outros', label: 'Outros' }
  ];

  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    try {
      setLoading(true);
      const [vendasRes, produtosRes, clientesRes] = await Promise.all([
        apiClient.get('/cabeleireiro/vendas/'),
        apiClient.get('/cabeleireiro/produtos/'),
        apiClient.get('/cabeleireiro/clientes/')
      ]);
      setVendas(ensureArray(vendasRes.data));
      setProdutos(ensureArray(produtosRes.data));
      setClientes(ensureArray(clientesRes.data));
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const produtoSelecionado = produtos.find(p => p.id === parseInt(formData.produto));
      if (!produtoSelecionado) {
        toast.error('Produto não encontrado');
        return;
      }

      const data = {
        cliente: formData.cliente ? parseInt(formData.cliente) : null,
        produto: parseInt(formData.produto),
        quantidade: parseInt(formData.quantidade),
        valor_unitario: produtoSelecionado.preco_venda,
        forma_pagamento: formData.forma_pagamento,
        observacoes: formData.observacoes
      };

      await apiClient.post('/cabeleireiro/vendas/', data);
      toast.success('Venda registrada!');
      resetForm();
      carregarDados();
    } catch (error) {
      console.error('Erro ao registrar venda:', error);
      toast.error('Erro ao registrar venda');
    }
  };

  const resetForm = () => {
    setFormData({
      cliente: '',
      produto: '',
      quantidade: '1',
      forma_pagamento: 'dinheiro',
      observacoes: ''
    });
    setShowForm(false);
  };

  const produtoSelecionado = produtos.find(p => p.id === parseInt(formData.produto));
  const valorTotal = produtoSelecionado 
    ? (Number(produtoSelecionado.preco_venda) * parseInt(formData.quantidade || '0')).toFixed(2)
    : '0.00';

  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="2xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">💰 Nova Venda</h3>
            <button onClick={resetForm} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Produto *</label>
              <select
                value={formData.produto}
                onChange={(e) => setFormData({ ...formData, produto: e.target.value })}
                required
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="">Selecione um produto</option>
                {produtos.map(produto => (
                  <option key={produto.id} value={produto.id}>
                    {produto.nome} - R$ {Number(produto.preco_venda).toFixed(2)} (Estoque: {produto.estoque_atual})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Cliente (opcional)</label>
              <select
                value={formData.cliente}
                onChange={(e) => setFormData({ ...formData, cliente: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="">Venda sem cliente</option>
                {clientes.map(cliente => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nome} - {cliente.telefone}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Quantidade *</label>
                <input
                  type="number"
                  min="1"
                  value={formData.quantidade}
                  onChange={(e) => setFormData({ ...formData, quantidade: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Forma de Pagamento *</label>
                <select
                  value={formData.forma_pagamento}
                  onChange={(e) => setFormData({ ...formData, forma_pagamento: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  {formasPagamento.map(forma => (
                    <option key={forma.value} value={forma.value}>{forma.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Observações</label>
              <textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                placeholder="Observações sobre a venda..."
                rows={2}
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>

            {produtoSelecionado && (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Valor Total:</p>
                <p className="text-2xl font-bold" style={{ color: loja.cor_primaria }}>
                  R$ {valorTotal}
                </p>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button type="button" onClick={resetForm} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Cancelar
              </button>
              <button type="submit" className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>
                Registrar Venda
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
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">💰 Histórico de Vendas</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {loading ? (
          <p className="text-center text-gray-500 py-8">Carregando vendas...</p>
        ) : vendas.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-4">Nenhuma venda registrada</p>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-3 rounded-lg text-white" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Registrar Venda
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-3 mb-6 max-h-96 overflow-y-auto">
              {vendas.map((venda) => (
                <div key={venda.id} className="flex items-center justify-between p-4 border rounded-lg bg-white dark:bg-gray-700">
                  <div className="flex-1">
                    <p className="font-semibold text-lg dark:text-white">{venda.produto.nome}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {venda.cliente ? `Cliente: ${venda.cliente.nome}` : 'Venda sem cliente'}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Qtd: {venda.quantidade} • {formasPagamento.find(f => f.value === venda.forma_pagamento)?.label}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(venda.data_venda).toLocaleString('pt-BR')}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold" style={{ color: loja.cor_primaria }}>
                      R$ {Number(venda.valor_total).toFixed(2)}
                    </p>
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
                + Nova Venda
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
