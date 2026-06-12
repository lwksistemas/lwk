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

export function ModalCardapio({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [aba, setAba] = useState<'categorias' | 'itens'>('categorias');
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [itens, setItens] = useState<ItemCardapio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFormCat, setShowFormCat] = useState(false);
  const [showFormItem, setShowFormItem] = useState(false);
  const [editCatId, setEditCatId] = useState<number | null>(null);
  const [editItemId, setEditItemId] = useState<number | null>(null);
  const [formCat, setFormCat] = useState({ nome: '', ordem: '0' });
  const [formItem, setFormItem] = useState({
    nome: '', descricao: '', categoria: '', preco: '', tempo_preparo: '15',
    is_disponivel: true
  });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [catRes, itensRes] = await Promise.all([
        clinicaApiClient.get<Categoria[] | { results?: Categoria[] }>('/restaurante/categorias/'),
        clinicaApiClient.get<ItemCardapio[] | { results?: ItemCardapio[] }>('/restaurante/cardapio/')
      ]);
      setCategorias(Array.isArray(catRes.data) ? catRes.data : (catRes.data as { results?: Categoria[] })?.results ?? []);
      setItens(Array.isArray(itensRes.data) ? itensRes.data : (itensRes.data as { results?: ItemCardapio[] })?.results ?? []);
    } catch (e) {
      logger.warn('Erro ao carregar cardápio:', e);
      toast.error('Erro ao carregar cardápio');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const handleSaveCategoria = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { nome: formCat.nome, ordem: parseInt(formCat.ordem, 10) || 0 };
      if (editCatId) {
        await clinicaApiClient.put(`/restaurante/categorias/${editCatId}/`, payload);
        toast.success('Categoria atualizada');
      } else {
        await clinicaApiClient.post('/restaurante/categorias/', payload);
        toast.success('Categoria criada');
      }
      setShowFormCat(false);
      setEditCatId(null);
      setFormCat({ nome: '', ordem: '0' });
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveItem = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const precoNum = formItem.preco ? parseFloat(String(formItem.preco).replace(',', '.')) : 0;
      if (isNaN(precoNum) || precoNum < 0) {
        toast.error('Preço inválido. Use um número maior ou igual a zero.');
        setSaving(false);
        return;
      }
      const payload = {
        nome: formItem.nome.trim(),
        descricao: (formItem.descricao || '').trim() || formItem.nome,
        categoria: formItem.categoria ? parseInt(formItem.categoria, 10) : null,
        preco: String(precoNum),
        tempo_preparo: parseInt(formItem.tempo_preparo, 10) || 15,
        is_disponivel: formItem.is_disponivel
      };
      if (editItemId) {
        await clinicaApiClient.put(`/restaurante/cardapio/${editItemId}/`, payload);
        toast.success('Item atualizado');
      } else {
        await clinicaApiClient.post('/restaurante/cardapio/', payload);
        toast.success('Item criado');
      }
      setShowFormItem(false);
      setEditItemId(null);
      setFormItem({ nome: '', descricao: '', categoria: '', preco: '', tempo_preparo: '15', is_disponivel: true });
      load();
      onSuccess?.();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCategoria = async (id: number, nome: string) => {
    if (!confirm(`Excluir categoria "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/categorias/${id}/`);
      toast.success('Categoria excluída');
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(formatApiError(err));
    }
  };

  const handleDeleteItem = async (id: number, nome: string) => {
    if (!confirm(`Excluir item "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/cardapio/${id}/`);
      toast.success('Item excluído');
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(formatApiError(err));
    }
  };

  if (showFormCat) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            {editCatId ? 'Editar' : 'Nova'} Categoria
          </h3>
          <form onSubmit={handleSaveCategoria} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
              <input type="text" value={formCat.nome} onChange={e => setFormCat(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: Bebidas" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ordem</label>
              <input type="number" value={formCat.ordem} onChange={e => setFormCat(f => ({ ...f, ordem: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => { setShowFormCat(false); setEditCatId(null); }} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Salvar'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  if (showFormItem) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            {editItemId ? 'Editar' : 'Novo'} Item do Cardápio
          </h3>
          <form onSubmit={handleSaveItem} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
              <input type="text" value={formItem.nome} onChange={e => setFormItem(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: Refrigerante" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
              <textarea value={formItem.descricao} onChange={e => setFormItem(f => ({ ...f, descricao: e.target.value }))} rows={2} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
              <select value={formItem.categoria} onChange={e => setFormItem(f => ({ ...f, categoria: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                <option value="">Nenhuma</option>
                {categorias.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço (R$) *</label>
                <input type="text" value={formItem.preco} onChange={e => setFormItem(f => ({ ...f, preco: e.target.value }))} required placeholder="0.00" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tempo preparo (min)</label>
                <input type="number" value={formItem.tempo_preparo} onChange={e => setFormItem(f => ({ ...f, tempo_preparo: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="disp" checked={formItem.is_disponivel} onChange={e => setFormItem(f => ({ ...f, is_disponivel: e.target.checked }))} />
              <label htmlFor="disp" className="text-sm text-gray-700 dark:text-gray-300">Disponível</label>
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => { setShowFormItem(false); setEditItemId(null); }} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Salvar'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📋 Cardápio</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400">✕</button>
        </div>
        <div className="flex gap-2 mb-4">
          <button onClick={() => setAba('categorias')} className={`px-4 py-2 rounded-lg font-medium ${aba === 'categorias' ? 'text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`} style={aba === 'categorias' ? { backgroundColor: loja.cor_primaria } : {}}>Categorias</button>
          <button onClick={() => setAba('itens')} className={`px-4 py-2 rounded-lg font-medium ${aba === 'itens' ? 'text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`} style={aba === 'itens' ? { backgroundColor: loja.cor_primaria } : {}}>Itens</button>
        </div>
        {loading ? (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">Carregando...</p>
        ) : aba === 'categorias' ? (
          <div className="space-y-2">
            {categorias.length === 0 ? <p className="text-gray-500 dark:text-gray-400 py-4">Nenhuma categoria. Clique em Nova Categoria.</p> : categorias.map(c => (
              <div key={c.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <span className="font-medium text-gray-900 dark:text-white">{c.nome}</span>
                <div className="flex gap-2">
                  <button onClick={() => { setEditCatId(c.id); setFormCat({ nome: c.nome, ordem: String(c.ordem ?? 0) }); setShowFormCat(true); }} className="px-3 py-1 text-sm rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>Editar</button>
                  <button onClick={() => handleDeleteCategoria(c.id, c.nome)} className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg">Excluir</button>
                </div>
              </div>
            ))}
            <button onClick={() => { setFormCat({ nome: '', ordem: '0' }); setShowFormCat(true); }} className="w-full py-2 border border-dashed border-gray-400 dark:border-gray-500 rounded-lg text-gray-600 dark:text-gray-400">+ Nova Categoria</button>
          </div>
        ) : (
          <div className="space-y-2">
            {itens.length === 0 ? <p className="text-gray-500 dark:text-gray-400 py-4">Nenhum item. Clique em Novo Item.</p> : itens.map(i => (
              <div key={i.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">{i.nome}</span>
                  <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">{formatCurrency(i.preco)}</span>
                  {!i.is_disponivel && <span className="ml-2 text-xs text-red-600">(indisponível)</span>}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setEditItemId(i.id); setFormItem({ nome: i.nome, descricao: i.descricao || '', categoria: i.categoria ? String(i.categoria) : '', preco: i.preco, tempo_preparo: String(i.tempo_preparo), is_disponivel: i.is_disponivel }); setShowFormItem(true); }} className="px-3 py-1 text-sm rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>Editar</button>
                  <button onClick={() => handleDeleteItem(i.id, i.nome)} className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg">Excluir</button>
                </div>
              </div>
            ))}
            <button onClick={() => { setFormItem({ nome: '', descricao: '', categoria: '', preco: '', tempo_preparo: '15', is_disponivel: true }); setShowFormItem(true); }} className="w-full py-2 border border-dashed border-gray-400 dark:border-gray-500 rounded-lg text-gray-600 dark:text-gray-400">+ Novo Item</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ——— Modal Mesas ———
