'use client';

import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail, downloadBlobAsFile, crmMensagemEnvioCanalSucesso } from '@/lib/crm-utils';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { reenviarAssinaturaAposEdicaoSeNecessario } from '@/lib/crm-reenviar-assinatura';
import { crmEnviarCliente } from '@/lib/crm-enviar-cliente';
import {
  CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL,
  CRM_STATUS_ASSINATURA_LABEL as STATUS_ASSINATURA_LABEL,
} from '@/lib/crm-constants';
import { Plus, Eye, Edit2, Trash2, ClipboardList, ArrowRight, Mail, MessageCircle, FileText, FileSignature } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import BotaoAssinaturaDigital from '@/components/crm-vendas/BotaoAssinaturaDigital';
import CrmConfirmDeleteModal from '@/components/crm-vendas/CrmConfirmDeleteModal';
import CrmDocumentoStatusBadge from '@/components/crm-vendas/CrmDocumentoStatusBadge';
import CrmDocumentoDetalhesModal from '@/components/crm-vendas/CrmDocumentoDetalhesModal';
import type { FormDataProposta } from '@/components/crm-vendas/modals/ModalPropostaForm';
import type {
  CrmPropostaOportunidadeOption,
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
  titulo: string;
  conteudo: string;
  valor_total: string | null;
  status: string;
  status_assinatura?: string;
  data_envio: string | null;
  data_resposta: string | null;
  created_at: string;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

export default function CrmVendasPropostasPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [propostas, setPropostas] = useState<Proposta[]>([]);
  const [oportunidades, setOportunidades] = useState<CrmPropostaOportunidadeOption[]>([]);
  const [itensOportunidade, setItensOportunidade] = useState<CrmOportunidadeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selected, setSelected] = useState<Proposta | null>(null);
  const [formData, setFormData] = useState<FormDataProposta>({
    oportunidade_id: '',
    titulo: '',
    conteudo: '',
    valor_total: '',
    status: 'rascunho' as string,
    nome_vendedor_assinatura: '',
    nome_cliente_assinatura: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [enviandoId, setEnviandoId] = useState<number | null>(null);
  const [salvandoPadrao, setSalvandoPadrao] = useState(false);
  const [propostaConteudoPadrao, setPropostaConteudoPadrao] = useState('');
  const [templates, setTemplates] = useState<CrmPropostaTemplate[]>([]);

  const { lojaInfo, loadLojaInfo } = useCrmLojaInfoPublica(slug);
  const { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo } = useCrmLeadEVendedorForm(
    formData,
    setFormData
  );

  const handleEnviarCliente = async (propostaId: number, canal: 'email' | 'whatsapp') => {
    setEnviandoId(propostaId);
    try {
      await crmEnviarCliente('propostas', propostaId, canal);
      alert(crmMensagemEnvioCanalSucesso(canal));
      await loadPropostas(true);
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao enviar.'));
    } finally {
      setEnviandoId(null);
    }
  };

  const handleDownloadPdf = async (propostaId: number, titulo: string) => {
    try {
      const response = await apiClient.get(`/crm-vendas/propostas/${propostaId}/download_pdf/`, {
        responseType: 'blob',
      });
      downloadBlobAsFile(
        response.data instanceof Blob ? response.data : new Blob([response.data]),
        `proposta_${propostaId}_${titulo.replace(/\s+/g, '_')}.pdf`
      );
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao baixar PDF.'));
    }
  };

  /** silent: não ativa loading em tela cheia (evita sumir a lista após salvar/excluir). */
  const loadPropostas = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const res = await apiClient.get<Proposta[] | { results: Proposta[] }>('/crm-vendas/propostas/');
      setPropostas(normalizeListResponse(res.data));
      setError(null);
    } catch (err: unknown) {
      setError(getCrmApiErrorDetail(err, 'Erro ao carregar propostas.'));
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  const loadOportunidades = useCallback(async () => {
    try {
      const res = await apiClient.get<
        CrmPropostaOportunidadeOption[] | { results: CrmPropostaOportunidadeOption[] }
      >('/crm-vendas/oportunidades/');
      setOportunidades(normalizeListResponse(res.data));
    } catch {
      setOportunidades([]);
    }
  }, []);

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

  useEffect(() => {
    loadPropostas();
  }, [loadPropostas]);

  useEffect(() => {
    if (modalType === 'edit') {
      loadOportunidades();
      loadLojaInfo();
      loadCrmConfig();
      loadTemplates();
      loadVendedorInfo();
    }
  }, [modalType, loadOportunidades, loadLojaInfo, loadCrmConfig, loadTemplates, loadVendedorInfo]);

  useEffect(() => {
    if ((modalType === 'create' || modalType === 'edit') && formData.oportunidade_id) {
      loadItensOportunidade(formData.oportunidade_id);
      const opp = oportunidades.find((o) => String(o.id) === formData.oportunidade_id);
      if (opp?.lead) {
        loadLeadInfo(opp.lead);
      } else {
        setLeadInfo(null);
      }
    } else if (!formData.oportunidade_id) {
      setItensOportunidade([]);
      setLeadInfo(null);
    }
  }, [modalType, formData.oportunidade_id, oportunidades, loadItensOportunidade, loadLeadInfo, setLeadInfo]);

  const openModal = (type: ModalType, item?: Proposta) => {
    setModalType(type);
    setSelected(item || null);
    if (type === 'edit' && item) {
      setFormData({
        oportunidade_id: String(item.oportunidade),
        titulo: item.titulo || '',
        conteudo: item.conteudo || '',
        valor_total: item.valor_total || '',
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
        status: 'rascunho',
        nome_vendedor_assinatura: '',
        nome_cliente_assinatura: '',
      });
      setItensOportunidade([]);
      setLeadInfo(null);
    }
  };

  const handleOportunidadeChange = (id: string) => {
    const opp = oportunidades.find((o) => String(o.id) === id);
    setFormData((f) => ({
      ...f,
      oportunidade_id: id,
      valor_total: opp?.valor ? String(opp.valor) : f.valor_total,
    }));
    loadItensOportunidade(id);
    if (opp?.lead) {
      loadLeadInfo(opp.lead);
    } else {
      setLeadInfo(null);
    }
  };

  const closeModal = () => {
    setModalType(null);
    setSelected(null);
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
        status: formData.status,
        nome_vendedor_assinatura: formData.nome_vendedor_assinatura?.trim() || null,
        nome_cliente_assinatura: formData.nome_cliente_assinatura?.trim() || null,
      };
      if (modalType === 'create') {
        await apiClient.post('/crm-vendas/propostas/', payload);
      } else if (modalType === 'edit' && selected) {
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

  if (loading && propostas.length === 0) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
        <SkeletonTable rows={5} columns={5} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Criar Propostas</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Crie e gerencie propostas comerciais vinculadas às oportunidades
          </p>
        </div>
        <div className="flex gap-2">
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
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-[#16325c] rounded-lg shadow border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[500px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-[#0d1f3c] bg-gray-50 dark:bg-[#0d1f3c]/50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Título</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Oportunidade</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ações</th>
              </tr>
            </thead>
            <tbody>
              {propostas.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-gray-500 dark:text-gray-400">
                    <ClipboardList size={48} className="mx-auto mb-3 opacity-30" />
                    <p className="font-medium">Nenhuma proposta cadastrada</p>
                    <p className="text-sm mt-1">Clique em &quot;Nova Proposta&quot; ou vá ao Pipeline para criar</p>
                    <Link
                      href={`/loja/${slug}/crm-vendas/pipeline`}
                      className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg text-sm"
                    >
                      Ir para Pipeline
                      <ArrowRight size={16} />
                    </Link>
                  </td>
                </tr>
              ) : (
                propostas.map((p) => (
                  <tr key={p.id} className="border-b border-gray-100 dark:border-[#0d1f3c] hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/30">
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
                    <td className="py-3 px-4">
                      <div className="flex justify-end gap-1 flex-wrap">
                        <BotaoAssinaturaDigital
                          tipoDocumento="proposta"
                          documentoId={p.id}
                          statusAssinatura={p.status_assinatura}
                          leadEmail={p.lead_email}
                          onSucesso={() => loadPropostas(true)}
                        />
                        <button
                          type="button"
                          onClick={() => handleDownloadPdf(p.id, p.titulo)}
                          className="p-1.5 rounded bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50"
                          title="Baixar PDF"
                        >
                          <FileText size={16} />
                        </button>
                        <button type="button" onClick={() => handleEnviarCliente(p.id, 'email')} disabled={enviandoId !== null} className="p-1.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50" title="Enviar PDF por e-mail"><Mail size={16} /></button>
                        <button type="button" onClick={() => handleEnviarCliente(p.id, 'whatsapp')} disabled={enviandoId !== null} className="p-1.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50" title="Enviar PDF por WhatsApp"><MessageCircle size={16} /></button>
                        <button type="button" onClick={() => openModal('view', p)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="Visualizar"><Eye size={16} /></button>
                        <button type="button" onClick={() => openModal('edit', p)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="Editar"><Edit2 size={16} /></button>
                        <button type="button" onClick={() => openModal('delete', p)} className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600" title="Excluir"><Trash2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {modalType === 'edit' && (
        <ModalPropostaForm
          title="Editar Proposta"
          form={formData}
          formErro={null}
          enviando={submitting}
          lojaInfo={lojaInfo}
          leadInfo={leadInfo}
          oportunidades={oportunidades}
          itensOportunidade={itensOportunidade}
          statusOpcoes={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))}
          onFormChange={setFormData}
          onOportunidadeChange={handleOportunidadeChange}
          onSubmit={handleSubmit}
          onClose={closeModal}
          isEdit={modalType === 'edit'}
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
    </div>
  );
}
