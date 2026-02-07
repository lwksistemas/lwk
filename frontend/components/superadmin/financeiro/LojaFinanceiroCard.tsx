'use client';

import { useState } from 'react';

interface AsaasPayment {
  id: number;
  asaas_id: string;
  value: string;
  status: string;
  status_display: string;
  due_date: string;
  payment_date: string | null;
  bank_slip_url: string;
}

interface LojaFinanceiroCardProps {
  loja: {
    id: number;
    loja_slug: string;
    loja_nome: string;
    plano_nome: string;
    plano_valor: string;
    ativa: boolean;
    data_vencimento: string;
    current_payment_data: AsaasPayment | null;
    total_payments: number;
  };
  pagamentos: AsaasPayment[];
  onAtualizarStatus: (paymentId: number) => void;
  onNovaCobranca: (lojaId: number) => void;
  formatDate: (date: string) => string;
  formatCurrency: (value: number) => string;
}

export function LojaFinanceiroCard({
  loja,
  pagamentos,
  onAtualizarStatus,
  onNovaCobranca,
  formatDate,
  formatCurrency
}: LojaFinanceiroCardProps) {
  const [expanded, setExpanded] = useState(false);

  const lojaPagamentos = pagamentos.filter(p => 
    p.asaas_id.includes(loja.loja_slug) || 
    (p as any).external_reference?.includes(loja.loja_slug)
  );

  const pagamentosPagos = lojaPagamentos.filter(p => p.status === 'RECEIVED' || p.status === 'CONFIRMED');
  const pagamentosPendentes = lojaPagamentos.filter(p => p.status === 'PENDING');

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      {/* Header - Sempre visível */}
      <div 
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 flex-1">
            {/* Nome da Loja */}
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {loja.loja_nome}
              </h3>
              <p className="text-sm text-gray-500">
                {loja.plano_nome} - {formatCurrency(parseFloat(loja.plano_valor))}
              </p>
            </div>

            {/* Status */}
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                loja.ativa 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {loja.ativa ? 'Ativa' : 'Inativa'}
              </span>
            </div>

            {/* Próximo Vencimento */}
            <div className="text-right">
              <p className="text-xs text-gray-500">Próximo Vencimento</p>
              <p className="text-sm font-semibold text-gray-900">
                {formatDate(loja.data_vencimento)}
              </p>
            </div>

            {/* Estatísticas Rápidas */}
            <div className="flex items-center space-x-4 text-sm">
              <div className="text-center">
                <p className="text-xs text-gray-500">Total</p>
                <p className="font-semibold text-gray-900">{loja.total_payments}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-500">Pagos</p>
                <p className="font-semibold text-green-600">{pagamentosPagos.length}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-500">Pendentes</p>
                <p className="font-semibold text-yellow-600">{pagamentosPendentes.length}</p>
              </div>
            </div>

            {/* Ícone Expandir */}
            <div className="text-gray-400">
              {expanded ? '▼' : '▶'}
            </div>
          </div>
        </div>
      </div>

      {/* Conteúdo Expandido - Histórico de Pagamentos */}
      {expanded && (
        <div className="border-t border-gray-200 bg-gray-50">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-gray-700">
                📋 Histórico de Pagamentos ({lojaPagamentos.length})
              </h4>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onNovaCobranca(loja.id);
                }}
                className="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
              >
                ➕ Nova Cobrança
              </button>
            </div>

            {lojaPagamentos.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                Nenhum pagamento encontrado
              </p>
            ) : (
              <div className="space-y-2">
                {lojaPagamentos.map((pagamento) => (
                  <div
                    key={pagamento.id}
                    className="bg-white rounded border border-gray-200 p-3 hover:border-purple-300 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      {/* Info do Pagamento */}
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            pagamento.status === 'RECEIVED' || pagamento.status === 'CONFIRMED'
                              ? 'bg-green-100 text-green-800'
                              : pagamento.status === 'PENDING'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {pagamento.status_display}
                          </span>
                          <span className="text-sm font-semibold text-gray-900">
                            {formatCurrency(parseFloat(pagamento.value))}
                          </span>
                          <span className="text-xs text-gray-500">
                            Vencimento: {formatDate(pagamento.due_date)}
                          </span>
                          {pagamento.payment_date && (
                            <span className="text-xs text-green-600">
                              Pago em: {formatDate(pagamento.payment_date)}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Ações */}
                      <div className="flex items-center space-x-2">
                        {pagamento.bank_slip_url && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              window.open(pagamento.bank_slip_url, '_blank');
                            }}
                            className="px-3 py-1 text-xs bg-orange-500 text-white rounded hover:bg-orange-600 transition-colors"
                          >
                            📄 Boleto
                          </button>
                        )}
                        {pagamento.status === 'PENDING' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onAtualizarStatus(pagamento.id);
                            }}
                            className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                          >
                            🔄 Atualizar
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
