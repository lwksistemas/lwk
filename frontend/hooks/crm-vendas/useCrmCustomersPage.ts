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

export function useCrmCustomersPage() {
  const toast = useToast();
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const basePath = `/loja/${slug}/crm-vendas/customers`;
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

  const [contaParaExcluir, setContaParaExcluir] = useState<CrmConta | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const irParaVerConta = useCallback(
    (id: number) => {
      router.push(`${basePath}/${id}`);
    },
    [basePath, router],
  );

  useEffect(() => {
    if (!verParam) return;
    const id = parseInt(verParam, 10);
    if (isNaN(id)) return;
    router.replace(`${basePath}/${id}`, { scroll: false });
  }, [basePath, router, verParam]);

  const handleDelete = async () => {
    if (!contaParaExcluir) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/contas/${contaParaExcluir.id}/`);
      await loadContas(true);
      setContaParaExcluir(null);
      toast.success('Conta excluída.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
    } finally {
      setSubmitting(false);
    }
  };

  const irParaNovaConta = () => {
    router.push(`${basePath}/nova-conta`);
  };

  const irParaEditarConta = (id: number) => {
    router.push(`${basePath}/${id}/editar`);
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
    contaParaExcluir,
    setContaParaExcluir,
    submitting,
    handleDelete,
    irParaNovaConta,
    irParaEditarConta,
    irParaVerConta,
    exportContasCsv,
  };
}
