'use client';

import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { LojaInfo } from '@/types/dashboard';
import { clinicaApiClient } from '@/lib/api-client';

export function ModalFuncionarios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);
  const [funcionarios, setFuncionarios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    nome: '', email: '', telefone: '', cargo: '', data_admissao: ''
  });

  useEffect(() => { loadFuncionarios(); }, []);

  const loadFuncionarios = async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get('/crm/vendedores/');
      setFuncionarios(Array.isArray(res.data) ? res.data : res.data?.results ?? []);
    } catch (error) {
      toast.error('Erro ao carregar funcionários');
      setFuncionarios([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editando) {
        await clinicaApiClient.put(`/crm/vendedores/${editando}/`, formData);
        toast.success('Funcionário atualizado!');
      } else {
        await clinicaApiClient.post('/crm/vendedores/', formData);
        toast.success('Funcionário cadastrado!');
      }
      resetForm();
      loadFuncionarios();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar funcionário');
    }
  };

  const handleEditar = (func: any) => {
    setEditando(func.id);
    setFormData({
      nome: func.nome,
      email: func.email || '',
      telefone: func.telefone || '',
      cargo: func.cargo || 'Vendedor',
      data_admissao: func.data_admissao || ''
    });
    setShowForm(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Excluir funcionário "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/crm/vendedores/${id}/`);
      toast.success('Funcionário excluído!');
      loadFuncionarios();
    } catch (error) {
      toast.error('Erro ao excluir funcionário');
    }
  };

  const resetForm = () => {
    setFormData({ nome: '', email: '', telefone: '', cargo: '', data_admissao: '' });
    setEditando(null);
    setShowForm(false);
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-2xl w-full">
          <h3 className="text-2xl font-bold mb-6 dark:text-white" style={{ color: loja.cor_primaria }}>
            👥 {editando ? 'Editar' : 'Novo'} Funcionário
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Nome *</label>
                <input type="text" value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} required 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Email *</label>
                <input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Telefone *</label>
                <input type="tel" value={formData.telefone} onChange={(e) => setFormData({...formData, telefone: e.target.value})} required 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Cargo *</label>
                <select value={formData.cargo} onChange={(e) => setFormData({...formData, cargo: e.target.value})} required 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  <option value="">Selecione...</option>
                  <option value="Vendedor">Vendedor</option>
                  <option value="Gerente de Vendas">Gerente de Vendas</option>
                  <option value="Coordenador">Coordenador</option>
                  <option value="Diretor Comercial">Diretor Comercial</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Data Admissão</label>
                <input type="date" value={formData.data_admissao} onChange={(e) => setFormData({...formData, data_admissao: e.target.value})} 
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
            </div>
            <div className="flex justify-end gap-4 pt-4">
              <button type="button" onClick={resetForm} className="px-6 py-2 border rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">Cancelar</button>
              <button type="submit" className="px-6 py-2 text-white rounded-md" style={{ backgroundColor: loja.cor_primaria }}>{editando ? 'Atualizar' : 'Cadastrar'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-4 dark:text-white" style={{ color: loja.cor_primaria }}>👥 Gerenciar Funcionários</h3>
        {loading ? (
          <div className="text-center py-8 text-gray-500">Carregando...</div>
        ) : funcionarios.length === 0 ? (
          <div className="text-center py-8">
            <p className="mb-4 text-gray-500">Nenhum funcionário cadastrado</p>
            <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Funcionário</button>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {funcionarios.map((func: any) => (
                <div key={func.id} className="flex flex-col sm:flex-row justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                  <div className="flex-1">
                    <p className="font-semibold text-lg dark:text-white">{func.nome}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{func.cargo || 'Vendedor'}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{func.email} • {func.telefone}</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleEditar(func)} className="px-4 py-2 text-sm text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                    <button onClick={() => handleExcluir(func.id, func.nome)} className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700">🗑️</button>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
              <button onClick={onClose} className="px-6 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">Fechar</button>
              <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Funcionário</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
