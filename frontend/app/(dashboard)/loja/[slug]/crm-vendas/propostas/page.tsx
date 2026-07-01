'use client';

import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import {
  normalizeListResponse,
  getCrmApiErrorDetail,
  fetchCrmOportunidade,
} from '@/lib/crm-utils';
import CrmPaginationBar from '@/components/crm-vendas/CrmPaginationBar';
import { usePaginatedList } from '@/hooks/usePaginatedList';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import { useCrmDocumentoActions } from '@/hooks/useCrmDocumentoActions';
import { reenviarAssinaturaAposEdicaoSeNecessario } from '@/lib/crm-reenviar-assinatura';
import {
  CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL,
  CRM_STATUS_ASSINATURA_LABEL as STATUS_ASSINATURA_LABEL,
} from '@/lib/crm-constants';
import { formatDate } from '@/lib/financeiro-helpers';
import { Plus, Eye, Edit2, Trash2, ClipboardList, FileText, FileSignature, Ban, ShoppingCart } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import CrmEnviarAssinaturaColuna from '@/components/crm-vendas/CrmEnviarAssinaturaColuna';
import CrmConfirmDeleteModal from '@/components/crm-vendas/CrmConfirmDeleteModal';
import CrmCancelarModal from '@/components/crm-vendas/CrmCancelarModal';
import CrmDocumentoStatusBadge from '@/components/crm-vendas/CrmDocumentoStatusBadge';
import CrmDocumentoDetalhesModal from '@/components/crm-vendas/CrmDocumentoDetalhesModal';
import {
  CrmDocumentoEmptyState,
  CrmDocumentoListPageShell,
} from '@/components/crm-vendas/documentos/CrmDocumentoListPageShell';
import CrmDocumentoMaisAcoesMenu from '@/components/crm-vendas/documentos/CrmDocumentoMaisAcoesMenu';
import CrmDocumentoArquivoAcoes from '@/components/crm-vendas/documentos/CrmDocumentoArquivoAcoes';
import type { FormDataProposta } from '@/components/crm-vendas/modals/ModalPropostaForm';
import type {
  CrmOportunidadeItem,
  CrmPropostaTemplate,
} from '@/lib/crm-proposta-form-types';

const ModalPropostaForm = dynamic(() => import('@/components/crm-vendas/modals/ModalPropostaForm'), { ssr: false });

