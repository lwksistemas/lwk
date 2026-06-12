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
