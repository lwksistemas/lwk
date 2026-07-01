'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { applyTelefoneInternacionalPayload, formatTelefone } from '@/lib/format-br';
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

export type CrmContatoModalType = 'create' | 'edit' | 'view' | 'delete' | null;

const EMPTY_FORM = { nome: '', email: '', telefone: '', cargo: '', conta: '', observacoes: '' };

export function useCrmContatosPage() {
  const toast = useToast();
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
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

  const [modalType, setModalType] = useState<CrmContatoModalType>(null);
  const [selectedContato, setSelectedContato] = useState<CrmContato | null>(null);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [contaNomeForm, setContaNomeForm] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const contaIdNaUrl = searchParams.get('conta_id');
  const verParam = searchParams.get('ver');

  const openModal = useCallback((type: CrmContatoModalType, contato?: CrmContato) => {
    setModalType(type);
    setSelectedContato(contato || null);
    if (type === 'edit' && contato) {
      setFormData({
        nome: contato.nome || '',
        email: contato.email || '',
        telefone: formatTelefone(contato.telefone || ''),
        cargo: contato.cargo || '',
        conta: String(contato.conta) || '',
        observacoes: contato.observacoes || '',
      });
      setContaNomeForm(contato.conta_nome || '');
    } else if (type === 'create') {
      setFormData(EMPTY_FORM);
      setContaNomeForm('');
    }
  }, []);

  const closeModal = useCallback(() => {
    setModalType(null);
    setSelectedContato(null);
    setFormData(EMPTY_FORM);
    setContaNomeForm('');
  }, []);

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
    if (cid) setFormData((f) => ({ ...f, conta: cid }));
    openModal('create');
    router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
  }, [searchParams, router, slug, openModal]);

  useEffect(() => {
    if (!verParam) return;
    const id = parseInt(verParam, 10);
    if (isNaN(id)) return;
    const found = contatos.find((c) => c.id === id);
    if (found) {
      openModal('view', found);
      router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
    } else if (!loading) {
      apiClient
        .get<CrmContato>(`/crm-vendas/contatos/${id}/`)
        .then((res) => {
          openModal('view', res.data);
          router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
        })
        .catch(() => {});
    }
  }, [verParam, contatos, loading, slug, router, openModal]);

  const limparFiltroConta = () => {
    setContaFiltro(null);
    router.replace(`/loja/${slug}/crm-vendas/contatos`, { scroll: false });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.nome.trim()) {
      toast.warning('Nome é obrigatório');
      return;
    }
    if (!formData.conta) {
      toast.warning('Conta é obrigatória');
      return;
    }
    try {
      setSubmitting(true);
      const payload = applyTelefoneInternacionalPayload({ ...formData, conta: parseInt(formData.conta, 10) });
      if (modalType === 'create') {
        const res = await apiClient.post('/crm-vendas/contatos/', payload);
        const novoContato = res.data;
        try {
          const contaRes = await apiClient.get(`/crm-vendas/contas/${payload.conta}/`);
          const conta = contaRes.data;
          const leadPayload = {
            nome: novoContato.nome,
            empresa: conta.nome,
            email: novoContato.email || conta.email || '',
            telefone: novoContato.telefone || conta.telefone || '',
            origem: 'site',
            status: 'novo',
            conta: conta.id,
            contato: novoContato.id,
            cpf_cnpj: conta.cnpj || '',
            cep: conta.cep || '',
            logradouro: conta.logradouro || '',
            numero: conta.numero || '',
            complemento: conta.complemento || '',
            bairro: conta.bairro || '',
            cidade: conta.cidade || '',
            uf: conta.uf || '',
          };
          await apiClient.post('/crm-vendas/leads/', leadPayload);
          toast.success('Contato e Lead criados com sucesso!');
        } catch (leadErr: unknown) {
          const detail = (leadErr as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
            ?.detail;
          toast.warning(`Contato criado, mas o Lead automático falhou: ${detail || (leadErr as Error).message}`);
        }
      } else if (modalType === 'edit' && selectedContato) {
        await apiClient.put(`/crm-vendas/contatos/${selectedContato.id}/`, payload);
        toast.success('Contato atualizado.');
      }
      await reloadContatos(true);
      closeModal();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || 'Erro ao salvar contato.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedContato) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/contatos/${selectedContato.id}/`);
      await reloadContatos(true);
      closeModal();
      toast.success('Contato excluído.');
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || 'Erro ao excluir contato.');
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
    modalType,
    selectedContato,
    formData,
    setFormData,
    contaNomeForm,
    submitting,
    openModal,
    closeModal,
    limparFiltroConta,
    handleSubmit,
    handleDelete,
  };
}
