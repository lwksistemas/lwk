'use client';

import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import {
  CRM_CONTRATO_STATUS_LABEL as STATUS_LABEL,
  CRM_STATUS_ASSINATURA_LABEL as STATUS_ASSINATURA_LABEL,
} from '@/lib/crm-constants';
import { Plus, Eye, Edit2, Trash2, X, FileSignature, ArrowRight, Mail, MessageCircle } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import BotaoAssinaturaDigital from '@/components/crm-vendas/BotaoAssinaturaDigital';
import type { LojaInfo, LeadInfo } from '@/components/crm-vendas/modals/ModalPropostaForm';
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
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [leadInfo, setLeadInfo] = useState<LeadInfo | null>(null);
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
    status: 'rascunho' as string,
    nome_vendedor_assinatura: '',
    nome_cliente_assinatura: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [enviandoId, setEnviandoId] = useState<number | null>(null);
  const [vendedorNome, setVendedorNome] = useState<string>('');

  const handleEnviarCliente = async (contratoId: number, canal: 'email' | 'whatsapp') => {
    setEnviandoId(contratoId);
    try {
      await apiClient.post(`/crm-vendas/contratos/${contratoId}/enviar_cliente/`, { canal });
      alert(`Enviado por ${canal === 'email' ? 'e-mail' : 'WhatsApp'} com sucesso!`);
      await loadContratos();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao enviar.');
    } finally {
      setEnviandoId(null);
    }
  };

  const loadContratos = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Contrato[] | { results: Contrato[] }>('/crm-vendas/contratos/');
      setContratos(normalizeListResponse(res.data));
      setError(null);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Erro ao carregar contratos.');
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

  const loadLojaInfo = useCallback(async () => {
    try {
      const res = await apiClient.get<LojaInfo>(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLojaInfo(res.data);
    } catch {
      setLojaInfo(null);
    }
  }, [slug]);

  const loadLeadInfo = useCallback(async (leadId: number) => {
    if (!leadId) {
      setLeadInfo(null);
      return;
    }
    try {
      const res = await apiClient.get<LeadInfo>(`/crm-vendas/leads/${leadId}/`);
      setLeadInfo(res.data);
      // Preencher automaticamente o nome do cliente
      if (res.data.nome && !formData.nome_cliente_assinatura) {
        setFormData((f) => ({ ...f, nome_cliente_assinatura: res.data.nome }));
      }
    } catch {
      setLeadInfo(null);
    }
  }, [formData.nome_cliente_assinatura]);

  const loadVendedorInfo = useCallback(async () => {
    try {
      const res = await apiClient.get<{ nome: string }>('/crm-vendas/vendedores/me/');
      setVendedorNome(res.data.nome);
      // Preencher automaticamente o nome do vendedor
      if (res.data.nome && !formData.nome_vendedor_assinatura) {
        setFormData((f) => ({ ...f, nome_vendedor_assinatura: res.data.nome }));
      }
    } catch {
      setVendedorNome('');
    }
  }, [formData.nome_vendedor_assinatura]);

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
  }, [modalType, formData.oportunidade_id, oportunidades, loadLeadInfo]);

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
        status: formData.status,
        nome_vendedor_assinatura: formData.nome_vendedor_assinatura?.trim() || null,
        nome_cliente_assinatura: formData.nome_cliente_assinatura?.trim() || null,
      };
      if (modalType === 'create') {
        await apiClient.post('/crm-vendas/contratos/', payload);
      } else if (modalType === 'edit' && selected) {
        const assinaturaAntes = selected.status_assinatura;
        await apiClient.put(`/crm-vendas/contratos/${selected.id}/`, payload);
        if (assinaturaAntes === 'aguardando_cliente' || assinaturaAntes === 'aguardando_vendedor') {
          const textoConfirm =
            assinaturaAntes === 'aguardando_cliente'
              ? 'O contrato foi alterado. Deseja reenviar ao cliente o e-mail com o link de assinatura digital?'
              : 'O contrato foi alterado. Deseja reenviar ao vendedor o e-mail com o link de assinatura digital?';
          if (window.confirm(textoConfirm)) {
            try {
              const res = await apiClient.post<{ message?: string }>(
                `/crm-vendas/contratos/${selected.id}/reenviar_para_assinatura/`
              );
              alert(res.data.message || 'Link reenviado.');
            } catch (err: unknown) {
              const ex = err as { response?: { data?: { detail?: string } } };
              alert(ex.response?.data?.detail || 'Erro ao reenviar assinatura.');
            }
          }
        }
      }
      await loadContratos();
      closeModal();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao salvar.');
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
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao excluir.');
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
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Título</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Oportunidade</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Ações</th>
              </tr>
            </thead>
            <tbody>
              {contratos.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-gray-500 dark:text-gray-400">
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
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{c.titulo || c.numero || `Contrato #${c.id}`}</td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{c.oportunidade_titulo}</td>
                    <td className="py-3 px-4">
                      {/* Mostrar status de assinatura se houver, senão mostrar status normal */}
                      {c.status_assinatura && c.status_assinatura !== 'rascunho' ? (
                        <span className={`inline-block px-2 py-0.5 rounded text-xs ${
                          c.status_assinatura === 'concluido' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' :
                          c.status_assinatura === 'aguardando_vendedor' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700' :
                          c.status_assinatura === 'aguardando_cliente' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700' :
                          'bg-gray-100 dark:bg-gray-700 text-gray-600'
                        }`}>
                          {STATUS_ASSINATURA_LABEL[c.status_assinatura] || c.status_assinatura}
                        </span>
                      ) : (
                        <span className={`inline-block px-2 py-0.5 rounded text-xs ${
                          c.status === 'assinado' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' :
                          c.status === 'cancelado' ? 'bg-red-100 dark:bg-red-900/30 text-red-700' :
                          c.status === 'enviado' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700' :
                          'bg-gray-100 dark:bg-gray-700 text-gray-600'
                        }`}>
                          {STATUS_LABEL[c.status] || c.status}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-end gap-1 flex-wrap">
                        <BotaoAssinaturaDigital
                          tipoDocumento="contrato"
                          documentoId={c.id}
                          statusAssinatura={c.status_assinatura}
                          leadEmail={c.lead_email}
                          onSucesso={loadContratos}
                        />
                        <button type="button" onClick={() => handleEnviarCliente(c.id, 'email')} disabled={enviandoId !== null} className="p-1.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50" title="Enviar por e-mail"><Mail size={16} /></button>
                        <button type="button" onClick={() => handleEnviarCliente(c.id, 'whatsapp')} disabled={enviandoId !== null} className="p-1.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50" title="Enviar por WhatsApp"><MessageCircle size={16} /></button>
                        <button type="button" onClick={() => openModal('view', c)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="Visualizar"><Eye size={16} /></button>
                        <button type="button" onClick={() => openModal('edit', c)} className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="Editar"><Edit2 size={16} /></button>
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

      {modalType === 'view' && (
        <>
          <div className="fixed inset-0 bg-black/50 z-[80]" onClick={closeModal} />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Detalhes</h2>
                <button type="button" onClick={closeModal} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"><X size={20} /></button>
              </div>
              <div className="p-6">
                {selected && (
                  <div className="space-y-3">
                    <p><span className="font-medium">Título:</span> {selected.titulo}</p>
                    <p><span className="font-medium">Oportunidade:</span> {selected.oportunidade_titulo}</p>
                    <p><span className="font-medium">Lead:</span> {selected.lead_nome}</p>
                    <p><span className="font-medium">Status:</span> {STATUS_LABEL[selected.status] || selected.status}</p>
                    {selected.valor_total && <p><span className="font-medium">Valor:</span> {parseFloat(selected.valor_total).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</p>}
                    {selected.conteudo && <p><span className="font-medium">Conteúdo:</span><br /><pre className="whitespace-pre-wrap text-sm mt-1">{selected.conteudo}</pre></p>}
                    <button type="button" onClick={closeModal} className="w-full mt-4 py-2 border rounded-lg">Fechar</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {modalType === 'delete' && (
        <>
          <div className="fixed inset-0 bg-black/50 z-[80]" onClick={closeModal} />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Excluir</h2>
                <button type="button" onClick={closeModal} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"><X size={20} /></button>
              </div>
              <div className="p-6">
                {selected && (
                  <div className="space-y-4">
                    <p className="text-gray-600 dark:text-gray-400">Deseja excluir &quot;{selected.titulo || selected.numero || 'este contrato'}&quot;?</p>
                    <div className="flex gap-2">
                      <button type="button" onClick={closeModal} className="flex-1 px-4 py-2 border rounded-lg">Cancelar</button>
                      <button type="button" onClick={handleDelete} disabled={submitting} className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50">
                        {submitting ? 'Excluindo...' : 'Excluir'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
