/**
 * Componente de ações para assinaturas Asaas
 * Botões de boleto, PIX, status, nova cobrança e excluir
 * (Botões de NF ficam no histórico de pagamentos)
 */
import type { Pagamento, Assinatura } from '@/hooks/useAssinaturas';

interface AssinaturaAsaasProps {
  assinatura: Assinatura;
  payment: Pagamento;
  onDownloadBoleto: (payment: Pagamento) => void;
  onCopyPix: (pixCode: string) => void;
  onUpdateStatus: (paymentId: number) => void;
  onNovaCobranca: (assinatura: Assinatura) => void;
  onExcluir: (payment: Pagamento) => void;
  gerandoCobranca: number | null;
}

export function AssinaturaAsaas({
  assinatura,
  payment,
  onDownloadBoleto,
  onCopyPix,
  onUpdateStatus,
  onNovaCobranca,
  onExcluir,
  gerandoCobranca
}: AssinaturaAsaasProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onDownloadBoleto(payment)}
        className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
      >
        📄 Baixar Boleto
      </button>

      {payment.pix_copy_paste && (
        <button
          onClick={() => onCopyPix(payment.pix_copy_paste)}
          className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
        >
          📱 Copiar PIX
        </button>
      )}

      <button
        onClick={() => {
          const id = payment.id;
          if (id != null) onUpdateStatus(id);
        }}
        disabled={payment.id == null}
        className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        🔄 Atualizar Status
      </button>

      <button
        onClick={() => onNovaCobranca(assinatura)}
        disabled={gerandoCobranca === assinatura.id}
        className="px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 disabled:opacity-50 transition-colors"
      >
        {gerandoCobranca === assinatura.id ? 'Gerando...' : '➕ Nova Cobrança'}
      </button>

      <button
        onClick={() => onExcluir(payment)}
        disabled={payment.is_paid}
        className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title={payment.is_paid ? 'Não é possível excluir cobrança paga' : 'Excluir cobrança'}
      >
        🗑️ Excluir
      </button>
    </div>
  );
}
