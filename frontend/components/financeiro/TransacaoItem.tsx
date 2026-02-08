/**
 * Item de Transação
 * Componente reutilizável para lista de transações
 */

import { formatCurrency, formatDate, getStatusBadgeClass } from '@/lib/financeiro-helpers';
import type { Transacao } from '@/types/financeiro';

interface TransacaoItemProps {
  transacao: Transacao;
  corPrimaria: string;
  onMarcarPago: (id: number) => void;
  onExcluir: (id: number, descricao: string) => void;
}

export function TransacaoItem({
  transacao,
  corPrimaria,
  onMarcarPago,
  onExcluir
}: TransacaoItemProps) {
  return (
    <div className="flex items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <div
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: transacao.categoria_cor }}
          />
          <p className="font-semibold text-gray-900 dark:text-white truncate">
            {transacao.descricao}
          </p>
          <span className={`px-2 py-0.5 text-xs rounded-full whitespace-nowrap ${getStatusBadgeClass(transacao.status)}`}>
            {transacao.status}
          </span>
          {transacao.esta_atrasado && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
              ⚠️ Atrasado
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          📁 {transacao.categoria_nome} • 📅 Venc: {formatDate(transacao.data_vencimento)}
          {transacao.data_pagamento && ` • ✅ Pago: ${formatDate(transacao.data_pagamento)}`}
          {transacao.cliente_nome && ` • 👤 ${transacao.cliente_nome}`}
        </p>
      </div>
      
      <div className="flex items-center gap-4 ml-4">
        <p className="text-lg font-bold whitespace-nowrap" style={{ color: corPrimaria }}>
          {formatCurrency(transacao.valor)}
        </p>
        <div className="flex gap-2">
          {transacao.status === 'pendente' && (
            <button
              onClick={() => onMarcarPago(transacao.id)}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors whitespace-nowrap"
              title="Marcar como pago"
            >
              ✓ Pagar
            </button>
          )}
          <button
            onClick={() => onExcluir(transacao.id, transacao.descricao)}
            className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            title="Excluir"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>
  );
}
