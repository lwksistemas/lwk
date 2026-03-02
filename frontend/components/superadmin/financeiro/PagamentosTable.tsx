/**
 * Componente de tabela de pagamentos
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
import type { Pagamento } from '@/hooks/useAssinaturas';

interface PagamentosTableProps {
  pagamentos: Pagamento[];
  onDownloadBoleto: (payment: Pagamento) => void;
  onCopyPix: (pixCode: string) => void;
  onUpdateStatusAsaas?: (paymentId: number) => void;
  onExcluirAsaas?: (payment: Pagamento) => void;
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

export function PagamentosTable({
  pagamentos,
  onDownloadBoleto,
  onCopyPix,
  onUpdateStatusAsaas,
  onExcluirAsaas
}: PagamentosTableProps) {
  if (pagamentos.length === 0) {
    return (
      <p className="text-gray-500 dark:text-gray-400 text-center py-8">
        Nenhum pagamento encontrado.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            {['Cliente', 'Valor', 'Status', 'Vencimento', 'Provedor', 'Ações'].map((header) => (
              <th
                key={header}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {pagamentos.map((pagamento) => {
            const isAsaas = pagamento.provedor === 'asaas' || !pagamento.provedor;
            
            return (
              <tr
                key={pagamento.id ?? `pay-${pagamento.asaas_id}`}
                className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td className="px-6 py-4">
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {pagamento.customer_name}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {pagamento.customer_email}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">
                  {formatCurrency(pagamento.value)}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(pagamento.status)}`}>
                    {pagamento.status_display}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                  {formatDate(pagamento.due_date)}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    isAsaas 
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                      : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  }`}>
                    {isAsaas ? '🔵 Asaas' : '🟢 Mercado Pago'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm space-x-2">
                  <button
                    onClick={() => onDownloadBoleto(pagamento)}
                    className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
                  >
                    📄 PDF
                  </button>
                  {pagamento.pix_copy_paste && (
                    <button
                      onClick={() => onCopyPix(pagamento.pix_copy_paste)}
                      className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300 transition-colors"
                    >
                      📱 PIX
                    </button>
                  )}
                  {isAsaas && onUpdateStatusAsaas && (
                    <button
                      onClick={() => pagamento.id != null && onUpdateStatusAsaas(pagamento.id)}
                      disabled={pagamento.id == null}
                      className="text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      🔄 Status
                    </button>
                  )}
                  {isAsaas && onExcluirAsaas && (
                    <button
                      onClick={() => onExcluirAsaas(pagamento)}
                      disabled={pagamento.is_paid}
                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      title={pagamento.is_paid ? 'Não é possível excluir cobrança paga' : 'Excluir cobrança'}
                    >
                      🗑️ Excluir
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
