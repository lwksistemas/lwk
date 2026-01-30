'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { formatApiError } from '@/lib/api-errors';
import { useToast } from '@/components/ui/Toast';
import type { LojaInfo, Cliente } from '../types';

export function ModalClientes({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [lista, setLista] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ nome: '', email: '', telefone: '', endereco: '' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await clinicaApiClient.get<Cliente[] | { results?: Cliente[] }>('/restaurante/clientes/');
      setLista(Array.isArray(res.data) ? res.data : (res.data as { results?: Cliente[] })?.results ?? []);
    } catch {
      setLista([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nome.trim()) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      if (editId) {
        await clinicaApiClient.put(`/restaurante/clientes/${editId}/`, form);
        toast.success('Cliente atualizado');
      } else {
        await clinicaApiClient.post('/restaurante/clientes/', form);
        toast.success('Cliente cadastrado');
      }
      setShowForm(false);
      setEditId(null);
      setForm({ nome: '', email: '', telefone: '', endereco: '' });
      load();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (c: Cliente) => {
    setEditId(c.id);
    setForm({ nome: c.nome, email: c.email || '', telefone: c.telefone || '', endereco: c.endereco || '' });
    setShowForm(true);
  };

  const handleDelete = async (id: number, nome: string) => {
    if (!confirm(`Excluir cliente "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/clientes/${id}/`);
      toast.success('Cliente excluído');
      load();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[60] p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>👤 Clientes</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        {loading ? (
          <div className="text-center py-6 text-gray-500">Carregando...</div>
        ) : showForm ? (
          <form onSubmit={handleSubmit} className="space-y-3">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label><input type="text" value={form.nome} onChange={e => setForm(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Nome do cliente" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label><input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label><input type="tel" value={form.telefone} onChange={e => setForm(f => ({ ...f, telefone: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="(00) 00000-0000" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço</label><input type="text" value={form.endereco} onChange={e => setForm(f => ({ ...f, endereco: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => { setShowForm(false); setEditId(null); }} disabled={saving} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">Voltar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : (editId ? 'Atualizar' : 'Cadastrar')}</button>
            </div>
          </form>
        ) : (
          <>
            {lista.length === 0 ? <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Nenhum cliente. Cadastre o primeiro.</p> : <ul className="space-y-2 max-h-48 overflow-y-auto mb-4">{lista.map(c => (<li key={c.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"><div><p className="font-medium text-gray-900 dark:text-white">{c.nome}</p><p className="text-xs text-gray-600 dark:text-gray-400">{c.email}{c.telefone ? ` · ${c.telefone}` : ''}</p></div><div className="flex gap-2"><button type="button" onClick={() => handleEdit(c)} className="px-2 py-1 rounded text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>Editar</button><button type="button" onClick={() => handleDelete(c.id, c.nome)} className="px-2 py-1 rounded bg-red-600 text-white text-sm">Excluir</button></div></li>))}</ul>}
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => { setEditId(null); setForm({ nome: '', email: '', telefone: '', endereco: '' }); setShowForm(true); }} className="px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">Fechar</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
