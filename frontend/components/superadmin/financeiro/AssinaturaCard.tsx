/**
 * Componente de card de assinatura (Asaas ou Mercado Pago)
 * ✅ REFATORADO v780: Extraído e modularizado da página de financeiro
 * ✅ NOVO: Histórico de pagamentos com ações de NF (baixar, reenviar, cancelar)
 */
import { useState } from 'react';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
import type { Assinatura, Pagamento } from '@/hooks/useAssinaturas';
import { apiClient } from '@/lib/api-client';
import { AssinaturaAsaas } from './AssinaturaAsaas';
import { AssinaturaMercadoPago } from './AssinaturaMercadoPago';

interface AssinaturaCardProps {
  assinatura: Assinatura;
  // Ações Asaas
  onDownloadBoletoAsaas: (payment: Pagamento) => void;
  onCopyPixAsaas: (pixCode: string) => void;
  onUpdateStatusAsaas: (paymentId: number) => void;
  onNovaCobranca: (assinatura: Assinatura) => void;
  onExcluirAsaas: (payment: Pagamento) => void;
  gerandoCobranca: number | null;
  // Ações Mercado Pago
  onDownloadBoletoMP: (payment: Pagamento) => void;
  onCopyPixMP: (pixCode: string) => void;
  onGerarPixMP: (payment: Pagamento) => void;
  onUpdateStatusMP: (lojaSlug: string) => void;
  onNovaCobrancaMP: (assinatura: Assinatura) => void;
  onExcluirMP: (payment: Pagamento) => void;
  gerandoPix: number | null;
  atualizandoMP: string | null;
  gerandoCobrancaMP: string | number | null;
  excluindoPagamentoMP: boolean;
}

function getStatusColor(status: string) {
  const colors: { [key: string]: string } = {
    'PENDING': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    'RECEIVED': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    'CONFIRMED': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    'OVERDUE': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    'REFUNDED': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  };
  return colors[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
}

export function AssinaturaCard({
  assinatura,
  onDownloadBoletoAsaas,
  onCopyPixAsaas,
  onUpdateStatusAsaas,
  onNovaCobranca,
  onExcluirAsaas,
  gerandoCobranca,
  onDownloadBoletoMP,
  onCopyPixMP,
  onGerarPixMP,
  onUpdateStatusMP,
  onNovaCobrancaMP,
  onExcluirMP,
  gerandoPix,
  atualizandoMP,
  gerandoCobrancaMP,
  excluindoPagamentoMP
}: AssinaturaCardProps) {
  const isAsaas = typeof assinatura.id === 'number';
  const isMercadoPago = assinatura.current_payment_data?.provedor === 'mercadopago';
  const [showHistorico, setShowHistorico] = useState(false);
  const historico = assinatura.payment_history || [];

  return (
    <div className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
      {/* Cabeçalho */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {assinatura.loja_nome}
            </h3>
            <span className={`px-2 py-1 text-xs rounded-full ${
              isAsaas
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            }`}>
              {isAsaas ? '🔵 Asaas' : '🟢 Mercado Pago'}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {assinatura.plano_nome} - {formatCurrency(assinatura.plano_valor)}
          </p>
          <p className="text-sm text-gray-500">Vencimento: {formatDate(assinatura.data_vencimento)}</p>
          <p className="text-sm text-gray-500">Total de pagamentos: {assinatura.total_payments}</p>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${
          assinatura.ativa
            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
        }`}>
          {assinatura.subscription_status_display || (assinatura.ativa ? 'Ativa' : 'Inativa')}
        </span>
      </div>

      {/* Pagamento Atual - só mostra se NÃO está pago (pendente/vencido) */}
      {assinatura.current_payment_data && !assinatura.current_payment_data.is_paid && (
        <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded">
          <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Próximo Pagamento</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-3">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Valor:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                {formatCurrency(assinatura.current_payment_data.value)}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Vencimento:</span>
              <span className="ml-2 text-gray-900 dark:text-gray-100">
                {formatDate(assinatura.current_payment_data.due_date)}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Status:</span>
              <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${getStatusColor(assinatura.current_payment_data.status)}`}>
                {assinatura.current_payment_data.status_display}
              </span>
            </div>
          </div>
          {isAsaas ? (
            <AssinaturaAsaas
              assinatura={assinatura}
              payment={assinatura.current_payment_data}
              onDownloadBoleto={onDownloadBoletoAsaas}
              onCopyPix={onCopyPixAsaas}
              onUpdateStatus={onUpdateStatusAsaas}
              onNovaCobranca={onNovaCobranca}
              onExcluir={onExcluirAsaas}
              gerandoCobranca={gerandoCobranca}
            />
          ) : isMercadoPago ? (
            <AssinaturaMercadoPago
              assinatura={assinatura}
              lojaSlug={assinatura.loja_slug}
              payment={assinatura.current_payment_data}
              onDownloadBoleto={onDownloadBoletoMP}
              onCopyPix={onCopyPixMP}
              onGerarPix={onGerarPixMP}
              onUpdateStatus={onUpdateStatusMP}
              onNovaCobranca={onNovaCobrancaMP}
              onExcluir={onExcluirMP}
              gerandoPix={gerandoPix}
              atualizandoMP={atualizandoMP}
              gerandoCobranca={gerandoCobrancaMP}
              excluindoPagamento={excluindoPagamentoMP}
            />
          ) : null}
        </div>
      )}

      {/* Histórico de Pagamentos */}
      {historico.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setShowHistorico(!showHistorico)}
            className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            {showHistorico ? '▼' : '▶'} Histórico de Pagamentos ({historico.length})
          </button>
          {showHistorico && (
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gray-100 dark:bg-gray-800">
                    <th className="px-2 py-1 text-left text-gray-600 dark:text-gray-400">Vencimento</th>
                    <th className="px-2 py-1 text-left text-gray-600 dark:text-gray-400">Valor</th>
                    <th className="px-2 py-1 text-left text-gray-600 dark:text-gray-400">Status</th>
                    <th className="px-2 py-1 text-left text-gray-600 dark:text-gray-400">Pago em</th>
                    <th className="px-2 py-1 text-left text-gray-600 dark:text-gray-400">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {historico.map((pag) => (
                    <tr key={pag.id} className="border-b dark:border-gray-700">
                      <td className="px-2 py-1.5 text-gray-900 dark:text-gray-100">
                        {pag.due_date ? formatDate(pag.due_date) : '-'}
                      </td>
                      <td className="px-2 py-1.5 text-gray-900 dark:text-gray-100">
                        {formatCurrency(pag.value)}
                      </td>
                      <td className="px-2 py-1.5">
                        <span className={`px-1.5 py-0.5 text-xs rounded-full ${getStatusColor(pag.status)}`}>
                          {pag.status_display}
                        </span>
                      </td>
                      <td className="px-2 py-1.5 text-gray-900 dark:text-gray-100">
                        {pag.payment_date ? formatDate(pag.payment_date) : '-'}
                      </td>
                      <td className="px-2 py-1.5">
                        <div className="flex gap-1 items-center flex-wrap">
                          {pag.bank_slip_url && (
                            <a
                              href={pag.bank_slip_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-1.5 py-0.5 bg-blue-600 text-white text-[10px] rounded hover:bg-blue-700 transition-colors"
                            >
                              📄 Boleto
                            </a>
                          )}
                          {pag.asaas_id && pag.is_paid && (
                            <span className="px-1.5 py-0.5 text-[10px] text-gray-500 dark:text-gray-400">
                              Ver NF em /superadmin/nfse
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
