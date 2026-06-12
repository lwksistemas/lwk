'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { formatApiError } from '@/lib/api-errors';
import { formatCurrency, formatDate, formatDateTime } from '@/lib/financeiro-helpers';
import { useToast } from '@/components/ui/Toast';
import { formatTelefone } from '@/lib/format-br';
import { logger } from '@/lib/logger';
import type {
  LojaInfo,
  Categoria,
  ItemCardapio,
  Mesa,
  Cliente,
  Pedido,
  Funcionario,
  Fornecedor,
  NotaFiscalEntrada,
  EstoqueItem,
  MovimentoEstoque,
  RegistroPesoBalança,
} from '../types';
import { STATUS_MESA, CARGO_FUNCIONARIO } from '../types';

export function ModalFuncionarios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [lista, setLista] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ nome: '', email: '', telefone: '', cargo: 'garcom' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get<Funcionario[] | { results?: Funcionario[] }>('/restaurante/funcionarios/');
      setLista(Array.isArray(res.data) ? res.data : (res.data as { results?: Funcionario[] })?.results ?? []);
    } catch (e) {
      toast.error('Erro ao carregar funcionários');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editId) {
        await clinicaApiClient.put(`/restaurante/funcionarios/${editId}/`, form);
        toast.success('Funcionário atualizado');
      } else {
        await clinicaApiClient.post('/restaurante/funcionarios/', form);
        toast.success('Funcionário cadastrado');
      }
      setShowForm(false);
      setEditId(null);
      setForm({ nome: '', email: '', telefone: '', cargo: 'garcom' });
      load();
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number, nome: string) => {
    if (!confirm(`Excluir funcionário "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/funcionarios/${id}/`);
      toast.success('Funcionário excluído');
      load();
    } catch (err: any) {
      toast.error(formatApiError(err));
    }
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>{editId ? 'Editar' : 'Novo'} Funcionário</h3>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
              <input type="text" value={form.nome} onChange={e => setForm(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
              <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
              <input type="tel" value={form.telefone} onChange={e => setForm(f => ({ ...f, telefone: formatTelefone(e.target.value) }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cargo</label>
              <select value={form.cargo} onChange={e => setForm(f => ({ ...f, cargo: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                {CARGO_FUNCIONARIO.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => { setShowForm(false); setEditId(null); }} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Salvar'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>👥 Gerenciar Funcionários</h3>
          <div className="flex gap-2">
            <button onClick={() => { setForm({ nome: '', email: '', telefone: '', cargo: 'garcom' }); setShowForm(true); }} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Funcionário</button>
            <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
          </div>
        </div>
        {loading ? <p className="text-center text-gray-500 py-8">Carregando...</p> : (
          <div className="space-y-2">
            {lista.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">Nenhum funcionário cadastrado</p>
                <p className="text-sm mb-4">O administrador da loja é automaticamente cadastrado como funcionário</p>
              </div>
            ) : lista.map(f => (
              <div 
                key={f.id} 
                className={`flex items-center justify-between p-4 border dark:border-gray-600 rounded-lg ${
                  f.is_admin 
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700' 
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="font-semibold text-lg text-gray-900 dark:text-white">{f.nome}</span>
                    {f.is_admin && (
                      <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">
                        👤 Administrador
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{CARGO_FUNCIONARIO.find(c => c.value === f.cargo)?.label ?? f.cargo}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{f.email} • {f.telefone}</p>
                  {f.is_admin && (
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                      ℹ️ Administrador vinculado automaticamente à loja (não pode ser editado ou excluído)
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  {f.is_admin ? (
                    <button 
                      disabled
                      className="px-4 py-2 text-sm bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 rounded-lg cursor-not-allowed"
                      title="Administrador não pode ser editado"
                    >
                      🔒 Protegido
                    </button>
                  ) : (
                    <>
                      <button onClick={() => { setEditId(f.id); setForm({ nome: f.nome, email: f.email || '', telefone: f.telefone || '', cargo: f.cargo }); setShowForm(true); }} className="px-3 py-1 text-sm rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                      <button onClick={() => handleDelete(f.id, f.nome)} className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg">🗑️ Excluir</button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
