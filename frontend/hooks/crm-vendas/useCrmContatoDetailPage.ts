'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import type { CrmContato } from '@/hooks/crm-vendas/useCrmContatosPage';

export function useCrmContatoDetailPage(slug: string, contatoId: number) {
  const toast = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  const listPath = `/loja/${slug}/crm-vendas/contatos`;
  const editPath = `${listPath}/${contatoId}/editar`;

  const [contato, setContato] = useState<CrmContato | null>(null);
  const [loading, setLoading] = useState(true);
  const [excluindo, setExcluindo] = useState(false);
  const [confirmarExclusao, setConfirmarExclusao] = useState(false);

  const carregar = useCallback(() => {
    if (Number.isNaN(contatoId)) return;
    setLoading(true);
    return apiClient
      .get<CrmContato>(`/crm-vendas/contatos/${contatoId}/`)
      .then((res) => setContato(res.data))
      .catch(() => router.replace(listPath))
      .finally(() => setLoading(false));
  }, [contatoId, listPath, router]);

  useEffect(() => {
    if (Number.isNaN(contatoId)) {
      router.replace(listPath);
      return;
    }
    carregar();
  }, [carregar, contatoId, listPath, router]);

  useEffect(() => {
    if (searchParams.get('excluir') === '1') {
      setConfirmarExclusao(true);
      router.replace(`${listPath}/${contatoId}`, { scroll: false });
    }
  }, [contatoId, listPath, router, searchParams]);

  const excluir = async () => {
    if (!contato) return;
    setExcluindo(true);
    try {
      await apiClient.delete(`/crm-vendas/contatos/${contato.id}/`);
      toast.success('Contato excluído.');
      router.push(listPath);
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir contato.'));
    } finally {
      setExcluindo(false);
      setConfirmarExclusao(false);
    }
  };

  return {
    contato,
    loading,
    excluindo,
    confirmarExclusao,
    setConfirmarExclusao,
    excluir,
    voltar: () => router.push(listPath),
    irParaEditar: () => router.push(editPath),
    irParaConta: () => {
      if (contato?.conta) router.push(`/loja/${slug}/crm-vendas/customers/${contato.conta}`);
    },
  };
}
