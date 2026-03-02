/**
 * Hook para ações específicas do Mercado Pago
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import type { Pagamento } from './useAssinaturas';

export function useMercadoPagoActions() {
  const [gerandoPix, setGerandoPix] = useState<number | null>(null);
  const [atualizandoMP, setAtualizandoMP] = useState<string | null>(null);

  const downloadBoleto = useCallback(async (payment: Pagamento) => {
    if (payment.id == null || payment.id === undefined) {
      alert('Link do boleto não disponível para este pagamento.');
      return;
    }
    
    try {
      const res = await apiClient.get(`/superadmin/loja-pagamentos/${payment.id}/baixar_boleto_pdf/`);
      const data = res.data as { boleto_url?: string; provedor?: string };
      
      if (data?.boleto_url) {
        window.open(data.boleto_url, '_blank', 'noopener,noreferrer');
      } else {
        alert('Link do boleto não disponível. Verifique se o pagamento existe na conta (produção/sandbox).');
      }
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error;
      alert(msg || 'Não foi possível obter o link do boleto.');
    }
  }, []);

  const gerarPix = useCallback(async (payment: Pagamento, onSuccess?: () => void) => {
    if (payment.id == null) return;
    
    try {
      setGerandoPix(payment.id);
      const res = await apiClient.post(`/superadmin/loja-pagamentos/${payment.id}/gerar_pix/`);
      const data = res.data as { pix_copy_paste?: string; pix_qr_code?: string };
      
      if (data?.pix_copy_paste) {
        navigator.clipboard.writeText(data.pix_copy_paste);
        if (onSuccess) onSuccess();
        alert('PIX gerado! O código foi copiado para a área de transferência.');
      }
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error;
      alert(msg || 'Não foi possível gerar o PIX.');
    } finally {
      setGerandoPix(null);
    }
  }, []);

  const updateStatus = useCallback(async (lojaSlug: string, onSuccess?: () => void) => {
    setAtualizandoMP(lojaSlug);
    try {
      const res = await apiClient.post('/superadmin/sync-mercadopago/', { loja_slug: lojaSlug });
      if (onSuccess) onSuccess();
      
      const processed = res.data?.processed ?? 0;
      if (processed > 0) {
        alert(`Status atualizado: ${processed} pagamento(s) sincronizado(s) com o Mercado Pago.`);
      } else {
        alert(res.data?.message || 'Nenhuma alteração. O pagamento pode ainda estar pendente no Mercado Pago.');
      }
    } catch (error: unknown) {
      console.error('Erro ao sincronizar Mercado Pago:', error);
      const msg = (error as { response?: { data?: { error?: string } } })?.response?.data?.error;
      alert(msg || 'Erro ao atualizar status. Tente novamente.');
    } finally {
      setAtualizandoMP(null);
    }
  }, []);

  const copyPixCode = useCallback((pixCode: string) => {
    navigator.clipboard.writeText(pixCode);
    alert('Código PIX copiado!');
  }, []);

  return {
    downloadBoleto,
    gerarPix,
    updateStatus,
    copyPixCode,
    gerandoPix,
    atualizandoMP
  };
}
