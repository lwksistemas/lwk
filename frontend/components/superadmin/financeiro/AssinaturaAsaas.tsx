/**
 * Componente de ações para assinaturas Asaas
 * ✅ REFATORADO v780: Extraído da página de financeiro
 * ✅ NOVO v1484: Botões de Nota Fiscal (Baixar, Reenviar, Cancelar)
 */
import { useState } from 'react';
import type { Pagamento, Assinatura } from '@/hooks/useAssinaturas';
import { apiClient } from '@/lib/api-client';

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
  const [baixandoNF, setBaixandoNF] = useState(false);
  const [reenviandoNF, setReenviandoNF] = useState(false);
  const [cancelandoNF, setCancelandoNF] = useState(false);

  const getFinanceiroId = () => assinatura.financeiro_id;

  const handleBaixarNotaFiscal = async () => {
    try {
      setBaixandoNF(true);
      const financeiro_id = getFinanceiroId();
      if (!financeiro_id) {
        alert('ID do financeiro não encontrado para esta loja');
        return;
      }
      const { data } = await apiClient.get(`/superadmin/financeiro/${financeiro_id}/baixar_nota_fiscal/`);
      if (data.success && data.pdf_url) {
        window.open(data.pdf_url, '_blank');
      } else {
        alert(data.error || 'Nota fiscal não encontrada');
      }
    } catch (error: any) {
      alert(error.response?.data?.error || 'Erro ao baixar nota fiscal');
    } finally {
      setBaixandoNF(false);
    }
  };

  const handleReenviarNotaFiscal = async () => {
    try {
      setReenviandoNF(true);
      const financeiro_id = getFinanceiroId();
      if (!financeiro_id) {
        alert('ID do financeiro não encontrado para esta loja');
        return;
      }
      const { data } = await apiClient.post(`/superadmin/financeiro/${financeiro_id}/reenviar_nota_fiscal/`);
      if (data.success) {
        alert(data.message || 'Nota fiscal reenviada com sucesso!');
      } else {
        alert(data.error || 'Erro ao reenviar nota fiscal');
      }
    } catch (error: any) {
      alert(error.response?.data?.error || 'Erro ao reenviar nota fiscal');
    } finally {
      setReenviandoNF(false);
    }
  };

  const handleCancelarNotaFiscal = async () => {
    if (!confirm('Tem certeza que deseja cancelar a nota fiscal? Esta ação não pode ser desfeita.')) {
      return;
    }
    try {
      setCancelandoNF(true);
      const financeiro_id = getFinanceiroId();
      if (!financeiro_id) {
        alert('ID do financeiro não encontrado para esta loja');
        return;
      }
      const { data } = await apiClient.post(`/superadmin/financeiro/${financeiro_id}/cancelar_nota_fiscal/`);
      if (data.success) {
        alert(data.message || 'Nota fiscal cancelada com sucesso!');
      } else {
        alert(data.error || 'Erro ao cancelar nota fiscal');
      }
    } catch (error: any) {
      alert(error.response?.data?.error || 'Erro ao cancelar nota fiscal');
    } finally {
      setCancelandoNF(false);
    }
  };

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

      {/* Botões de Nota Fiscal */}
      <button
        onClick={handleBaixarNotaFiscal}
        disabled={baixandoNF || !payment.is_paid}
        className="px-3 py-1 bg-indigo-600 text-white text-xs rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title={!payment.is_paid ? 'NF disponível apenas para pagamentos confirmados' : 'Baixar PDF da nota fiscal'}
      >
        {baixandoNF ? '⏳ Baixando...' : '🧾 Baixar NF'}
      </button>

      <button
        onClick={handleReenviarNotaFiscal}
        disabled={reenviandoNF || !payment.is_paid}
        className="px-3 py-1 bg-teal-600 text-white text-xs rounded hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title={!payment.is_paid ? 'NF disponível apenas para pagamentos confirmados' : 'Reenviar NF por email'}
      >
        {reenviandoNF ? '⏳ Enviando...' : '📧 Reenviar NF'}
      </button>

      <button
        onClick={handleCancelarNotaFiscal}
        disabled={cancelandoNF || !payment.is_paid}
        className="px-3 py-1 bg-rose-600 text-white text-xs rounded hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title={!payment.is_paid ? 'NF disponível apenas para pagamentos confirmados' : 'Cancelar nota fiscal'}
      >
        {cancelandoNF ? '⏳ Cancelando...' : '❌ Cancelar NF'}
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
