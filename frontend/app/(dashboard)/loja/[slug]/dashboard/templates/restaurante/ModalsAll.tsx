'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { formatApiError } from '@/lib/api-errors';
import { formatCurrency, formatDate, formatDateTime } from '@/lib/financeiro-helpers';
import { useToast } from '@/components/ui/Toast';
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
} from './types';
import { STATUS_MESA, CARGO_FUNCIONARIO } from './types';
// ——— Modal Cardápio (Categorias + Itens) ———
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
      console.error(e);
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
export function ModalPedidos({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [itens, setItens] = useState<ItemCardapio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNovo, setShowNovo] = useState(false);
  const [form, setForm] = useState({ tipo: 'local' as 'local' | 'delivery' | 'retirada', cliente: '', mesa: '', endereco_entrega: '', taxa_entrega: '0' });
  const [itensPedido, setItensPedido] = useState<{ item_id: number; quantidade: number; preco: string }[]>([]);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [pRes, cRes, mRes, iRes] = await Promise.all([
        clinicaApiClient.get<Pedido[] | { results?: Pedido[] }>('/restaurante/pedidos/'),
        clinicaApiClient.get<Cliente[] | { results?: Cliente[] }>('/restaurante/clientes/'),
        clinicaApiClient.get<Mesa[] | { results?: Mesa[] }>('/restaurante/mesas/'),
        clinicaApiClient.get<ItemCardapio[] | { results?: ItemCardapio[] }>('/restaurante/cardapio/')
      ]);
      setPedidos(Array.isArray(pRes.data) ? pRes.data : (pRes.data as { results?: Pedido[] })?.results ?? []);
      setClientes(Array.isArray(cRes.data) ? cRes.data : (cRes.data as { results?: Cliente[] })?.results ?? []);
      setMesas(Array.isArray(mRes.data) ? mRes.data : (mRes.data as { results?: Mesa[] })?.results ?? []);
      setItens(Array.isArray(iRes.data) ? iRes.data : (iRes.data as { results?: ItemCardapio[] })?.results ?? []);
    } catch (e) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const addItem = (item: ItemCardapio) => {
    const exist = itensPedido.find(x => x.item_id === item.id);
    if (exist) setItensPedido(prev => prev.map(x => x.item_id === item.id ? { ...x, quantidade: x.quantidade + 1 } : x));
    else setItensPedido(prev => [...prev, { item_id: item.id, quantidade: 1, preco: item.preco }]);
  };

  const removeItem = (itemId: number) => setItensPedido(prev => prev.filter(x => x.item_id !== itemId));

  const totalPedido = itensPedido.reduce((s, x) => s + Number(x.preco) * x.quantidade, 0) + (form.tipo === 'delivery' ? Number(form.taxa_entrega || 0) : 0);

  const handleCriarPedido = async (e: React.FormEvent) => {
    e.preventDefault();
    if (itensPedido.length === 0) { toast.error('Adicione pelo menos um item'); return; }
    setSaving(true);
    try {
      const subtotal = itensPedido.reduce((s, x) => s + Number(x.preco) * x.quantidade, 0);
      const taxa = form.tipo === 'delivery' ? Number(form.taxa_entrega || 0) : 0;
      const total = subtotal + taxa;
      const numeroPedido = `PED-${Date.now()}`;
      const payloadPedido = {
        numero_pedido: numeroPedido,
        status: 'pendente',
        subtotal: String(subtotal.toFixed(2)),
        desconto: '0.00',
        total: String(total.toFixed(2)),
        tipo: form.tipo,
        cliente: form.cliente ? parseInt(form.cliente, 10) : null,
        mesa: form.tipo === 'local' && form.mesa ? parseInt(form.mesa, 10) : null,
        endereco_entrega: form.tipo === 'delivery' ? form.endereco_entrega : null,
        taxa_entrega: form.tipo === 'delivery' ? (form.taxa_entrega || '0') : '0',
        taxa_servico: '0.00'
      };
      const res = await clinicaApiClient.post<{ id: number }>('/restaurante/pedidos/', payloadPedido);
      const pedidoId = res.data.id;
      for (const x of itensPedido) {
        const sub = Number(x.preco) * x.quantidade;
        await clinicaApiClient.post('/restaurante/itens-pedido/', {
          pedido: pedidoId,
          item_cardapio: x.item_id,
          quantidade: x.quantidade,
          preco_unitario: x.preco,
          subtotal: String(sub.toFixed(2))
        });
      }
      toast.success('Pedido criado');
      setShowNovo(false);
      setForm({ tipo: 'local', cliente: '', mesa: '', endereco_entrega: '', taxa_entrega: '0' });
      setItensPedido([]);
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  if (showNovo) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📦 Novo Pedido</h3>
          <form onSubmit={handleCriarPedido} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
              <select value={form.tipo} onChange={e => setForm(f => ({ ...f, tipo: e.target.value as 'local' | 'delivery' | 'retirada' }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                <option value="local">Local (mesa)</option>
                <option value="delivery">Delivery</option>
                <option value="retirada">Retirada</option>
              </select>
            </div>
            {form.tipo === 'local' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mesa</label>
                <select value={form.mesa} onChange={e => setForm(f => ({ ...f, mesa: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                  <option value="">—</option>
                  {mesas.map(m => <option key={m.id} value={m.id}>Mesa {m.numero}</option>)}
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cliente (opcional)</label>
              <select value={form.cliente} onChange={e => setForm(f => ({ ...f, cliente: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                <option value="">—</option>
                {clientes.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
              </select>
            </div>
            {form.tipo === 'delivery' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço de entrega</label>
                  <textarea value={form.endereco_entrega} onChange={e => setForm(f => ({ ...f, endereco_entrega: e.target.value }))} rows={2} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Taxa entrega (R$)</label>
                  <input type="text" value={form.taxa_entrega} onChange={e => setForm(f => ({ ...f, taxa_entrega: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="0.00" />
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Itens do pedido</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {itens.filter(i => i.is_disponivel).map(i => (
                  <button type="button" key={i.id} onClick={() => addItem(i)} className="px-3 py-2 rounded-lg border dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm">
                    {i.nome} — {formatCurrency(i.preco)}
                  </button>
                ))}
              </div>
              <ul className="space-y-1">
                {itensPedido.map(x => {
                  const item = itens.find(i => i.id === x.item_id);
                  return item ? (
                    <li key={x.item_id} className="flex justify-between items-center">
                      <span>{item.nome} x{x.quantidade}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{formatCurrency(Number(x.preco) * x.quantidade)}</span>
                        <button type="button" onClick={() => removeItem(x.item_id)} className="text-red-600 text-sm">Remover</button>
                      </div>
                    </li>
                  ) : null;
                })}
              </ul>
            </div>
            <p className="font-bold text-lg">Total: {formatCurrency(totalPedido)}</p>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => setShowNovo(false)} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Criar Pedido'}</button>
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
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📦 Pedidos</h3>
          <div className="flex gap-2">
            <button onClick={() => setShowNovo(true)} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo</button>
            <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
          </div>
        </div>
        {loading ? <p className="text-center text-gray-500 py-8">Carregando...</p> : (
          <div className="space-y-2">
            {pedidos.length === 0 ? <p className="text-gray-500 py-4">Nenhum pedido.</p> : pedidos.map(p => (
              <div key={p.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">#{p.id}</span>
                  <span className="ml-2 text-sm text-gray-500">{p.tipo} • {p.status}</span>
                </div>
                <span className="font-bold" style={{ color: loja.cor_primaria }}>{formatCurrency(p.total)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ——— Modal Delivery (pedidos tipo delivery) ———
export function ModalDelivery({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get<Pedido[] | { results?: Pedido[] }>('/restaurante/pedidos/', { params: { tipo: 'delivery' } });
      const list = Array.isArray(res.data) ? res.data : (res.data as { results?: Pedido[] })?.results ?? [];
      setPedidos(list);
    } catch (e) {
      toast.error('Erro ao carregar pedidos de delivery');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>🛵 Controle de Delivery</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        {loading ? <p className="text-center text-gray-500 py-8">Carregando...</p> : (
          <div className="space-y-3">
            {pedidos.length === 0 ? <p className="text-gray-500 py-4">Nenhum pedido de delivery no momento.</p> : pedidos.map(p => (
              <div key={p.id} className="p-4 border dark:border-gray-600 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Pedido #{p.id}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Status: {p.status}</p>
                    {p.endereco_entrega && <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">📍 {p.endereco_entrega}</p>}
                    <p className="text-sm font-semibold mt-1">{formatCurrency(p.total)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ——— Modal PDV (vendas rápidas) ———
export function ModalPDV({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [itens, setItens] = useState<ItemCardapio[]>([]);
  const [carrinho, setCarrinho] = useState<{ item: ItemCardapio; qtd: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get<ItemCardapio[] | { results?: ItemCardapio[] }>('/restaurante/cardapio/');
      setItens(Array.isArray(res.data) ? res.data : (res.data as { results?: ItemCardapio[] })?.results ?? []);
    } catch (e) {
      toast.error('Erro ao carregar cardápio');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const add = (item: ItemCardapio) => {
    const exist = carrinho.find(x => x.item.id === item.id);
    if (exist) setCarrinho(prev => prev.map(x => x.item.id === item.id ? { ...x, qtd: x.qtd + 1 } : x));
    else setCarrinho(prev => [...prev, { item, qtd: 1 }]);
  };

  const remove = (itemId: number) => setCarrinho(prev => prev.filter(x => x.item.id !== itemId));

  const total = carrinho.reduce((s, x) => s + Number(x.item.preco) * x.qtd, 0);

  const finalizar = async () => {
    if (carrinho.length === 0) { toast.error('Adicione itens ao carrinho'); return; }
    try {
      const subtotal = carrinho.reduce((s, x) => s + Number(x.item.preco) * x.qtd, 0);
      const payloadPedido = {
        numero_pedido: `PDV-${Date.now()}`,
        status: 'pendente',
        subtotal: String(subtotal.toFixed(2)),
        desconto: '0.00',
        total: String(subtotal.toFixed(2)),
        tipo: 'local',
        taxa_servico: '0.00',
        taxa_entrega: '0.00'
      };
      const res = await clinicaApiClient.post<{ id: number }>('/restaurante/pedidos/', payloadPedido);
      const pedidoId = res.data.id;
      for (const x of carrinho) {
        const sub = Number(x.item.preco) * x.qtd;
        await clinicaApiClient.post('/restaurante/itens-pedido/', {
          pedido: pedidoId,
          item_cardapio: x.item.id,
          quantidade: x.qtd,
          preco_unitario: x.item.preco,
          subtotal: String(sub.toFixed(2))
        });
      }
      toast.success('Venda registrada');
      setCarrinho([]);
      onSuccess?.();
    } catch (err: any) {
      toast.error(formatApiError(err));
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>💳 PDV - Vendas</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Cardápio — clique para adicionar</p>
            {loading ? <p className="text-gray-500">Carregando...</p> : (
              <div className="flex flex-wrap gap-2 max-h-[300px] overflow-y-auto">
                {itens.filter(i => i.is_disponivel).map(i => (
                  <button type="button" key={i.id} onClick={() => add(i)} className="px-3 py-2 rounded-lg border dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-left text-sm">
                    {i.nome} — {formatCurrency(i.preco)}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Carrinho</p>
            <ul className="space-y-2 mb-4">
              {carrinho.map(x => (
                <li key={x.item.id} className="flex justify-between items-center">
                  <span>{x.item.nome} x{x.qtd}</span>
                  <div className="flex items-center gap-2">
                    <span>{formatCurrency(Number(x.item.preco) * x.qtd)}</span>
                    <button type="button" onClick={() => remove(x.item.id)} className="text-red-600 text-sm">Remover</button>
                  </div>
                </li>
              ))}
            </ul>
            <p className="font-bold text-lg mb-2">Total: {formatCurrency(total)}</p>
            <button onClick={finalizar} disabled={carrinho.length === 0} className="w-full py-3 rounded-lg text-white font-bold min-h-[44px] disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>Finalizar venda</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ——— Modal Nota Fiscal (entrada: upload XML, fornecedores, listagem) ———
export function ModalNotaFiscal({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([]);
  const [notas, setNotas] = useState<NotaFiscalEntrada[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    numero: '',
    fornecedor_id: '',
    data_emissao: '',
    data_entrada: '',
    valor_total: '',
    observacoes: ''
  });
  const [xmlFile, setXmlFile] = useState<File | null>(null);
  const [showModalFornecedor, setShowModalFornecedor] = useState(false);

  const loadFornecedores = useCallback(async () => {
    try {
      const res = await clinicaApiClient.get<Fornecedor[] | { results?: Fornecedor[] }>('/restaurante/fornecedores/');
      setFornecedores(Array.isArray(res.data) ? res.data : (res.data as { results?: Fornecedor[] })?.results ?? []);
    } catch {
      setFornecedores([]);
    }
  }, []);

  const loadNotas = useCallback(async () => {
    try {
      const res = await clinicaApiClient.get<NotaFiscalEntrada[] | { results?: NotaFiscalEntrada[] }>('/restaurante/notas-fiscais/');
      setNotas(Array.isArray(res.data) ? res.data : (res.data as { results?: NotaFiscalEntrada[] })?.results ?? []);
    } catch {
      setNotas([]);
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([loadFornecedores(), loadNotas()]);
    setLoading(false);
  }, [loadFornecedores, loadNotas]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.numero.trim() || !form.fornecedor_id) {
      toast.error('Preencha número da NF e fornecedor');
      return;
    }
    setSaving(true);
    try {
      const payload = new FormData();
      payload.append('numero', form.numero.trim());
      payload.append('fornecedor', form.fornecedor_id);
      if (form.data_emissao) payload.append('data_emissao', form.data_emissao);
      if (form.data_entrada) payload.append('data_entrada', form.data_entrada);
      payload.append('valor_total', form.valor_total || '0');
      if (form.observacoes) payload.append('observacoes', form.observacoes);
      if (xmlFile) payload.append('xml_file', xmlFile);
      await clinicaApiClient.post('/restaurante/notas-fiscais/', payload);
      toast.success('Nota fiscal registrada');
      setForm({ numero: '', fornecedor_id: '', data_emissao: '', data_entrada: '', valor_total: '', observacoes: '' });
      setXmlFile(null);
      setShowForm(false);
      loadNotas();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-2xl w-full shadow-xl my-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📄 Entrada de Nota Fiscal</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
          Registro de entrada de NF-e de compras: upload de XML, vinculação a fornecedores e estoque.
        </p>

        {loading ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : showForm ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número da NF *</label>
              <input type="text" name="numero" value={form.numero} onChange={handleChange} placeholder="Ex: 000.000.000" required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fornecedor *</label>
                <select name="fornecedor_id" value={form.fornecedor_id} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                  <option value="">Selecione...</option>
                  {fornecedores.filter(f => f).map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}
                </select>
              </div>
              <button type="button" onClick={() => setShowModalFornecedor(true)} className="mt-6 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm" title="Cadastrar fornecedor">+ Fornecedor</button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data emissão</label>
                <input type="date" name="data_emissao" value={form.data_emissao} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data entrada</label>
                <input type="date" name="data_entrada" value={form.data_entrada} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor total (R$)</label>
              <input type="number" name="valor_total" value={form.valor_total} onChange={handleChange} step="0.01" min="0" placeholder="0,00" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Arquivo XML da NF-e (opcional)</label>
              <input type="file" accept=".xml,application/xml" onChange={e => setXmlFile(e.target.files?.[0] || null)} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white text-sm" />
              {xmlFile && <p className="text-xs text-green-600 dark:text-green-400 mt-1">📎 {xmlFile.name}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
              <textarea name="observacoes" value={form.observacoes} onChange={handleChange} rows={2} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => { setShowForm(false); setXmlFile(null); }} disabled={saving} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px] disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Registrar NF'}</button>
            </div>
          </form>
        ) : (
          <>
            <div className="flex justify-end mb-3">
              <button type="button" onClick={() => setShowForm(true)} className="px-4 py-2 rounded-lg text-white text-sm min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Nova Nota Fiscal</button>
            </div>
            {notas.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p className="mb-2">Nenhuma nota fiscal registrada.</p>
                <p className="text-sm mb-4">Cadastre fornecedores e registre a primeira NF (com ou sem upload de XML).</p>
                <button type="button" onClick={() => setShowForm(true)} className="px-4 py-2 rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>+ Registrar primeira NF</button>
              </div>
            ) : (
              <ul className="space-y-3 max-h-[320px] overflow-y-auto">
                {notas.map(n => (
                  <li key={n.id} className="flex flex-wrap items-center justify-between p-3 border dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700/50 gap-2">
                    <div>
                      <span className="font-semibold text-gray-900 dark:text-white">NF {n.numero}</span>
                      <span className="text-gray-600 dark:text-gray-400 ml-2">— {n.fornecedor_nome || 'Fornecedor'}</span>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Emissão: {formatDate(n.data_emissao)} · Entrada: {formatDate(n.data_entrada)} · {formatCurrency(n.valor_total)}
                        {n.xml_file && <span className="ml-2">📎 XML</span>}
                        {n.aplicado_estoque && <span className="ml-2 text-green-600 dark:text-green-400">✓ Estoque</span>}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            <div className="flex justify-end gap-2 mt-4 pt-4 border-t dark:border-gray-600">
              <button type="button" onClick={() => setShowModalFornecedor(true)} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">👥 Fornecedores</button>
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
            </div>
          </>
        )}

        {showModalFornecedor && (
          <ModalFornecedoresRestaurante loja={loja} onClose={() => { setShowModalFornecedor(false); loadFornecedores(); }} />
        )}
      </div>
    </div>
  );
}

// Formata CNPJ para exibição (14 dígitos → 00.000.000/0000-00)
function formatCnpjDisplay(value: string): string {
  const n = (value || '').replace(/\D/g, '');
  if (n.length <= 2) return n;
  if (n.length <= 5) return n.slice(0, 2) + '.' + n.slice(2);
  if (n.length <= 8) return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5);
  if (n.length <= 12) return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5, 8) + '/' + n.slice(8);
  return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5, 8) + '/' + n.slice(8, 12) + '-' + n.slice(12, 14);
}

// ——— Modal Fornecedores (dentro do contexto NF) ———
export function ModalFornecedoresRestaurante({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [lista, setLista] = useState<Fornecedor[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nome: '', cnpj: '', email: '', telefone: '', endereco: '' });
  const [saving, setSaving] = useState(false);
  const [buscarCnpjLoading, setBuscarCnpjLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await clinicaApiClient.get<Fornecedor[] | { results?: Fornecedor[] }>('/restaurante/fornecedores/');
      setLista(Array.isArray(res.data) ? res.data : (res.data as { results?: Fornecedor[] })?.results ?? []);
    } catch {
      setLista([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  /** Consulta CNPJ na BrasilAPI e preenche nome e endereço automaticamente */
  const buscarCnpj = async () => {
    const cnpj = form.cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) {
      toast.error('Informe um CNPJ válido com 14 dígitos para buscar.');
      return;
    }
    setBuscarCnpjLoading(true);
    try {
      const res = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
      if (!res.ok) {
        toast.error('CNPJ não encontrado ou serviço indisponível.');
        return;
      }
      const data = await res.json();
      const partes: string[] = [];
      if (data.logradouro) partes.push(data.logradouro);
      if (data.numero) partes.push(data.numero);
      if (data.complemento) partes.push(data.complemento);
      if (data.bairro) partes.push(data.bairro);
      if (data.municipio) partes.push(data.municipio);
      if (data.uf) partes.push(data.uf);
      if (data.cep) partes.push(`CEP ${(data.cep || '').replace(/\D/g, '').slice(0, 5)}-${(data.cep || '').replace(/\D/g, '').slice(5, 8)}`);
      const endereco = partes.join(', ');
      setForm(prev => ({
        ...prev,
        nome: data.razao_social || data.nome_fantasia || prev.nome,
        endereco: endereco || prev.endereco,
      }));
      toast.success('Dados do CNPJ preenchidos.');
    } catch {
      toast.error('Erro ao consultar CNPJ. Tente novamente.');
    } finally {
      setBuscarCnpjLoading(false);
    }
  };

  const handleCnpjChange = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 14);
    setForm(f => ({ ...f, cnpj: formatCnpjDisplay(digits) }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nome.trim()) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      await clinicaApiClient.post('/restaurante/fornecedores/', form);
      toast.success('Fornecedor cadastrado');
      setForm({ nome: '', cnpj: '', email: '', telefone: '', endereco: '' });
      setShowForm(false);
      load();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[60] p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>👥 Fornecedores</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        {loading ? <div className="text-center py-6 text-gray-500">Carregando...</div> : showForm ? (
          <form onSubmit={handleSubmit} className="space-y-3">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome/Razão Social *</label><input type="text" value={form.nome} onChange={e => setForm(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Nome do fornecedor" /></div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CNPJ</label>
              <div className="flex gap-2">
                <input type="text" value={form.cnpj} onChange={e => handleCnpjChange(e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="00.000.000/0000-00" maxLength={18} />
                <button type="button" onClick={buscarCnpj} disabled={buscarCnpjLoading || form.cnpj.replace(/\D/g, '').length !== 14} className="px-3 py-2 rounded-lg text-white text-sm whitespace-nowrap disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }} title="Buscar dados na Receita Federal">{buscarCnpjLoading ? 'Buscando...' : 'Buscar CNPJ'}</button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Digite o CNPJ e clique em Buscar para preencher nome e endereço automaticamente.</p>
            </div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label><input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label><input type="tel" value={form.telefone} onChange={e => setForm(f => ({ ...f, telefone: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço</label><input type="text" value={form.endereco} onChange={e => setForm(f => ({ ...f, endereco: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Preenchido automaticamente ao buscar CNPJ" /></div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowForm(false)} disabled={saving} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">Voltar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Cadastrar'}</button>
            </div>
          </form>
        ) : (
          <>
            {lista.length === 0 ? <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Nenhum fornecedor. Cadastre o primeiro.</p> : <ul className="space-y-2 max-h-48 overflow-y-auto mb-4">{lista.map(f => <li key={f.id} className="text-sm text-gray-900 dark:text-white">{f.nome}{f.cnpj ? ` · ${f.cnpj}` : ''}</li>)}</ul>}
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(true)} className="px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Fornecedor</button>
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">Fechar</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const UNIDADES_ESTOQUE = [
  { value: 'UN', label: 'Unidade' },
  { value: 'KG', label: 'Quilograma (kg)' },
  { value: 'L', label: 'Litro (L)' },
  { value: 'CX', label: 'Caixa' },
  { value: 'PCT', label: 'Pacote' },
];

// ——— Modal Estoque (controle completo: itens, entradas/saídas, alertas) ———
export function ModalEstoque({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [itens, setItens] = useState<EstoqueItem[]>([]);
  const [alertas, setAlertas] = useState<EstoqueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showMovimento, setShowMovimento] = useState<EstoqueItem | null>(null);
  const [form, setForm] = useState({ nome: '', unidade: 'UN', quantidade_minima: '0', observacoes: '' });
  const [movForm, setMovForm] = useState({ tipo: 'entrada' as 'entrada' | 'saida', quantidade: '', observacao: '' });
  const [saving, setSaving] = useState(false);

  const loadItens = useCallback(async () => {
    try {
      const [resItens, resAlertas] = await Promise.all([
        clinicaApiClient.get<EstoqueItem[] | { results?: EstoqueItem[] }>('/restaurante/estoque-itens/'),
        clinicaApiClient.get<EstoqueItem[]>('/restaurante/estoque-itens/alertas/'),
      ]);
      setItens(Array.isArray(resItens.data) ? resItens.data : (resItens.data as { results?: EstoqueItem[] })?.results ?? []);
      setAlertas(Array.isArray(resAlertas.data) ? resAlertas.data : []);
    } catch {
      setItens([]);
      setAlertas([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadItens(); }, [loadItens]);

  const handleSaveItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nome.trim()) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      await clinicaApiClient.post('/restaurante/estoque-itens/', { ...form, quantidade_atual: 0 });
      toast.success('Item cadastrado');
      setForm({ nome: '', unidade: 'UN', quantidade_minima: '0', observacoes: '' });
      setShowForm(false);
      loadItens();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleMovimentar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showMovimento || !movForm.quantidade.trim()) return;
    const qty = parseFloat(movForm.quantidade.replace(',', '.'));
    if (isNaN(qty) || qty <= 0) { toast.error('Quantidade inválida'); return; }
    setSaving(true);
    try {
      await clinicaApiClient.post(`/restaurante/estoque-itens/${showMovimento.id}/movimentar/`, {
        tipo: movForm.tipo,
        quantidade: qty,
        observacao: movForm.observacao || undefined,
      });
      toast.success(movForm.tipo === 'entrada' ? 'Entrada registrada' : 'Saída registrada');
      setShowMovimento(null);
      setMovForm({ tipo: 'entrada', quantidade: '', observacao: '' });
      loadItens();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-2xl w-full shadow-xl my-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📦 Controle de Estoque</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">Cadastro de itens, entradas/saídas e alertas de mínimo.</p>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Carregando...</div>
        ) : showForm ? (
          <form onSubmit={handleSaveItem} className="space-y-3">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome do item *</label><input type="text" value={form.nome} onChange={e => setForm(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: Arroz, Óleo, Carne kg" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Unidade</label><select value={form.unidade} onChange={e => setForm(f => ({ ...f, unidade: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">{UNIDADES_ESTOQUE.map(u => <option key={u.value} value={u.value}>{u.label}</option>)}</select></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantidade mínima (alerta)</label><input type="text" value={form.quantidade_minima} onChange={e => setForm(f => ({ ...f, quantidade_minima: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="0" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label><input type="text" value={form.observacoes} onChange={e => setForm(f => ({ ...f, observacoes: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowForm(false)} disabled={saving} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">Voltar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Cadastrar'}</button>
            </div>
          </form>
        ) : showMovimento ? (
          <form onSubmit={handleMovimentar} className="space-y-3">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Movimentar: <strong>{showMovimento.nome}</strong> (atual: {showMovimento.quantidade_atual} {showMovimento.unidade})</p>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label><select value={movForm.tipo} onChange={e => setMovForm(f => ({ ...f, tipo: e.target.value as 'entrada' | 'saida' }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"><option value="entrada">Entrada</option><option value="saida">Saída</option></select></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantidade *</label><input type="text" value={movForm.quantidade} onChange={e => setMovForm(f => ({ ...f, quantidade: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: 10 ou 2,5" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observação</label><input type="text" value={movForm.observacao} onChange={e => setMovForm(f => ({ ...f, observacao: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => { setShowMovimento(null); setMovForm({ tipo: 'entrada', quantidade: '', observacao: '' }); }} disabled={saving} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">Voltar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Registrar'}</button>
            </div>
          </form>
        ) : (
          <>
            {alertas.length > 0 && (
              <div className="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                <p className="text-sm font-semibold text-amber-800 dark:text-amber-200 mb-2">⚠️ Alertas de estoque mínimo</p>
                <ul className="text-sm text-amber-700 dark:text-amber-300 space-y-1">
                  {alertas.map(a => (
                    <li key={a.id}>{a.nome}: {a.quantidade_atual} {a.unidade} (mín: {a.quantidade_minima})</li>
                  ))}
                </ul>
              </div>
            )}
            {itens.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Nenhum item de estoque. Cadastre o primeiro.</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
                {itens.map(item => (
                  <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{item.nome}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{item.quantidade_atual} {item.unidade} {item.quantidade_minima && parseFloat(item.quantidade_minima) > 0 && parseFloat(item.quantidade_atual) < parseFloat(item.quantidade_minima) && <span className="text-amber-600">(abaixo do mínimo)</span>}</p>
                    </div>
                    <button type="button" onClick={() => setShowMovimento(item)} className="px-3 py-1.5 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>Entrada/Saída</button>
                  </div>
                ))}
              </div>
            )}
            <div className="flex flex-wrap justify-end gap-2">
              <button type="button" onClick={() => setShowForm(true)} className="px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Item</button>
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">Fechar</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ——— Modal Balança (registro de peso por item, integração com estoque) ———
export function ModalBalanca({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [itens, setItens] = useState<EstoqueItem[]>([]);
  const [registros, setRegistros] = useState<RegistroPesoBalança[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ estoque_item_id: '', peso_kg: '', adicionar_ao_estoque: true, observacao: '' });

  const load = useCallback(async () => {
    try {
      const [resItens, resReg] = await Promise.all([
        clinicaApiClient.get<EstoqueItem[] | { results?: EstoqueItem[] }>('/restaurante/estoque-itens/'),
        clinicaApiClient.get<RegistroPesoBalança[] | { results?: RegistroPesoBalança[] }>('/restaurante/registros-peso-balanca/'),
      ]);
      setItens(Array.isArray(resItens.data) ? resItens.data : (resItens.data as { results?: EstoqueItem[] })?.results ?? []);
      setRegistros(Array.isArray(resReg.data) ? resReg.data : (resReg.data as { results?: RegistroPesoBalança[] })?.results ?? []);
    } catch {
      setItens([]);
      setRegistros([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleRegistrar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.estoque_item_id || !form.peso_kg.trim()) { toast.error('Selecione o item e informe o peso'); return; }
    const peso = parseFloat(form.peso_kg.replace(',', '.'));
    if (isNaN(peso) || peso <= 0) { toast.error('Peso inválido'); return; }
    try {
      await clinicaApiClient.post('/restaurante/registros-peso-balanca/', {
        estoque_item: Number(form.estoque_item_id),
        peso_kg: peso,
        adicionar_ao_estoque: form.adicionar_ao_estoque,
        observacao: form.observacao || undefined,
      });
      toast.success(form.adicionar_ao_estoque ? 'Peso registrado e adicionado ao estoque' : 'Peso registrado');
      setForm({ estoque_item_id: '', peso_kg: '', adicionar_ao_estoque: true, observacao: '' });
      load();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    }
  };

  const itensKg = itens.filter(i => i.unidade === 'KG');

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full shadow-xl my-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>⚖️ Balança</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">Registro de peso (kg) por item. Opção de adicionar automaticamente ao estoque.</p>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Carregando...</div>
        ) : (
          <>
            <form onSubmit={handleRegistrar} className="space-y-3 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Item (por kg) *</label>
                <select value={form.estoque_item_id} onChange={e => setForm(f => ({ ...f, estoque_item_id: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                  <option value="">Selecione...</option>
                  {(itensKg.length ? itensKg : itens).map(i => (
                    <option key={i.id} value={i.id}>{i.nome} ({i.unidade})</option>
                  ))}
                </select>
                {itensKg.length === 0 && itens.length > 0 && <p className="text-xs text-amber-600 mt-1">Cadastre itens com unidade KG no Estoque para pesar.</p>}
              </div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Peso (kg) *</label><input type="text" value={form.peso_kg} onChange={e => setForm(f => ({ ...f, peso_kg: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: 2,5" /></div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="add_estoque" checked={form.adicionar_ao_estoque} onChange={e => setForm(f => ({ ...f, adicionar_ao_estoque: e.target.checked }))} className="rounded" />
                <label htmlFor="add_estoque" className="text-sm text-gray-700 dark:text-gray-300">Adicionar ao estoque (entrada)</label>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observação</label><input type="text" value={form.observacao} onChange={e => setForm(f => ({ ...f, observacao: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
              <button type="submit" className="w-full px-4 py-2 rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>Registrar peso</button>
            </form>
            {registros.length > 0 && (
              <div className="border-t dark:border-gray-600 pt-4">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Últimos registros</p>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 max-h-32 overflow-y-auto">
                  {registros.slice(0, 10).map(r => (
                    <li key={r.id}>{r.estoque_item_nome || 'Item'}: {r.peso_kg} kg {r.adicionar_ao_estoque && '(entrada)'} — {formatDateTime(r.created_at)}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex justify-end mt-4">
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">Fechar</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ——— Modal Funcionários ———
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
              <input type="tel" value={form.telefone} onChange={e => setForm(f => ({ ...f, telefone: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
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
