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
