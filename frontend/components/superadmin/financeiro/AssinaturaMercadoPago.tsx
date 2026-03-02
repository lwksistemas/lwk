/**
 * Componente de ações para assinaturas Mercado Pago
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import type { Pagamento } from '@/hooks/useAssinaturas';

interface AssinaturaMercadoPagoProps {
  lojaSlug: string;
  payment: Pagamento;
  onDownloadBoleto: (payment: Pagamento) => void;
  onCopyPix: (pixCode: string) => void;
  onGerarPix: (payment: Pagamento) => void;
  onUpdateStatus: (lojaSlug: string) => void;
  gerandoPix: number | null;
  atualizandoMP: string | null;
}

export function AssinaturaMercadoPago({
  lojaSlug,
  payment,
  onDownloadBoleto,
  onCopyPix,
  onGerarPix,
  onUpdateStatus,
  gerandoPix,
  atualizandoMP
}: AssinaturaMercadoPagoProps) {
  const updatingThis = atualizandoMP === lojaSlug;
  
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
    </div>
  );
}
