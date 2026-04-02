/**
 * Hook para gerenciar lista de assinaturas (Asaas + Mercado Pago)
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import { useState, useCallback, useMemo } from 'react';
import apiClient from '@/lib/api-client';

export interface Pagamento {
  id: number | null;
  asaas_id: string;
  customer_name: string;
  customer_email: string;
  value: string;
  status: string;
  status_display: string;
  due_date: string;
  payment_date: string | null;
  bank_slip_url: string;
  pix_copy_paste: string;
  pix_qr_code?: string | null;
  is_paid: boolean;
  is_overdue: boolean;
  is_pending: boolean;
  provedor?: 'asaas' | 'mercadopago';
}

export interface Assinatura {
  id: number | string;
  loja_slug: string;
  loja_nome: string;
  plano_nome: string;
  plano_valor: string;
  ativa: boolean;
  data_vencimento: string;
  current_payment_data: Pagamento | null;
  total_payments: number;
  financeiro_id?: number;  // ✅ NOVO v1489: ID do FinanceiroLoja para endpoints de NF
  subscription_status?: string;
  subscription_status_display?: string;
}

export function useAssinaturas() {
  const [assinaturas, setAssinaturas] = useState<Assinatura[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroProvedor, setFiltroProvedor] = useState<'todos' | 'asaas' | 'mercadopago'>('todos');

  const loadAssinaturas = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/superadmin/financeiro-unificado/');
      const data = res.data;
      setAssinaturas(Array.isArray(data.assinaturas) ? data.assinaturas : []);
    } catch (error) {
      console.error('Erro ao carregar assinaturas:', error);
      setAssinaturas([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const assinaturasFiltradas = useMemo(() => {
    if (filtroProvedor === 'todos') return assinaturas;
    
    return assinaturas.filter(assinatura => {
      const isAsaas = typeof assinatura.id === 'number';
      const isMercadoPago = assinatura.current_payment_data?.provedor === 'mercadopago';
      
      if (filtroProvedor === 'asaas') return isAsaas;
      if (filtroProvedor === 'mercadopago') return isMercadoPago;
      return true;
    });
  }, [assinaturas, filtroProvedor]);

  return {
    assinaturas,
    assinaturasFiltradas,
    filtroProvedor,
    setFiltroProvedor,
    loading,
    reload: loadAssinaturas
  };
}
