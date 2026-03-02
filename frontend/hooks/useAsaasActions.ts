/**
 * Hook para ações específicas do Asaas
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import type { Pagamento } from './useAssinaturas';

export function useAsaasActions() {
  const [gerandoCobranca, setGerandoCobranca] = useState<number | null>(null);
  const [excluindoPagamento, setExcluindoPagamento] = useState(false);

  const downloadBoleto = useCallback((payment: Pagamento) => {
    if (payment.bank_slip_url) {
      window.open(payment.bank_slip_url, '_blank', 'noopener,noreferrer');
    } else {
      alert('Boleto não disponível');
    }
  }, []);

  const updateStatus = useCallback(async (paymentId: number, onSuccess?: () => void) => {
    try {
      await apiClient.post(`/asaas/payments/${paymentId}/update_status/`);
      if (onSuccess) onSuccess();
      alert('Status atualizado com sucesso!');
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
      alert('Erro ao atualizar status');
    }
  }, []);

  const createManualPayment = useCallback(async (
    assinaturaId: number,
    dueDate: string | undefined,
    onSuccess?: () => void
  ) => {
    setGerandoCobranca(assinaturaId);
    try {
      const endpoint = dueDate 
        ? `/asaas/subscriptions/${assinaturaId}/create_manual_payment/`
        : `/asaas/subscriptions/${assinaturaId}/generate_new_payment/`;
      
      const payload = dueDate ? { due_date: dueDate } : {};
      
      const response = await apiClient.post(endpoint, payload);
      if (response.data.success) {
        if (onSuccess) onSuccess();
        alert('Cobrança criada com sucesso!');
        return true;
      } else {
        alert(response.data.error || 'Erro ao criar cobrança');
        return false;
      }
    } catch (error: any) {
      console.error('Erro ao criar cobrança:', error);
      alert(`Erro: ${error.response?.data?.error || error.message || 'Erro ao criar cobrança'}`);
      return false;
    } finally {
      setGerandoCobranca(null);
    }
  }, []);

  const deletePayment = useCallback(async (paymentId: number, onSuccess?: () => void) => {
    setExcluindoPagamento(true);
    try {
      const response = await apiClient.delete(`/asaas/payments/${paymentId}/delete_payment/`);
      if (response.data.success) {
        if (onSuccess) onSuccess();
        alert('Cobrança excluída com sucesso!');
        return true;
      } else {
        alert(response.data.error || 'Erro ao excluir cobrança');
        return false;
      }
    } catch (error: any) {
      console.error('Erro ao excluir cobrança:', error);
      alert(`Erro: ${error.response?.data?.error || error.message || 'Erro ao excluir cobrança'}`);
      return false;
    } finally {
      setExcluindoPagamento(false);
    }
  }, []);

  const copyPixCode = useCallback((pixCode: string) => {
    navigator.clipboard.writeText(pixCode);
    alert('Código PIX copiado!');
  }, []);

  return {
    downloadBoleto,
    updateStatus,
    createManualPayment,
    deletePayment,
    copyPixCode,
    gerandoCobranca,
    excluindoPagamento
  };
}
