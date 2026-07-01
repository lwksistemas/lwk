'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { useToast } from '@/components/ui/Toast';
import { exportContasCsv } from '@/lib/crm-contas';

export interface CrmConta {
  id: number;
  nome: string;
  razao_social?: string;
  cnpj?: string;
  inscricao_estadual?: string;
  tipo: string;
  segmento: string;
  telefone?: string;
  email?: string;
  site?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  observacoes?: string;
  created_at: string;
}

export type CrmContaModalType = 'view' | 'delete' | null;

export function useCrmCustomersPage() {
  const toast = useToast();
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const verParam = searchParams.get('ver');
  const { colunasContasVisiveis } = useCRMConfig();

  const {
    items: contas,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    reload: loadContas,
  } = usePaginatedList<CrmConta>('/crm-vendas/contas/', {
    errorFallback: 'Erro ao carregar clientes.',
  });

  const [modalType, setModalType] = useState<CrmContaModalType>(null);
  const [selectedConta, setSelectedConta] = useState<CrmConta | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const openModal = useCallback((type: CrmContaModalType, conta?: CrmConta) => {
    setModalType(type);
    setSelectedConta(conta || null);
  }, []);

  const closeModal = useCallback(() => {
    setModalType(null);
    setSelectedConta(null);
  }, []);

  useEffect(() => {
    if (!verParam) return;
    const id = parseInt(verParam, 10);
    if (isNaN(id)) return;
    const found = contas.find((c) => c.id === id);
    if (found) {
      openModal('view', found);
      router.replace(`/loja/${slug}/crm-vendas/customers`, { scroll: false });
    } else if (!loading) {
      apiClient
        .get<CrmConta>(`/crm-vendas/contas/${id}/`)
        .then((res) => {
          openModal('view', res.data);
          router.replace(`/loja/${slug}/crm-vendas/customers`, { scroll: false });
        })
        .catch(() => {});
    }
  }, [verParam, contas, loading, slug, router, openModal]);

  const handleDelete = async () => {
    if (!selectedConta) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/contas/${selectedConta.id}/`);
      await loadContas(true);
      closeModal();
      toast.success('Conta excluída.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
    } finally {
      setSubmitting(false);
    }
  };

  const irParaNovaConta = () => {
    router.push(`/loja/${slug}/crm-vendas/customers/nova-conta`);
  };

  const irParaEditarConta = (id: number) => {
    router.push(`/loja/${slug}/crm-vendas/customers/${id}/editar`);
  };

  return {
    slug,
    contas,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    colunasVisiveis: colunasContasVisiveis(),
    modalType,
    selectedConta,
    submitting,
    openModal,
    closeModal,
    handleDelete,
    irParaNovaConta,
    irParaEditarConta,
    exportContasCsv,
  };
}
