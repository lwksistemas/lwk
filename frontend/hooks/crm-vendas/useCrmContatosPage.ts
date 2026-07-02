'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { useToast } from '@/components/ui/Toast';

export interface CrmContato {
  id: number;
  nome: string;
  email?: string;
  telefone?: string;
  cargo?: string;
  conta: number;
  conta_nome?: string;
  observacoes?: string;
  created_at: string;
}

export function useCrmContatosPage() {
  const toast = useToast();
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const basePath = `/loja/${slug}/crm-vendas/contatos`;
  const { colunasContatosVisiveis } = useCRMConfig();
  const colunasVisiveis = colunasContatosVisiveis();

  const [contaFiltro, setContaFiltro] = useState<number | null>(null);
  const [contaFiltroNome, setContaFiltroNome] = useState<string | null>(null);

  const {
    items: contatos,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    reload: reloadContatos,
  } = usePaginatedList<CrmContato>('/crm-vendas/contatos/', {
    params: { conta_id: contaFiltro ?? undefined },
    errorFallback: 'Erro ao carregar contatos.',
  });

  const [contatoParaExcluir, setContatoParaExcluir] = useState<CrmContato | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const contaIdNaUrl = searchParams.get('conta_id');
  const verParam = searchParams.get('ver');

  const irParaNovoContato = useCallback(() => {
    const qs = contaFiltro ? `?conta_id=${contaFiltro}${contaFiltroNome ? `&conta_nome=${encodeURIComponent(contaFiltroNome)}` : ''}` : '';
    router.push(`${basePath}/novo${qs}`);
  }, [basePath, contaFiltro, contaFiltroNome, router]);

  const irParaEditarContato = useCallback(
    (id: number) => {
      router.push(`${basePath}/${id}/editar`);
    },
    [basePath, router],
  );

  const irParaVerContato = useCallback(
    (id: number) => {
      router.push(`${basePath}/${id}`);
    },
    [basePath, router],
  );

  useEffect(() => {
    if (contaIdNaUrl) {
      const id = parseInt(contaIdNaUrl, 10);
      if (!isNaN(id)) {
        setContaFiltro(id);
        return;
      }
    }
    setContaFiltro(null);
  }, [contaIdNaUrl]);

  useEffect(() => {
    if (!contaFiltro) {
      setContaFiltroNome(null);
      return;
    }
    let cancelled = false;
    apiClient
      .get<{ nome: string }>(`/crm-vendas/contas/${contaFiltro}/`)
      .then((res) => {
        if (!cancelled) setContaFiltroNome(res.data.nome);
      })
      .catch(() => {
        if (!cancelled) setContaFiltroNome(null);
      });
    return () => {
      cancelled = true;
    };
  }, [contaFiltro]);

  useEffect(() => {
    if (searchParams.get('criar') !== '1') return;
    const cid = searchParams.get('conta_id');
    const cname = searchParams.get('conta_nome');
    const qs = cid
      ? `?conta_id=${cid}${cname ? `&conta_nome=${encodeURIComponent(cname)}` : ''}`
      : '';
    router.replace(`${basePath}/novo${qs}`, { scroll: false });
  }, [basePath, router, searchParams]);

  useEffect(() => {
    if (!verParam) return;
    const id = parseInt(verParam, 10);
    if (isNaN(id)) return;
    router.replace(`${basePath}/${id}`, { scroll: false });
  }, [basePath, router, verParam]);

  const limparFiltroConta = () => {
    setContaFiltro(null);
    router.replace(basePath, { scroll: false });
  };

  const handleDelete = async () => {
    if (!contatoParaExcluir) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/contatos/${contatoParaExcluir.id}/`);
      await reloadContatos(true);
      setContatoParaExcluir(null);
      toast.success('Contato excluído.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir contato.'));
    } finally {
      setSubmitting(false);
    }
  };

  return {
    slug,
    contatos,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    colunasVisiveis,
    contaFiltro,
    contaFiltroNome,
    contatoParaExcluir,
    setContatoParaExcluir,
    submitting,
    irParaNovoContato,
    irParaEditarContato,
    irParaVerContato,
    limparFiltroConta,
    handleDelete,
  };
}
