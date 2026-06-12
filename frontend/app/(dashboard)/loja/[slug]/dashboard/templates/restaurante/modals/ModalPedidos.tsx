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
