'use client';

import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail, crmMensagemEnvioCanalSucesso, downloadBlobAsFile } from '@/lib/crm-utils';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { reenviarAssinaturaAposEdicaoSeNecessario } from '@/lib/crm-reenviar-assinatura';
import { crmEnviarCliente } from '@/lib/crm-enviar-cliente';
import {
  CRM_CONTRATO_STATUS_LABEL as STATUS_LABEL,
  CRM_STATUS_ASSINATURA_LABEL as STATUS_ASSINATURA_LABEL,
} from '@/lib/crm-constants';
import { Plus, Eye, Edit2, Trash2, FileSignature, ArrowRight, Mail, MessageCircle, Ban } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import BotaoAssinaturaDigital from '@/components/crm-vendas/BotaoAssinaturaDigital';
import CrmConfirmDeleteModal from '@/components/crm-vendas/CrmConfirmDeleteModal';
import CrmDocumentoStatusBadge from '@/components/crm-vendas/CrmDocumentoStatusBadge';
import CrmDocumentoDetalhesModal from '@/components/crm-vendas/CrmDocumentoDetalhesModal';
import type { FormDataContrato } from '@/components/crm-vendas/modals/ModalContratoForm';

const ModalContratoForm = dynamic(() => import('@/components/crm-vendas/modals/ModalContratoForm'), { ssr: false });

interface Contrato {
  id: number;
  oportunidade: number;
  oportunidade_titulo: string;
  lead_nome: string;
  lead_email?: string;
  numero: string;
  titulo: string;
  conteudo: string;
  valor_total: string | null;
  desconto_tipo: 'percentual' | 'valor';
  desconto_valor: string;
  valor_com_desconto: string | null;
  status: string;
  status_assinatura?: string;
  data_envio: string | null;
  data_assinatura: string | null;
  created_at: string;
}

