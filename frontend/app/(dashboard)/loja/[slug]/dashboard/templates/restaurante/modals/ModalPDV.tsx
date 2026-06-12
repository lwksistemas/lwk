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
