'use client';

import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { LojaInfo, Lead } from '@/types/dashboard';
import { clinicaApiClient } from '@/lib/api-client';
import { formatCurrency } from '@/lib/financeiro-helpers';
import { ORIGENS_CRM, STATUS_LEAD } from '@/constants/status';

const INTERESSES_CRM = ['Produto A', 'Produto B', 'Serviço Premium', 'Consultoria', 'Outro'];

export function ModalLead({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    nome: '', email: '', telefone: '', empresa: '', cargo: '',
    origem: 'site', interesse: 'Produto A', valor_estimado: '', status: 'novo', observacoes: ''
  });

  useEffect(() => {
    loadLeads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadLeads = async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get('/crm/leads/');
      setLeads(Array.isArray(res.data) ? res.data : res.data?.results ?? []);
    } catch (error) {
      toast.error('Erro ao carregar leads');
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        valor_estimado: formData.valor_estimado ? parseFloat(formData.valor_estimado) : 0,
        cargo: formData.cargo || null,
        observacoes: formData.observacoes || null
      };
      if (editando) {
        await clinicaApiClient.put(`/crm/leads/${editando}/`, payload);
        toast.success('Lead atualizado!');
      } else {
        await clinicaApiClient.post('/crm/leads/', payload);
        toast.success('Lead cadastrado!');
      }
      resetForm();
      loadLeads();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar lead');
    }
  };

  const handleEditar = (lead: any) => {
    setEditando(lead.id);
    setFormData({
      nome: lead.nome, email: lead.email, telefone: lead.telefone,
      empresa: lead.empresa, cargo: lead.cargo || '', origem: lead.origem || 'site',
      interesse: lead.interesse || 'Produto A', valor_estimado: String(lead.valor_estimado ?? ''),
      status: lead.status || 'novo', observacoes: lead.observacoes || ''
    });
    setShowForm(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Excluir lead "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/crm/leads/${id}/`);
      toast.success('Lead excluído!');
      loadLeads();
      onSuccess?.();
    } catch (error) {
      toast.error('Erro ao excluir lead');
    }
  };

  const handleConverter = async (lead: any) => {
    if (!confirm(`Converter "${lead.nome}" em cliente?`)) return;
    try {
      await clinicaApiClient.post('/crm/clientes/', {
        nome: lead.nome, email: lead.email, telefone: lead.telefone,
        empresa: lead.empresa, cnpj: '', endereco: '', cidade: '', estado: '', observacoes: ''
      });
      await clinicaApiClient.delete(`/crm/leads/${lead.id}/`);
      toast.success('Lead convertido em cliente!');
      loadLeads();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao converter lead');
    }
  };

  const resetForm = () => {
    setFormData({ nome: '', email: '', telefone: '', empresa: '', cargo: '', origem: 'site', interesse: 'Produto A', valor_estimado: '', status: 'novo', observacoes: '' });
    setEditando(null);
    setShowForm(false);
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <h3 className="text-2xl font-bold mb-6 dark:text-white" style={{ color: loja.cor_primaria }}>
            🎯 {editando ? 'Editar' : 'Novo'} Lead
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 dark:text-white">Nome *</label>
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
                <label className="block text-sm font-medium mb-1 dark:text-white">Empresa *</label>
                <input type="text" value={formData.empresa} onChange={(e) => setFormData({...formData, empresa: e.target.value})} required className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Cargo</label>
                <input type="text" value={formData.cargo} onChange={(e) => setFormData({...formData, cargo: e.target.value})} className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Origem *</label>
                <select value={formData.origem} onChange={(e) => setFormData({...formData, origem: e.target.value})} required className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {ORIGENS_CRM.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Interesse *</label>
                <select value={formData.interesse} onChange={(e) => setFormData({...formData, interesse: e.target.value})} required className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {INTERESSES_CRM.map(int => <option key={int} value={int}>{int}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Status *</label>
                <select value={formData.status} onChange={(e) => setFormData({...formData, status: e.target.value})} required className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                  {STATUS_LEAD.map(st => <option key={st.value} value={st.value}>{st.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Valor Estimado (R$)</label>
                <input type="number" value={formData.valor_estimado} onChange={(e) => setFormData({...formData, valor_estimado: e.target.value})} min="0" step="0.01" className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-4 dark:text-white" style={{ color: loja.cor_primaria }}>🎯 Gerenciar Leads</h3>
        {loading ? (
          <div className="text-center py-8 text-gray-500">Carregando...</div>
        ) : leads.length === 0 ? (
          <div className="text-center py-8">
            <p className="mb-4 text-gray-500">Nenhum lead cadastrado</p>
            <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Lead</button>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {leads.map((lead: any) => (
                <div key={lead.id} className="flex flex-col sm:flex-row justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                  <div className="flex-1">
                    <p className="font-semibold text-lg dark:text-white">{lead.nome}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{lead.empresa} • {lead.email}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{lead.telefone}</p>
                    <div className="mt-2 flex gap-2">
                      <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">
                        {STATUS_LEAD.find(s => s.value === lead.status)?.label}
                      </span>
                      <span className="text-sm font-bold" style={{ color: loja.cor_primaria }}>{formatCurrency(lead.valor_estimado)}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleEditar(lead)} className="px-3 py-2 text-sm text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                    <button onClick={() => handleConverter(lead)} className="px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700">✅ Converter</button>
                    <button onClick={() => handleExcluir(lead.id, lead.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700">🗑️</button>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
              <button onClick={onClose} className="px-6 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">Fechar</button>
              <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Lead</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