interface Proposta {
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

type ModalType = 'edit' | 'view' | 'delete' | 'cancelar' | null;

/** Proposta finalizada — não exibe coluna de envio de assinatura. */
function propostaOcultaColunaAssinatura(p: Proposta): boolean {
  return (
    p.status === 'cancelada' ||
    p.status === 'pedido' ||
    p.status_assinatura === 'concluido'
  );
}

export default function CrmVendasPropostasPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
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
  } = usePaginatedList<Proposta>('/crm-vendas/propostas/', {
    params: { status: statusParam },
    errorFallback: 'Erro ao carregar propostas.',
  });

  const exibirColunaAssinatura = propostas.some(
    (p) => !propostaOcultaColunaAssinatura(p),
  );

  const [itensOportunidade, setItensOportunidade] = useState<CrmOportunidadeItem[]>([]);
  const [oportunidadeTituloInicial, setOportunidadeTituloInicial] = useState('');
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selected, setSelected] = useState<Proposta | null>(null);
  const [formData, setFormData] = useState<FormDataProposta>({
    oportunidade_id: '',
    titulo: '',
    conteudo: '',
    valor_total: '',
    desconto_tipo: 'percentual',
    desconto_valor: '',
    status: 'rascunho' as string,
    nome_vendedor_assinatura: '',
    nome_cliente_assinatura: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [salvandoPadrao, setSalvandoPadrao] = useState(false);
  const [propostaConteudoPadrao, setPropostaConteudoPadrao] = useState('');
  const [templates, setTemplates] = useState<CrmPropostaTemplate[]>([]);
  const [alterandoStatus, setAlterandoStatus] = useState<number | null>(null);
  const [menuAberto, setMenuAberto] = useState<number | null>(null);

  const { enviandoId, handleEnviarCliente, handleDownloadPdf, handleDownloadDocx } = useCrmDocumentoActions(
    'propostas',
    loadPropostas,
  );

  const { lojaInfo, loadLojaInfo } = useCrmLojaInfoPublica(slug);
  const { proposta: propostaWhatsappHabilitada } = useWhatsappEnvioFlags();
  const { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo } = useCrmLeadEVendedorForm(
    formData,
    setFormData
  );

  const loadItensOportunidade = useCallback(async (oportunidadeId: string) => {
    if (!oportunidadeId) {
      setItensOportunidade([]);
      return;
    }
    try {
      const res = await apiClient.get<CrmOportunidadeItem[] | { results: CrmOportunidadeItem[] }>(
        `/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidadeId}`
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
        '/crm-vendas/proposta-templates/'
      );
      setTemplates(normalizeListResponse(res.data));
    } catch {
      setTemplates([]);
    }
  }, []);

  const handleSalvarComoPadrao = useCallback(async (conteudo: string) => {
    try {
      setSalvandoPadrao(true);
      await apiClient.patch('/crm-vendas/config/', { proposta_conteudo_padrao: conteudo });
      setPropostaConteudoPadrao(conteudo);
      alert('Proposta PADRAO salva com sucesso! O conteúdo será usado em novas propostas.');
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
    } finally {
      setSalvandoPadrao(false);
    }
  }, []);

  const handleMarcarComoAssinado = async (propostaId: number) => {
    if (!confirm('Marcar esta proposta como assinada manualmente?\n\nUse esta opção quando o cliente assinar de outra forma (manual, gov.br, etc).')) {
      return;
    }
    try {
      setAlterandoStatus(propostaId);
      await apiClient.patch(`/crm-vendas/propostas/${propostaId}/`, {
        status_assinatura: 'concluido',
        status: 'aceita',
      });
      await loadPropostas(true);
      alert('Proposta marcada como assinada com sucesso!');
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao atualizar status.'));
    } finally {
      setAlterandoStatus(null);
    }
  };

  const handleConfirmarPedido = async (propostaId: number) => {
    if (!confirm('Confirmar esta proposta como Pedido?\n\nIsso indica que o cliente confirmou o pedido formal e está pronto para gerar o contrato.')) {
      return;
    }
    try {
      setAlterandoStatus(propostaId);
      await apiClient.post(`/crm-vendas/propostas/${propostaId}/confirmar_pedido/`);
      await loadPropostas(true);
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao confirmar pedido.'));
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
  }, [modalType, formData.oportunidade_id, loadLojaInfo, loadCrmConfig, loadTemplates, loadVendedorInfo, loadItensOportunidade, loadLeadInfo, setLeadInfo]);

  const openModal = (type: ModalType, item?: Proposta) => {
    setModalType(type);
    setSelected(item || null);
    if (type === 'edit' && item) {
      setOportunidadeTituloInicial(item.oportunidade_titulo || '');
      setFormData({
        oportunidade_id: String(item.oportunidade),
        titulo: item.titulo || '',
        conteudo: item.conteudo || '',
        valor_total: item.valor_total || '',
        desconto_tipo: (item as unknown as { desconto_tipo?: 'percentual' | 'valor' }).desconto_tipo || 'percentual',
        desconto_valor: String((item as unknown as { desconto_valor?: string }).desconto_valor || ''),
        status: item.status || 'rascunho',
        nome_vendedor_assinatura: '',
        nome_cliente_assinatura: '',
      });
    } else if (type === 'create') {
      // Usar template padrão se existir, senão usar proposta_conteudo_padrao
      const templatePadrao = templates.find(t => t.is_padrao);
      const conteudoInicial = templatePadrao?.conteudo || propostaConteudoPadrao;
      
      setFormData({
        oportunidade_id: '',
        titulo: '',
        conteudo: conteudoInicial,
        valor_total: '',
        desconto_tipo: 'percentual',
        desconto_valor: '',
        status: 'rascunho',
        nome_vendedor_assinatura: '',
        nome_cliente_assinatura: '',
      });
      setItensOportunidade([]);
      setLeadInfo(null);
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
      alert('Título é obrigatório');
      return;
    }
    if (!formData.oportunidade_id) {
      alert('Selecione uma oportunidade');
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
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
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
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
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

  if (loading && propostas.length === 0) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} columns={6} />
      </div>
    );
  }

  return (
    <>
    <CrmDocumentoListPageShell
      titulo="Criar Propostas"
      subtitulo="Crie e gerencie propostas comerciais vinculadas às oportunidades"
      slug={slug}
      error={error}
      filtroStatus={filtroStatus}
      onFiltroChange={setFiltroStatus}
      filtroOpcoes={filtroOpcoes}
      headerActions={
        <>
          <Link
            href={`/loja/${slug}/crm-vendas/proposta-templates`}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded text-sm font-medium transition-colors shadow-sm"
          >
            <FileText size={18} />
            <span>Gerenciar Templates</span>
          </Link>
          <Link
            href={`/loja/${slug}/crm-vendas/propostas/nova`}
            className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
          >
            <Plus size={18} />
            <span>Nova Proposta</span>
          </Link>
        </>
      }
    >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[500px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-[#0d1f3c] bg-gray-50 dark:bg-[#0d1f3c]/50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Número</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Título</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Oportunidade</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                {exibirColunaAssinatura && (
                  <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase w-28">
                    <span className="block">Assinatura</span>
                    <span className="block text-[9px] font-normal normal-case text-gray-500 dark:text-gray-400">Cliente / vendedor</span>
                  </th>
                )}
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase whitespace-nowrap">Emissão</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ações</th>
              </tr>
            </thead>
            <tbody>
              {propostas.length === 0 ? (
                <tr>
                  <CrmDocumentoEmptyState
                    icon={ClipboardList}
                    titulo="Nenhuma proposta cadastrada"
                    subtitulo='Clique em "Nova Proposta" ou vá ao Pipeline para criar'
                    slug={slug}
                  />
                </tr>
              ) : (
                propostas.map((p) => (
                  <tr key={p.id} className="border-b border-gray-100 dark:border-[#0d1f3c] hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/30">
                    <td className="py-3 px-4 font-mono text-sm text-gray-600 dark:text-gray-400">#{p.numero || '---'}</td>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{p.titulo}</td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{p.oportunidade_titulo}</td>
                    <td className="py-3 px-4">
                      <CrmDocumentoStatusBadge
                        statusAssinatura={p.status_assinatura}
                        status={p.status}
                        labelsComercial={STATUS_LABEL}
                        labelsAssinatura={STATUS_ASSINATURA_LABEL}
                        variante="proposta"
                      />
                    </td>
                    {exibirColunaAssinatura && (
                      <td className="py-3 px-4">
                        {propostaOcultaColunaAssinatura(p) ? (
                          <span className="text-gray-300 dark:text-gray-600 text-center block">—</span>
                        ) : (
                          <CrmEnviarAssinaturaColuna
                            statusAssinatura={p.status_assinatura}
                            whatsappHabilitado={propostaWhatsappHabilitada}
                            enviando={enviandoId === p.id}
                            onEnviar={(canal) => handleEnviarCliente(p, canal)}
                          />
                        )}
                      </td>
                    )}
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                      {formatDate(p.created_at)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-end items-center gap-1">
                        <button type="button" onClick={() => openModal('view', p)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300" title="Visualizar"><Eye size={16} /></button>
                        {p.status !== 'cancelada' && (
                          <button type="button" onClick={() => openModal('edit', p)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300" title="Editar"><Edit2 size={16} /></button>
                        )}
                        <CrmDocumentoMaisAcoesMenu
                          itemId={p.id}
                          aberto={menuAberto === p.id}
                          onToggle={() => setMenuAberto(menuAberto === p.id ? null : p.id)}
                          onClose={() => setMenuAberto(null)}
                          placement="fixed"
                        >
                          <CrmDocumentoArquivoAcoes
                            somentePdf={p.status === 'cancelada'}
                            motivoCancelamento={p.status === 'cancelada' ? p.motivo_cancelamento : undefined}
                            onDownloadPdf={() => {
                              handleDownloadPdf(p.id, p.titulo);
                              setMenuAberto(null);
                            }}
                            onDownloadDocx={() => {
                              handleDownloadDocx(p.id, p.titulo);
                              setMenuAberto(null);
                            }}
                          />
                          {p.status !== 'cancelada' && (
                            <>
                              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                              {p.status_assinatura !== 'concluido' && (
                                <button
                                  type="button"
                                  onClick={() => {
                                    handleMarcarComoAssinado(p.id);
                                    setMenuAberto(null);
                                  }}
                                  disabled={alterandoStatus !== null}
                                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
                                >
                                  <FileSignature size={15} className="text-purple-500" /> Marcar como assinado
                                </button>
                              )}
                              {p.status === 'aceita' && p.status_assinatura !== 'concluido' && (
                                <button
                                  type="button"
                                  onClick={() => {
                                    handleConfirmarPedido(p.id);
                                    setMenuAberto(null);
                                  }}
                                  disabled={alterandoStatus !== null}
                                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-emerald-700 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 disabled:opacity-50 font-medium"
                                >
                                  <ShoppingCart size={15} className="text-emerald-600" /> Confirmar como Pedido
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => {
                                  openModal('cancelar', p);
                                  setMenuAberto(null);
                                }}
                                disabled={alterandoStatus !== null}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
                              >
                                <Ban size={15} className="text-red-500" /> Cancelar proposta
                              </button>
                              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                              <button
                                type="button"
                                onClick={() => {
                                  openModal('delete', p);
                                  setMenuAberto(null);
                                }}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                              >
                                <Trash2 size={15} /> Excluir proposta
                              </button>
                            </>
                          )}
                        </CrmDocumentoMaisAcoesMenu>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      <CrmPaginationBar
        page={page}
        totalPages={totalPages}
        totalCount={totalCount}
        pageSize={pageSize}
        loading={loading}
        itemLabel="propostas"
        onPageChange={setPage}
      />
    </CrmDocumentoListPageShell>

      <div className="px-4 py-3 bg-gray-50 dark:bg-[#0d1f3c]/30 rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de data, hora e endereço IP.
        </p>
      </div>

      {modalType === 'edit' && (
        <ModalPropostaForm
          title="Editar Proposta"
          form={formData}
          formErro={null}
          enviando={submitting}
          lojaInfo={lojaInfo}
          leadInfo={leadInfo}
          itensOportunidade={itensOportunidade}
          statusOpcoes={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))}
          onFormChange={setFormData}
          onOportunidadeChange={handleOportunidadeChange}
          onSubmit={handleSubmit}
          onClose={closeModal}
          isEdit={modalType === 'edit'}
          oportunidadeTituloInicial={oportunidadeTituloInicial}
          onSalvarComoPadrao={handleSalvarComoPadrao}
          salvandoPadrao={salvandoPadrao}
          templates={templates}
          onSelecionarTemplate={(conteudo) => setFormData((f) => ({ ...f, conteudo }))}
          vendedorNome={vendedorNome}
        />
      )}

      {modalType === 'view' && selected && (
        <CrmDocumentoDetalhesModal
          aberto
          onClose={closeModal}
          titulo={selected.titulo}
          oportunidadeTitulo={selected.oportunidade_titulo}
          leadNome={selected.lead_nome}
          statusExibicao={STATUS_LABEL[selected.status] || selected.status}
          valorTotal={selected.valor_total}
          descontoTipo={selected.desconto_tipo}
          descontoValor={selected.desconto_valor}
          valorComDesconto={selected.valor_com_desconto}
          conteudo={selected.conteudo}
        />
      )}

      {modalType === 'delete' && selected && (
        <CrmConfirmDeleteModal
          tituloItem={selected.titulo}
          enviando={submitting}
          onClose={closeModal}
          onConfirm={handleDelete}
        />
      )}

      {modalType === 'cancelar' && selected && (
        <CrmCancelarModal
          titulo={selected.titulo}
          tipo="proposta"
          onConfirm={handleCancelarProposta}
          onClose={closeModal}
        />
      )}
    </>
  );
}
