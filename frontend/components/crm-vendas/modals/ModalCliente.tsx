'use client';

import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { LojaInfo } from '@/types/dashboard';
import { clinicaApiClient } from '@/lib/api-client';

const ESTADOS = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'];

export function ModalCliente({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);
  const [clientes, setClientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    nome: '', email: '', telefone: '', empresa: '', cnpj: '',
    endereco: '', cidade: '', estado: '', observacoes: ''
  });

  useEffect(() => {
    loadClientes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadClientes = async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get('/crm/clientes/');
      setClientes(Array.isArray(res.data) ? res.data : res.data?.results ?? []);
    } catch (error) {
      toast.error('Erro ao carregar clientes');
      setClientes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        email: formData.email || null,
        cnpj: formData.cnpj || null,
        cpf_cnpj: formData.cnpj || null,
        endereco: formData.endereco || null,
        cidade: formData.cidade || null,
        estado: formData.estado || null
      };
      if (editando) {
        await clinicaApiClient.put(`/crm/clientes/${editando}/`, payload);
        toast.success('Cliente atualizado!');
      } else {
        await clinicaApiClient.post('/crm/clientes/', payload);
        toast.success('Cliente cadastrado!');
      }
      resetForm();
      loadClientes();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar cliente');
    }
  };

  const handleEditar = (cliente: any) => {
    setEditando(cliente.id);
    setFormData({
      nome: cliente.nome,
      email: cliente.email ?? '',
      telefone: cliente.telefone ?? '',
      empresa: cliente.empresa ?? '',
      cnpj: cliente.cnpj ?? cliente.cpf_cnpj ?? '',
      endereco: cliente.endereco || '',
      cidade: cliente.cidade || '',
      estado: cliente.estado || '',
      observacoes: cliente.observacoes || ''
    });
    setShowForm(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Excluir cliente "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/crm/clientes/${id}/`);
      toast.success('Cliente excluído!');
      loadClientes();
    } catch (error) {
      toast.error('Erro ao excluir cliente');
    }
  };

  const resetForm = () => {
    setFormData({ nome: '', email: '', telefone: '', empresa: '', cnpj: '', endereco: '', cidade: '', estado: '', observacoes: '' });
    setEditando(null);
    setShowForm(false);
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <h3 className="text-2xl font-bold mb-6 dark:text-white" style={{ color: loja.cor_primaria }}>
            👤 {editando ? 'Editar' : 'Novo'} Cliente
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Nome/Razão Social *</label>
                <input type="text" value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} required className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Email *</label>
                <input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Telefone *</label>
                <input type="tel" value={formData.telefone} onChange={(e) => setFormData({...formData, telefone: e.target.value})} required className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Empresa</label>
                <input type="text" value={formData.empresa} onChange={(e) => setFormData({...formData, empresa: e.target.value})} className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">CNPJ</label>
                <input type="text" value={formData.cnpj} onChange={(e) => setFormData({...formData, cnpj: e.target.value})} className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Endereço</label>
                <input type="text" value={formData.endereco} onChange={(e) => setFormData({...formData, endereco: e.target.value})} className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Cidade</label>
                <input type="text" value={formData.cidade} onChange={(e) => setFormData({...formData, cidade: e.target.value})} className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Estado</label>
                <select value={formData.estado} onChange={(e) => setFormData({...formData, estado: e.target.value})} className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  <option value="">Selecione...</option>
                  {ESTADOS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Observações</label>
                <textarea value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} rows={3} className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
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
        <h3 className="text-2xl font-bold mb-4 dark:text-white" style={{ color: loja.cor_primaria }}>👤 Gerenciar Clientes</h3>
        {loading ? (
          <div className="text-center py-8 text-gray-500">Carregando...</div>
        ) : clientes.length === 0 ? (
          <div className="text-center py-8">
            <p className="mb-4 text-gray-500">Nenhum cliente cadastrado</p>
            <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {clientes.map((cliente: any) => (
                <div key={cliente.id} className="flex flex-col sm:flex-row justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                  <div className="flex-1">
                    <p className="font-semibold text-lg dark:text-white">{cliente.nome}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{cliente.empresa || ''} {cliente.cnpj ? `• CNPJ: ${cliente.cnpj}` : ''}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{cliente.email} • {cliente.telefone}</p>
                    {(cliente.cidade || cliente.estado) && <p className="text-sm text-gray-600 dark:text-gray-400">{[cliente.cidade, cliente.estado].filter(Boolean).join('/')}</p>}
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleEditar(cliente)} className="px-4 py-2 text-sm text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                    <button onClick={() => handleExcluir(cliente.id, cliente.nome)} className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700">🗑️</button>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
              <button onClick={onClose} className="px-6 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">Fechar</button>
              <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
