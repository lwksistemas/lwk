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
import { STATUS_MESA, CARGO_FUNCIONARIO, UNIDADES_ESTOQUE } from '../types';

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
