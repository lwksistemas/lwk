'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { useToast } from '@/components/ui/Toast';
import type { CrmFuncionario } from '@/lib/crm-funcionarios';

export function useCrmFuncionariosPage(slug: string) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const base = `/loja/${slug}/crm-vendas/configuracoes/funcionarios`;

  const {
    items: vendedores,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    reload: carregar,
  } = usePaginatedList<CrmFuncionario>('/crm-vendas/vendedores/', {
    errorFallback: 'Erro ao carregar funcionários.',
  });

  const [reenviando, setReenviando] = useState<number | string | null>(null);
  const [excluindo, setExcluindo] = useState<number | string | null>(null);
  const [confirmarExcluir, setConfirmarExcluir] = useState<CrmFuncionario | null>(null);
  const [formErro, setFormErro] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get('saved') === '1') {
      toast.success('Funcionário salvo com sucesso.');
      router.replace(base);
    }
  }, [searchParams, toast, router, base]);

  const abrirNovo = () => router.push(`${base}/novo`);

  const abrirEditar = (v: CrmFuncionario) => {
    if (v.id === 'admin' || v.is_admin) return;
    router.push(`${base}/${v.id}/editar`);
  };

  const handleExcluir = async (v: CrmFuncionario) => {
    if (!confirmarExcluir || confirmarExcluir.id !== v.id) return;
    if (v.id === 'admin' || v.is_admin) return;
    setExcluindo(v.id);
    setFormErro(null);
    try {
      await apiClient.delete(`/crm-vendas/vendedores/${v.id}/`);
      setConfirmarExcluir(null);
      toast.success('Funcionário excluído.');
      carregar(true);
    } catch (err: unknown) {
      setFormErro(getCrmApiErrorDetail(err, 'Erro ao excluir. Tente novamente.'));
    } finally {
      setExcluindo(null);
    }
  };

  const handleReenviarSenha = async (v: CrmFuncionario) => {
    if (!v.email) return;
    setReenviando(v.id);
    setFormErro(null);
    try {
      const isAdmin = v.id === 'admin' || v.is_admin;
      const url = isAdmin
        ? '/crm-vendas/vendedores/reenviar_senha_administrador/'
        : `/crm-vendas/vendedores/${v.id}/reenviar_senha/`;
      await apiClient.post(url);
      toast.success('Senha provisória reenviada por email.');
      carregar(true);
    } catch (err: unknown) {
      setFormErro(getCrmApiErrorDetail(err, 'Erro ao reenviar senha.'));
    } finally {
      setReenviando(null);
    }
  };

  return {
    base,
    vendedores,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    formErro,
    reenviando,
    excluindo,
    confirmarExcluir,
    setConfirmarExcluir,
    abrirNovo,
    abrirEditar,
    handleExcluir,
    handleReenviarSenha,
  };
}
