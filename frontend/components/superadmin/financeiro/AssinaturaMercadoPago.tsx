/**
 * Componente de ações para assinaturas Mercado Pago
 * ✅ REFATORADO v780: Extraído da página de financeiro
 * ✅ ATUALIZADO v785: Adicionado Nova Cobrança e Excluir
 */
import type { Pagamento, Assinatura } from '@/hooks/useAssinaturas';

interface AssinaturaMercadoPagoProps {
  assinatura: Assinatura;
  lojaSlug: string;
  payment: Pagamento;
  onDownloadBoleto: (payment: Pagamento) => void;
  onCopyPix: (pixCode: string) => void;
  onGerarPix: (payment: Pagamento) => void;
  onUpdateStatus: (lojaSlug: string) => void;
  onNovaCobranca: (assinatura: Assinatura) => void;
  onExcluir: (payment: Pagamento) => void;
  gerandoPix: number | null;
  atualizandoMP: string | null;
  gerandoCobranca: string | number | null;
  excluindoPagamento: boolean;
}

export function AssinaturaMercadoPago({
  assinatura,
  lojaSlug,
  payment,
  onDownloadBoleto,
  onCopyPix,
  onGerarPix,
  onUpdateStatus,
  onNovaCobranca,
  onExcluir,
  gerandoPix,
  atualizandoMP,
  gerandoCobranca,
  excluindoPagamento
}: AssinaturaMercadoPagoProps) {
  const updatingThis = atualizandoMP === lojaSlug;
  const gerandoCobrancaThis = gerandoCobranca === lojaSlug || gerandoCobranca === assinatura.id;
  
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onDownloadBoleto(payment)}
        className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
      >
        📄 Baixar Boleto
      </button>
      
      {payment.pix_copy_paste ? (
        <button
          onClick={() => onCopyPix(payment.pix_copy_paste)}
          className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
        >
          📱 Copiar PIX
        </button>
      ) : payment.id != null && (
        <button
          onClick={() => onGerarPix(payment)}
          disabled={gerandoPix === payment.id}
          className="px-3 py-1 bg-emerald-600 text-white text-xs rounded hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {gerandoPix === payment.id ? 'Gerando...' : '🔲 Gerar PIX'}
        </button>
      )}
      
      <button
        onClick={() => onUpdateStatus(lojaSlug)}
        disabled={updatingThis || payment.is_paid}
        className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Consultar status no Mercado Pago e atualizar (ex.: boleto pago via PIX)"
      >
        {updatingThis ? 'Atualizando...' : '🔄 Atualizar Status'}
      </button>
      
      <button
        onClick={() => onNovaCobranca(assinatura)}
        disabled={gerandoCobrancaThis}
        className="px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 disabled:opacity-50 transition-colors"
      >
        {gerandoCobrancaThis ? 'Gerando...' : '➕ Nova Cobrança'}
      </button>
      
      <button
        onClick={() => onExcluir(payment)}
        disabled={payment.is_paid || excluindoPagamento}
        className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title={payment.is_paid ? 'Não é possível excluir cobrança paga' : 'Excluir cobrança'}
      >
        {excluindoPagamento ? 'Excluindo...' : '🗑️ Excluir'}
      </button>
    </div>
  );
}
