'use client';

import { useState } from 'react';
import { LojaInfo } from '@/types/dashboard';

export function ModalProduto({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [formData, setFormData] = useState({
    tipo: '', nome: '', descricao: '', categoria: '', preco: '', custo: '',
    estoque: '', codigo: '', duracao: '', observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const categoriasProduto = ['Software', 'Hardware', 'Licença', 'Material', 'Equipamento', 'Outro'];
  const categoriasServico = ['Consultoria', 'Treinamento', 'Suporte', 'Implementação', 'Manutenção', 'Desenvolvimento', 'Outro'];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert(`✅ ${formData.tipo === 'produto' ? 'Produto' : 'Serviço'} cadastrado!\n\n${formData.nome} - R$ ${formData.preco}`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao cadastrar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6 dark:text-white" style={{ color: loja.cor_primaria }}>📦 Novo Produto/Serviço</h3>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <button type="button" onClick={() => setFormData({...formData, tipo: 'produto', categoria: ''})}
              className={`p-4 rounded-lg border-2 ${formData.tipo === 'produto' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}`}>
              <div className="text-3xl mb-2">📦</div>
              <div className="font-semibold dark:text-white">Produto</div>
            </button>
            <button type="button" onClick={() => setFormData({...formData, tipo: 'servico', categoria: '', estoque: ''})}
              className={`p-4 rounded-lg border-2 ${formData.tipo === 'servico' ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : 'border-gray-300 dark:border-gray-600'}`}>
              <div className="text-3xl mb-2">🛠️</div>
              <div className="font-semibold dark:text-white">Serviço</div>
            </button>
          </div>

          {formData.tipo && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Nome *</label>
                <input type="text" value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} required 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Categoria *</label>
                <select value={formData.categoria} onChange={(e) => setFormData({...formData, categoria: e.target.value})} required 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  <option value="">Selecione...</option>
                  {(formData.tipo === 'produto' ? categoriasProduto : categoriasServico).map(cat => 
                    <option key={cat} value={cat}>{cat}</option>
                  )}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Preço (R$) *</label>
                <input type="number" value={formData.preco} onChange={(e) => setFormData({...formData, preco: e.target.value})} required min="0" step="0.01" 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              {formData.tipo === 'produto' && (
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-white">Estoque</label>
                  <input type="number" value={formData.estoque} onChange={(e) => setFormData({...formData, estoque: e.target.value})} min="0" 
                    className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
                </div>
              )}
              {formData.tipo === 'servico' && (
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-white">Duração</label>
                  <input type="text" value={formData.duracao} onChange={(e) => setFormData({...formData, duracao: e.target.value})} 
                    placeholder="Ex: 2 horas" className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
                </div>
              )}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Descrição</label>
                <textarea value={formData.descricao} onChange={(e) => setFormData({...formData, descricao: e.target.value})} rows={3} 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
            </div>
          )}
          
          <div className="flex justify-end gap-4 pt-4 border-t dark:border-gray-600">
            <button type="button" onClick={onClose} disabled={loading} 
              className="px-6 py-2 border rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">Cancelar</button>
            <button type="submit" disabled={loading || !formData.tipo} 
              className="px-6 py-2 text-white rounded-md disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>
              {loading ? 'Cadastrando...' : 'Cadastrar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
