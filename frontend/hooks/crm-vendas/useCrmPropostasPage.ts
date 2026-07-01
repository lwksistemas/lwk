'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import {
  normalizeListResponse,
  getCrmApiErrorDetail,
  fetchCrmOportunidade,
} from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import { useCrmDocumentoActions } from '@/hooks/useCrmDocumentoActions';
import { reenviarAssinaturaAposEdicaoSeNecessario } from '@/lib/crm-reenviar-assinatura';
import { CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import type { FormDataProposta } from '@/components/crm-vendas/modals/ModalPropostaForm';
import type { CrmOportunidadeItem, CrmPropostaTemplate } from '@/lib/crm-proposta-form-types';

export interface CrmProposta {
  id: number;
  oportunidade: number;
  oportunidade_titulo: string;
  lead_nome: string;
  lead_email?: string;
  lead_telefone?: string;
  vendedor_nome?: string;
  vendedor_email?: string;
  vendedor_telefone?: string;
  numero: string;
  titulo: string;
  conteudo: string;
  valor_total: string | null;
  desconto_tipo: 'percentual' | 'valor';
  desconto_valor: string;
  valor_com_desconto: string | null;
  status: string;
  status_assinatura?: string;
  motivo_cancelamento?: string;
  data_envio: string | null;
  data_resposta: string | null;
  created_at: string;
}

export type CrmPropostaModalType = 'edit' | 'view' | 'delete' | 'cancelar' | null;

export function propostaOcultaColunaAssinatura(p: CrmProposta): boolean {
  return (
    p.status === 'cancelada' ||
    p.status === 'pedido' ||
    p.status_assinatura === 'concluido'
  );
}

export function useCrmPropostasPage(slug: string) {
  const toast = useToast();
  const [filtroStatus, setFiltroStatus] = useState('');
  const statusParam = filtroStatus || undefined;

  const {
    items: propostas,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    reload: loadPropostas,
  } = usePaginatedList<CrmProposta>('/crm-vendas/propostas/', {
    params: { status: statusParam },
    errorFallback: 'Erro ao carregar propostas.',
  });

  const exibirColunaAssinatura = propostas.some((p) => !propostaOcultaColunaAssinatura(p));

  const [itensOportunidade, setItensOportunidade] = useState<CrmOportunidadeItem[]>([]);
  const [oportunidadeTituloInicial, setOportunidadeTituloInicial] = useState('');
  const [modalType, setModalType] = useState<CrmPropostaModalType>(null);
  const [selected, setSelected] = useState<CrmProposta | null>(null);
  const [formData, setFormData] = useState<FormDataProposta>({
    oportunidade_id: '',
    titulo: '',
    conteudo: '',
    valor_total: '',
    desconto_tipo: 'percentual',
    desconto_valor: '',
    status: 'rascunho',
    nome_vendedor_assinatura: '',
    nome_cliente_assinatura: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [salvandoPadrao, setSalvandoPadrao] = useState(false);
  const [propostaConteudoPadrao, setPropostaConteudoPadrao] = useState('');
  const [templates, setTemplates] = useState<CrmPropostaTemplate[]>([]);
  const [alterandoStatus, setAlterandoStatus] = useState<number | null>(null);
  const [menuAberto, setMenuAberto] = useState<number | null>(null);

  const { enviandoId, handleEnviarCliente, handleDownloadPdf, handleDownloadDocx } =
    useCrmDocumentoActions('propostas', loadPropostas);

  const { lojaInfo, loadLojaInfo } = useCrmLojaInfoPublica(slug);
  const { proposta: propostaWhatsappHabilitada } = useWhatsappEnvioFlags();
  const { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo } =
    useCrmLeadEVendedorForm(formData, setFormData);

  const loadItensOportunidade = useCallback(async (oportunidadeId: string) => {
    if (!oportunidadeId) {
      setItensOportunidade([]);
      return;
    }
    try {
      const res = await apiClient.get<CrmOportunidadeItem[] | { results: CrmOportunidadeItem[] }>(
        `/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidadeId}`,
      );
      setItensOportunidade(normalizeListResponse(res.data));
    } catch {
      setItensOportunidade([]);
    }
  }, []);

  const loadCrmConfig = useCallback(async () => {
    try {
      const res = await apiClient.get<{ proposta_conteudo_padrao?: string }>('/crm-vendas/config/');
      setPropostaConteudoPadrao(res.data?.proposta_conteudo_padrao ?? '');
    } catch {
      setPropostaConteudoPadrao('');
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const res = await apiClient.get<CrmPropostaTemplate[] | { results: CrmPropostaTemplate[] }>(
        '/crm-vendas/proposta-templates/',
      );
      setTemplates(normalizeListResponse(res.data));
    } catch {
      setTemplates([]);
    }
  }, []);

  const handleSalvarComoPadrao = useCallback(
    async (conteudo: string) => {
      try {
        setSalvandoPadrao(true);
        await apiClient.patch('/crm-vendas/config/', { proposta_conteudo_padrao: conteudo });
        setPropostaConteudoPadrao(conteudo);
        toast.success('Proposta padrão salva. O conteúdo será usado em novas propostas.');
      } catch (err: unknown) {
        toast.error(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
      } finally {
        setSalvandoPadrao(false);
      }
    },
    [toast],
  );

  const handleMarcarComoAssinado = async (propostaId: number) => {
    if (
      !confirm(
        'Marcar esta proposta como assinada manualmente?\n\nUse esta opção quando o cliente assinar de outra forma (manual, gov.br, etc).',
      )
    ) {
      return;
    }
    try {
      setAlterandoStatus(propostaId);
      await apiClient.patch(`/crm-vendas/propostas/${propostaId}/`, {
        status_assinatura: 'concluido',
        status: 'aceita',
      });
      await loadPropostas(true);
      toast.success('Proposta marcada como assinada com sucesso!');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao atualizar status.'));
    } finally {
      setAlterandoStatus(null);
    }
  };

  const handleConfirmarPedido = async (propostaId: number) => {
    if (
      !confirm(
        'Confirmar esta proposta como Pedido?\n\nIsso indica que o cliente confirmou o pedido formal e está pronto para gerar o contrato.',
      )
    ) {
      return;
    }
    try {
      setAlterandoStatus(propostaId);
      await apiClient.post(`/crm-vendas/propostas/${propostaId}/confirmar_pedido/`);
      await loadPropostas(true);
      toast.success('Proposta confirmada como pedido.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao confirmar pedido.'));
    } finally {
      setAlterandoStatus(null);
    }
  };

  const handleCancelarProposta = async (motivo: string) => {
    if (!selected) return;
    try {
      setAlterandoStatus(selected.id);
      await apiClient.post(`/crm-vendas/propostas/${selected.id}/cancelar/`, { motivo });
      await loadPropostas(true);
      closeModal();
      toast.success('Proposta cancelada.');
    } catch (err: unknown) {
      throw new Error(getCrmApiErrorDetail(err, 'Erro ao cancelar proposta.'));
    } finally {
      setAlterandoStatus(null);
    }
  };

  useEffect(() => {
    if (modalType === 'edit') {
      loadLojaInfo();
      loadCrmConfig();
      loadTemplates();
      loadVendedorInfo();
      if (formData.oportunidade_id) {
        loadItensOportunidade(formData.oportunidade_id);
        fetchCrmOportunidade(formData.oportunidade_id)
          .then((opp) => {
            if (opp.lead) loadLeadInfo(opp.lead);
          })
          .catch(() => setLeadInfo(null));
      }
    }
  }, [
    modalType,
    formData.oportunidade_id,
    loadLojaInfo,
    loadCrmConfig,
    loadTemplates,
    loadVendedorInfo,
    loadItensOportunidade,
    loadLeadInfo,
    setLeadInfo,
  ]);

  const openModal = (type: CrmPropostaModalType, item?: CrmProposta) => {
    setModalType(type);
    setSelected(item || null);
    if (type === 'edit' && item) {
      setOportunidadeTituloInicial(item.oportunidade_titulo || '');
      setFormData({
        oportunidade_id: String(item.oportunidade),
        titulo: item.titulo || '',
        conteudo: item.conteudo || '',
        valor_total: item.valor_total || '',
        desconto_tipo: item.desconto_tipo || 'percentual',
        desconto_valor: String(item.desconto_valor || ''),
        status: item.status || 'rascunho',
        nome_vendedor_assinatura: '',
        nome_cliente_assinatura: '',
      });
    }
  };

  const handleOportunidadeChange = useCallback(
    async (id: string) => {
      setFormData((f) => ({ ...f, oportunidade_id: id }));
      if (!id) {
        setItensOportunidade([]);
        setLeadInfo(null);
        setOportunidadeTituloInicial('');
        return;
      }
      loadItensOportunidade(id);
      try {
        const opp = await fetchCrmOportunidade(id);
        setOportunidadeTituloInicial(opp.titulo);
        setFormData((f) => ({
          ...f,
          oportunidade_id: id,
          valor_total: opp.valor ? String(opp.valor) : f.valor_total,
        }));
        if (opp.lead) loadLeadInfo(opp.lead);
        else setLeadInfo(null);
      } catch {
        setLeadInfo(null);
      }
    },
    [loadItensOportunidade, loadLeadInfo, setLeadInfo],
  );

  const closeModal = () => {
    setModalType(null);
    setSelected(null);
    setOportunidadeTituloInicial('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.titulo.trim()) {
      toast.warning('Título é obrigatório');
      return;
    }
    if (!formData.oportunidade_id) {
      toast.warning('Selecione uma oportunidade');
      return;
    }
    try {
      setSubmitting(true);
      const payload = {
        oportunidade: parseInt(formData.oportunidade_id, 10),
        titulo: formData.titulo.trim(),
        conteudo: formData.conteudo,
        valor_total: formData.valor_total ? parseFloat(formData.valor_total) : null,
        desconto_tipo: formData.desconto_tipo || 'percentual',
        desconto_valor: formData.desconto_valor ? parseFloat(formData.desconto_valor) : 0,
        status: formData.status,
        nome_vendedor_assinatura: formData.nome_vendedor_assinatura?.trim() || null,
        nome_cliente_assinatura: formData.nome_cliente_assinatura?.trim() || null,
      };
      if (modalType === 'edit' && selected) {
        const assinaturaAntes = selected.status_assinatura;
        await apiClient.put(`/crm-vendas/propostas/${selected.id}/`, payload);
        await reenviarAssinaturaAposEdicaoSeNecessario('proposta', selected.id, assinaturaAntes);
      }
      await loadPropostas(true);
      closeModal();
      toast.success('Proposta salva com sucesso.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`/crm-vendas/propostas/${selected.id}/`);
      await loadPropostas(true);
      closeModal();
      toast.success('Proposta excluída.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
    } finally {
      setSubmitting(false);
    }
  };

  const filtroOpcoes = ['', 'rascunho', 'enviada', 'pedido', 'cancelada'].map((s) => ({
    value: s,
    label:
      s === ''
        ? `Todos (${filtroStatus === '' ? totalCount : propostas.length})`
        : `${STATUS_LABEL[s] || s} (${
            filtroStatus === s
              ? totalCount
              : propostas.filter(
                  (p) =>
                    p.status === s ||
                    (s === 'pedido' && (p.status === 'aceita' || p.status === 'pedido')),
                ).length
          })`,
  }));

  return {
    slug,
    propostas,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    filtroStatus,
    setFiltroStatus,
    filtroOpcoes,
    exibirColunaAssinatura,
    propostaWhatsappHabilitada,
    enviandoId,
    handleEnviarCliente,
    handleDownloadPdf,
    handleDownloadDocx,
    modalType,
    selected,
    formData,
    setFormData,
    submitting,
    salvandoPadrao,
    templates,
    alterandoStatus,
    menuAberto,
    setMenuAberto,
    lojaInfo,
    leadInfo,
    vendedorNome,
    itensOportunidade,
    oportunidadeTituloInicial,
    openModal,
    closeModal,
    handleOportunidadeChange,
    handleSubmit,
    handleDelete,
    handleSalvarComoPadrao,
    handleMarcarComoAssinado,
    handleConfirmarPedido,
    handleCancelarProposta,
  };
}
