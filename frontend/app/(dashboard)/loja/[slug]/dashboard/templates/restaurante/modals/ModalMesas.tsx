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

export function ModalMesas({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ numero: '', capacidade: '4', localizacao: '', status: 'livre' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get<Mesa[] | { results?: Mesa[] }>('/restaurante/mesas/');
      setMesas(Array.isArray(res.data) ? res.data : (res.data as { results?: Mesa[] })?.results ?? []);
    } catch (e) {
      toast.error('Erro ao carregar mesas');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { numero: form.numero, capacidade: parseInt(form.capacidade, 10) || 4, localizacao: form.localizacao || null, status: form.status };
      if (editId) {
        await clinicaApiClient.put(`/restaurante/mesas/${editId}/`, payload);
        toast.success('Mesa atualizada');
      } else {
        await clinicaApiClient.post('/restaurante/mesas/', payload);
        toast.success('Mesa criada');
      }
      setShowForm(false);
      setEditId(null);
      setForm({ numero: '', capacidade: '4', localizacao: '', status: 'livre' });
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number, numero: string) => {
    if (!confirm(`Excluir mesa ${numero}?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/mesas/${id}/`);
      toast.success('Mesa excluída');
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(formatApiError(err));
    }
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>{editId ? 'Editar' : 'Nova'} Mesa</h3>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número *</label>
              <input type="text" value={form.numero} onChange={e => setForm(f => ({ ...f, numero: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: 1" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capacidade *</label>
              <input type="number" value={form.capacidade} onChange={e => setForm(f => ({ ...f, capacidade: e.target.value }))} min={1} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Localização</label>
              <input type="text" value={form.localizacao} onChange={e => setForm(f => ({ ...f, localizacao: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Salão, Varanda" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
              <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                {STATUS_MESA.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
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
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>🪑 Mesas</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        {loading ? <p className="text-center text-gray-500 py-8">Carregando...</p> : (
          <div className="space-y-2">
            {mesas.length === 0 ? <p className="text-gray-500 py-4">Nenhuma mesa. Clique em Nova Mesa.</p> : mesas.map(m => (
              <div key={m.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">Mesa {m.numero}</span>
                  <span className="ml-2 text-sm text-gray-500">({m.capacidade} pessoas)</span>
                  <span className="ml-2 px-2 py-0.5 rounded text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300">{STATUS_MESA.find(s => s.value === m.status)?.label ?? m.status}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setEditId(m.id); setForm({ numero: m.numero, capacidade: String(m.capacidade), localizacao: m.localizacao || '', status: m.status }); setShowForm(true); }} className="px-3 py-1 text-sm rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>Editar</button>
                  <button onClick={() => handleDelete(m.id, m.numero)} className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg">Excluir</button>
                </div>
              </div>
            ))}
            <button onClick={() => { setForm({ numero: '', capacidade: '4', localizacao: '', status: 'livre' }); setShowForm(true); }} className="w-full py-2 border border-dashed border-gray-400 rounded-lg text-gray-600">+ Nova Mesa</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ——— Modal Pedidos (listar + novo) ———