interface OportunidadeOption {
  id: number;
  titulo: string;
  lead?: number;
  lead_nome: string;
  valor: string;
  etapa: string;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

export default function CrmVendasContratosPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [oportunidades, setOportunidades] = useState<OportunidadeOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selected, setSelected] = useState<Contrato | null>(null);
  const [formData, setFormData] = useState<FormDataContrato>({
    oportunidade_id: '',
    numero: '',
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
  const [enviandoId, setEnviandoId] = useState<number | null>(null);
  const [alterandoStatus, setAlterandoStatus] = useState<number | null>(null);

  const { lojaInfo, loadLojaInfo } = useCrmLojaInfoPublica(slug);
  const { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo } = useCrmLeadEVendedorForm(
    formData,
    setFormData
  );

  const handleEnviarCliente = async (contratoId: number, canal: 'email' | 'whatsapp') => {
    setEnviandoId(contratoId);
    try {
      await crmEnviarCliente('contratos', contratoId, canal);
      alert(crmMensagemEnvioCanalSucesso(canal));
      await loadContratos();
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao enviar.'));
    } finally {
      setEnviandoId(null);
    }
  };

  const handleDownloadPdf = async (contratoId: number, titulo: string) => {
    try {
      const response = await apiClient.get(`/crm-vendas/contratos/${contratoId}/download_pdf/`, {
        responseType: 'blob',
      });
      downloadBlobAsFile(
        response.data instanceof Blob ? response.data : new Blob([response.data]),
        `contrato_${contratoId}_${titulo.replace(/\s+/g, '_')}.pdf`
      );
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao baixar PDF.'));
    }
  };

  const handleDownloadDocx = async (contratoId: number, titulo: string) => {
    try {
      const response = await apiClient.get(`/crm-vendas/contratos/${contratoId}/download_docx/`, {
        responseType: 'blob',
      });
      downloadBlobAsFile(
        response.data instanceof Blob ? response.data : new Blob([response.data]),
        `contrato_${contratoId}_${titulo.replace(/\s+/g, '_')}.docx`
      );
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao baixar Word.'));
    }
  };

  const handleMarcarComoAssinado = async (contratoId: number) => {
    if (!confirm('Marcar este contrato como assinado manualmente?\n\nUse esta opção quando o cliente assinar de outra forma (manual, gov.br, etc).')) {
      return;
    }
    try {
      setAlterandoStatus(contratoId);
      await apiClient.patch(`/crm-vendas/contratos/${contratoId}/`, {
        status_assinatura: 'concluido',
        status: 'assinado',
      });
      await loadContratos();
      alert('Contrato marcado como assinado com sucesso!');
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao atualizar status.'));
    } finally {
      setAlterandoStatus(null);
    }
  };

  const handleCancelarContrato = async (contratoId: number) => {
    if (!confirm('Cancelar este contrato?\n\nO contrato será marcado como cancelado e ficará no histórico de negociações.')) {
      return;
    }
    try {
      setAlterandoStatus(contratoId);
      await apiClient.patch(`/crm-vendas/contratos/${contratoId}/`, {
        status: 'cancelado',
      });
      await loadContratos();
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao cancelar contrato.'));
    } finally {
      setAlterandoStatus(null);
    }
  };

  const loadContratos = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Contrato[] | { results: Contrato[] }>('/crm-vendas/contratos/');
      setContratos(normalizeListResponse(res.data));
      setError(null);
    } catch (err: unknown) {
      setError(getCrmApiErrorDetail(err, 'Erro ao carregar contratos.'));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadOportunidades = useCallback(async () => {
    try {
      const res = await apiClient.get<OportunidadeOption[] | { results: OportunidadeOption[] }>(
        '/crm-vendas/oportunidades/?etapa=closed_won'
      );
      setOportunidades(normalizeListResponse(res.data));
    } catch {
      setOportunidades([]);
    }
  }, []);

  useEffect(() => {
    loadContratos();
  }, [loadContratos]);

  useEffect(() => {
    if (modalType === 'create' || modalType === 'edit') {
      loadOportunidades();
      loadLojaInfo();
      loadVendedorInfo();
    }
  }, [modalType, loadOportunidades, loadLojaInfo, loadVendedorInfo]);

  useEffect(() => {
    if ((modalType === 'create' || modalType === 'edit') && formData.oportunidade_id) {
      const opp = oportunidades.find((o) => String(o.id) === formData.oportunidade_id);
      if (opp?.lead) {
        loadLeadInfo(opp.lead);
      } else {
        setLeadInfo(null);
      }
    } else if (!formData.oportunidade_id) {
      setLeadInfo(null);
    }
  }, [modalType, formData.oportunidade_id, oportunidades, loadLeadInfo, setLeadInfo]);

  const openModal = (type: ModalType, item?: Contrato) => {
    setModalType(type);
    setSelected(item || null);
    if (type === 'edit' && item) {
      setFormData({
        oportunidade_id: String(item.oportunidade),
        numero: item.numero || '',
        titulo: item.titulo || '',
        conteudo: item.conteudo || '',
        valor_total: item.valor_total || '',
        desconto_tipo: item.desconto_tipo || 'percentual',
        desconto_valor: String(item.desconto_valor || ''),
        status: item.status || 'rascunho',
        nome_vendedor_assinatura: '',
        nome_cliente_assinatura: '',
      });
    } else if (type === 'create') {
      setFormData({
        oportunidade_id: '',
        numero: '',
        titulo: '',
        conteudo: '',
        valor_total: '',
        desconto_tipo: 'percentual',
        desconto_valor: '',
        status: 'rascunho',
        nome_vendedor_assinatura: '',
        nome_cliente_assinatura: '',
      });
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
      alert('Selecione uma oportunidade fechada');
      return;
    }
    try {
      setSubmitting(true);
      const payload = {
        oportunidade: parseInt(formData.oportunidade_id, 10),
        numero: formData.numero || undefined,
        titulo: formData.titulo.trim(),
        conteudo: formData.conteudo,
        valor_total: formData.valor_total ? parseFloat(formData.valor_total) : null,
        desconto_tipo: formData.desconto_tipo || 'percentual',
        desconto_valor: formData.desconto_valor ? parseFloat(formData.desconto_valor) : 0,
        status: formData.status,
        nome_vendedor_assinatura: formData.nome_vendedor_assinatura?.trim() || null,
        nome_cliente_assinatura: formData.nome_cliente_assinatura?.trim() || null,
      };
      if (modalType === 'create') {
        await apiClient.post('/crm-vendas/contratos/', payload);
      } else if (modalType === 'edit' && selected) {
        const assinaturaAntes = selected.status_assinatura;
        await apiClient.put(`/crm-vendas/contratos/${selected.id}/`, payload);
        await reenviarAssinaturaAposEdicaoSeNecessario('contrato', selected.id, assinaturaAntes);
      }
      await loadContratos();
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
      await apiClient.delete(`/crm-vendas/contratos/${selected.id}/`);
      await loadContratos();
      closeModal();
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Criar Contrato</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Gere contratos a partir das oportunidades fechadas como ganhas
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href={`/loja/${slug}/crm-vendas/contrato-templates`}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded text-sm font-medium transition-colors shadow-sm"
          >
            <FileSignature size={18} />
            <span>Gerenciar Templates</span>
          </Link>
          <button
            type="button"
            onClick={() => openModal('create')}
            className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
          >
            <Plus size={18} />
            <span>Novo Contrato</span>
          </button>
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
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Número</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Título</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Oportunidade</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ações</th>
              </tr>
            </thead>
            <tbody>
              {contratos.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-gray-500 dark:text-gray-400">
                    <FileSignature size={48} className="mx-auto mb-3 opacity-30" />
                    <p className="font-medium">Nenhum contrato cadastrado</p>
                    <p className="text-sm mt-1">Crie contratos a partir de oportunidades fechadas como ganhas</p>
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
                contratos.map((c) => (
                  <tr key={c.id} className="border-b border-gray-100 dark:border-[#0d1f3c] hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/30">
                    <td className="py-3 px-4 font-mono text-sm text-gray-600 dark:text-gray-400">#{c.numero || '---'}</td>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{c.titulo || `Contrato #${c.id}`}</td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.oportunidade_titulo}</td>
                    <td className="py-3 px-4">
                      <CrmDocumentoStatusBadge
                        statusAssinatura={c.status_assinatura}
                        status={c.status}
                        labelsComercial={STATUS_LABEL}
                        labelsAssinatura={STATUS_ASSINATURA_LABEL}
                        variante="contrato"
                      />
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-end gap-1 flex-wrap">
                        <button
                          type="button"
                          onClick={() => handleDownloadPdf(c.id, c.titulo)}
                          className="px-2 py-1 rounded bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 text-xs"
                          title="Baixar PDF"
                        >
                          PDF
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDownloadDocx(c.id, c.titulo)}
                          className="px-2 py-1 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 text-xs"
                          title="Baixar Word"
                        >
                          Word
                        </button>
                        <BotaoAssinaturaDigital
                          tipoDocumento="contrato"
                          documentoId={c.id}
                          statusAssinatura={c.status_assinatura}
                          leadEmail={c.lead_email}
                          onSucesso={loadContratos}
                        />
                        {c.status_assinatura !== 'concluido' && (
                          <button
                            type="button"
                            onClick={() => handleMarcarComoAssinado(c.id)}
                            disabled={alterandoStatus !== null}
                            className="p-1.5 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 hover:bg-purple-200 dark:hover:bg-purple-900/50 disabled:opacity-50"
                            title="Marcar como assinado manualmente (gov.br, manual, etc)"
                          >
                            <FileSignature size={16} />
                          </button>
                        )}
                        <button type="button" onClick={() => handleEnviarCliente(c.id, 'email')} disabled={enviandoId !== null} className="p-1.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50" title="Enviar por e-mail"><Mail size={16} /></button>
                        <button type="button" onClick={() => handleEnviarCliente(c.id, 'whatsapp')} disabled={enviandoId !== null} className="p-1.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50" title="Enviar por WhatsApp"><MessageCircle size={16} /></button>
                        <button type="button" onClick={() => openModal('view', c)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="Visualizar"><Eye size={16} /></button>
                        <button type="button" onClick={() => openModal('edit', c)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="Editar"><Edit2 size={16} /></button>
                        {c.status !== 'cancelado' && (
                          <button
                            type="button"
                            onClick={() => handleCancelarContrato(c.id)}
                            disabled={alterandoStatus !== null}
                            className="p-1.5 rounded bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-900/50 disabled:opacity-50"
                            title="Cancelar contrato (manter no histórico)"
                          >
                            <Ban size={16} />
                          </button>
                        )}
                        <button type="button" onClick={() => openModal('delete', c)} className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600" title="Excluir"><Trash2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="px-4 py-3 bg-gray-50 dark:bg-[#0d1f3c]/30 rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de data, hora e endereço IP.
        </p>
      </div>

      {(modalType === 'create' || modalType === 'edit') && (
        <ModalContratoForm
          title={modalType === 'create' ? 'Novo Contrato' : 'Editar Contrato'}
          form={formData}
          formErro={null}
          enviando={submitting}
          lojaInfo={lojaInfo}
          leadInfo={leadInfo}
          oportunidades={oportunidades}
          statusOpcoes={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))}
          onFormChange={setFormData}
          onOportunidadeChange={handleOportunidadeChange}
          onSubmit={handleSubmit}
          onClose={closeModal}
          isEdit={modalType === 'edit'}
          vendedorNome={vendedorNome}
        />
      )}

      {modalType === 'view' && selected && (
        <CrmDocumentoDetalhesModal
          aberto
          onClose={closeModal}
          titulo={selected.titulo}
          numero={selected.numero || undefined}
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
          tituloItem={selected.titulo || selected.numero || 'este contrato'}
          enviando={submitting}
          onClose={closeModal}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}
