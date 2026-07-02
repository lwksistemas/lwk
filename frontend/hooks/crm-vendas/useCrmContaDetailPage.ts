'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import type { CrmConta } from '@/hooks/crm-vendas/useCrmCustomersPage';

export function useCrmContaDetailPage(slug: string, contaId: number) {
  const toast = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  const listPath = `/loja/${slug}/crm-vendas/customers`;
  const editPath = `${listPath}/${contaId}/editar`;

  const [conta, setConta] = useState<CrmConta | null>(null);
  const [loading, setLoading] = useState(true);
  const [excluindo, setExcluindo] = useState(false);
  const [confirmarExclusao, setConfirmarExclusao] = useState(false);

  const carregar = useCallback(() => {
    if (Number.isNaN(contaId)) return;
    setLoading(true);
    return apiClient
      .get<CrmConta>(`/crm-vendas/contas/${contaId}/`)
      .then((res) => setConta(res.data))
      .catch(() => router.replace(listPath))
      .finally(() => setLoading(false));
  }, [contaId, listPath, router]);

  useEffect(() => {
    if (Number.isNaN(contaId)) {
      router.replace(listPath);
      return;
    }
    carregar();
  }, [carregar, contaId, listPath, router]);

  useEffect(() => {
    if (searchParams.get('excluir') === '1') {
      setConfirmarExclusao(true);
      router.replace(`${listPath}/${contaId}`, { scroll: false });
    }
  }, [contaId, listPath, router, searchParams]);

  const excluir = async () => {
    if (!conta) return;
    setExcluindo(true);
    try {
      await apiClient.delete(`/crm-vendas/contas/${conta.id}/`);
      toast.success('Conta excluída.');
      router.push(listPath);
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir conta.'));
    } finally {
      setExcluindo(false);
      setConfirmarExclusao(false);
    }
  };

  return {
    conta,
    loading,
    excluindo,
    confirmarExclusao,
    setConfirmarExclusao,
    listPath,
    editPath,
    excluir,
    voltar: () => router.push(listPath),
    irParaEditar: () => router.push(editPath),
  };
}
