'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { buildCrmLeadPayload, getCrmApiErrorDetail } from '@/lib/crm-utils';
import { STATUS_LEAD_OPCOES } from '@/constants/crm';
import { formatTelefone } from '@/lib/format-br';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { useToast } from '@/components/ui/Toast';
import type { Lead } from '@/components/crm-vendas/LeadsTable';
import { EMPTY_FORM_LEAD, type FormDataLead } from '@/components/crm-vendas/modals/ModalLeadForm';
import { LEADS_PAGE_SIZE, loadLeadsPage, formatarDataLead, exportLeadsCsv } from '@/lib/crm-leads';

export function useCrmLeadsPage() {
  const toast = useToast();
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = (params?.slug as string) ?? '';
  const verParam = searchParams.get('ver');
  const { colunasLeadsVisiveis, origensAtivas } = useCRMConfig();

  const [leads, setLeads] = useState<Lead[]>([]);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leadVer, setLeadVer] = useState<Lead | null>(null);
  const [leadEditar, setLeadEditar] = useState<Lead | null>(null);
  const [leadExcluir, setLeadExcluir] = useState<Lead | null>(null);
  const [leadMudarStatus, setLeadMudarStatus] = useState<Lead | null>(null);
  const [novoStatus, setNovoStatus] = useState('');
  const [salvandoEdicao, setSalvandoEdicao] = useState(false);
  const [salvandoStatus, setSalvandoStatus] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [form, setForm] = useState<FormDataLead>(EMPTY_FORM_LEAD);

  useEffect(() => {
    loadLeadsPage(page, setLeads, setTotalCount, setTotalPages, setError, setLoading);
  }, [page, slug]);

  const reloadLeads = () => {
    loadLeadsPage(page, setLeads, setTotalCount, setTotalPages, setError, setLoading);
  };

  useEffect(() => {
    if (searchParams.get('novo') === '1') {
      router.replace(`/loja/${slug}/crm-vendas/leads/novo`, { scroll: false });
    }
  }, [searchParams, router, slug]);

  useEffect(() => {
    if (!verParam) return;
    const id = parseInt(verParam, 10);
    if (isNaN(id)) return;
    const found = leads.find((l) => l.id === id);
    if (found) {
      setLeadVer(found);
      router.replace(`/loja/${slug}/crm-vendas/leads`, { scroll: false });
    } else if (!loading) {
      apiClient
        .get<Lead>(`/crm-vendas/leads/${id}/`)
        .then((res) => {
          setLeadVer(res.data);
          router.replace(`/loja/${slug}/crm-vendas/leads`, { scroll: false });
        })
        .catch(() => {});
    }
  }, [verParam, leads, loading, router, slug]);

  const origemLabel = (value: string) => origensAtivas().find((o) => o.key === value)?.label ?? value;
  const statusLabel = (value: string) => STATUS_LEAD_OPCOES.find((o) => o.value === value)?.label ?? value;

  const handleEditarLead = (lead: Lead) => {
    setLeadEditar(lead);
    setForm({
      nome: lead.nome,
      empresa: lead.empresa || '',
      cpf_cnpj: lead.cpf_cnpj || '',
      email: lead.email || '',
      telefone: formatTelefone(lead.telefone || ''),
      origem: lead.origem,
      status: lead.status,
      cep: lead.cep || '',
      logradouro: lead.logradouro || '',
      numero: lead.numero || '',
      complemento: lead.complemento || '',
      bairro: lead.bairro || '',
      cidade: lead.cidade || '',
      uf: lead.uf || '',
      observacoes: lead.observacoes || '',
    });
    setFormErro(null);
  };

  const handleSalvarEdicao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadEditar || salvandoEdicao) return;
    setFormErro(null);
    if (!form.nome.trim()) {
      setFormErro('Informe o nome.');
      return;
    }
    setSalvandoEdicao(true);
    try {
      await apiClient.patch(`/crm-vendas/leads/${leadEditar.id}/`, buildCrmLeadPayload(form));
      setLeadEditar(null);
      reloadLeads();
      toast.success('Lead atualizado.');
    } catch (err) {
      setFormErro(getCrmApiErrorDetail(err, 'Erro ao salvar lead.'));
    } finally {
      setSalvandoEdicao(false);
    }
  };

  const confirmarExcluir = () => {
    if (!leadExcluir) return;
    setExcluindo(true);
    apiClient
      .delete(`/crm-vendas/leads/${leadExcluir.id}/`)
      .then(() => {
        setLeadExcluir(null);
        reloadLeads();
        toast.success('Lead excluído.');
      })
      .catch((err) => {
        toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir lead.'));
      })
      .finally(() => setExcluindo(false));
  };

  const handleMudarStatus = (lead: Lead) => {
    setLeadMudarStatus(lead);
    setNovoStatus(lead.status);
  };

  const salvarNovoStatus = async () => {
    if (!leadMudarStatus || novoStatus === leadMudarStatus.status) {
      setLeadMudarStatus(null);
      return;
    }
    if (salvandoStatus) return;
    setFormErro(null);
    setSalvandoStatus(true);
    try {
      await apiClient.patch(`/crm-vendas/leads/${leadMudarStatus.id}/`, { status: novoStatus });
      setLeadMudarStatus(null);
      reloadLeads();
      toast.success('Status atualizado.');
    } catch (err) {
      setFormErro(getCrmApiErrorDetail(err, 'Erro ao atualizar status.'));
    } finally {
      setSalvandoStatus(false);
    }
  };

  return {
    slug,
    leads,
    page,
    setPage,
    totalCount,
    totalPages,
    loading,
    error,
    leadVer,
    setLeadVer,
    leadEditar,
    setLeadEditar,
    leadExcluir,
    setLeadExcluir,
    leadMudarStatus,
    setLeadMudarStatus,
    novoStatus,
    setNovoStatus,
    salvandoEdicao,
    salvandoStatus,
    excluindo,
    formErro,
    setFormErro,
    form,
    setForm,
    colunasLeadsVisiveis,
    origensAtivas,
    origemLabel,
    statusLabel,
    formatarDataLead,
    handleEditarLead,
    handleSalvarEdicao,
    confirmarExcluir,
    handleMudarStatus,
    salvarNovoStatus,
    exportLeadsCsv,
    leadsPageSize: LEADS_PAGE_SIZE,
  };
}
