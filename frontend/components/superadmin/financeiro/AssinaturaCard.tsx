/**
 * Componente de card de assinatura (Asaas ou Mercado Pago)
 * ✅ REFATORADO v780: Extraído e modularizado da página de financeiro
 */
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';
import type { Assinatura } from '@/hooks/useAssinaturas';
import { AssinaturaAsaas } from './AssinaturaAsaas';
import { AssinaturaMercadoPago } from './AssinaturaMercadoPago';

interface AssinaturaCardProps {
  assinatura: Assinatura;
  // Asaas actions
  onDownloadBoletoAsaas: (payment: any) => void;
  onCopyPixAsaas: (pixCode: string) => void;
  onUpdateStatusAsaas: (paymentId: number) => void;
  onNovaCobranca: (assinatura: Assinatura) => void;
  onExcluirAsaas: (payment: any) => void;
  gerandoCobranca: number | null;
  // Mercado Pago actions
  onDownloadBoletoMP: (payment: any) => void;
  onCopyPixMP: (pixCode: string) => void;
  onGerarPixMP: (payment: any) => void;
  onUpdateStatusMP: (lojaSlug: string) => void;
  gerandoPix: number | null;
  atualizandoMP: string | null;
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
  gerandoPix,
  atualizandoMP
}: AssinaturaCardProps) {
  const isAsaas = typeof assinatura.id === 'number';
  const isMercadoPago = assinatura.current_payment_data?.provedor === 'mercadopago';
  
  return (
    <div className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
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
          <p className="text-sm text-gray-500 dark:text-gray-500">
            Vencimento: {formatDate(assinatura.data_vencimento)}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            Total de pagamentos: {assinatura.total_payments}
          </p>
        </div>
        
        <span className={`px-2 py-1 text-xs rounded-full ${
          assinatura.ativa 
            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
        }`}>
          {assinatura.subscription_status_display || (assinatura.ativa ? 'Ativa' : 'Inativa')}
        </span>
      </div>
      
      {/* Pagamento Atual */}
      {assinatura.current_payment_data && (
        <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded">
          <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
            Próximo Pagamento
          </h4>
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
              <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                getStatusColor(assinatura.current_payment_data.status)
              }`}>
                {assinatura.current_payment_data.status_display}
              </span>
            </div>
          </div>
          
          {/* Ações específicas por provedor */}
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
              lojaSlug={assinatura.loja_slug}
              payment={assinatura.current_payment_data}
              onDownloadBoleto={onDownloadBoletoMP}
              onCopyPix={onCopyPixMP}
              onGerarPix={onGerarPixMP}
              onUpdateStatus={onUpdateStatusMP}
              gerandoPix={gerandoPix}
              atualizandoMP={atualizandoMP}
            />
          ) : null}
        </div>
      )}
    </div>
  );
}
