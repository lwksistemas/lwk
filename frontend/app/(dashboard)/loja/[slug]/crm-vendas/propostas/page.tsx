'use client';

import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import { Plus, Eye, Edit2, Trash2, X, ClipboardList, ArrowRight, Mail, MessageCircle, FileText, FileSignature } from 'lucide-react';
import SkeletonTable from '@/components/crm-vendas/SkeletonTable';
import BotaoAssinaturaDigital from '@/components/crm-vendas/BotaoAssinaturaDigital';
import type { LojaInfo, LeadInfo, FormDataProposta } from '@/components/crm-vendas/modals/ModalPropostaForm';

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

interface OportunidadeOption {
  id: number;
  titulo: string;
  lead: number;
  lead_nome: string;
  valor: string;
  etapa: string;
}

interface OportunidadeItem {
  id: number;
  produto_servico: number;
  produto_servico_nome: string;
  produto_servico_tipo: string;
  quantidade: string;
  preco_unitario: string;
  subtotal: number;
  observacao?: string;
}

interface PropostaTemplate {
  id: number;
  nome: string;
  conteudo: string;
  is_padrao: boolean;
  ativo: boolean;
}

type ModalType = 'create' | 'edit' | 'view' | 'delete' | null;

const STATUS_LABEL: Record<string, string> = {
  rascunho: 'Rascunho',
  enviada: 'Enviada',
  aceita: 'Aceita',
  rejeitada: 'Rejeitada',
};

const STATUS_ASSINATURA_LABEL: Record<string, string> = {
  rascunho: 'Rascunho',
  aguardando_cliente: 'Aguardando Cliente',
  aguardando_vendedor: 'Aguardando Vendedor',
  concluido: 'Concluído',
};

export default function CrmVendasPropostasPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [propostas, setPropostas] = useState<Proposta[]>([]);
  const [oportunidades, setOportunidades] = useState<OportunidadeOption[]>([]);
  const [itensOportunidade, setItensOportunidade] = useState<OportunidadeItem[]>([]);
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [leadInfo, setLeadInfo] = useState<LeadInfo | null>(null);
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
  const [templates, setTemplates] = useState<PropostaTemplate[]>([]);
  const [vendedorNome, setVendedorNome] = useState<string>('');

  const handleEnviarCliente = async (propostaId: number, canal: 'email' | 'whatsapp') => {
    setEnviandoId(propostaId);
    try {
      await apiClient.post(`/crm-vendas/propostas/${propostaId}/enviar_cliente/`, { canal });
      alert(`Enviado por ${canal === 'email' ? 'e-mail' : 'WhatsApp'} com sucesso!`);
      await loadPropostas();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao enviar.');
    } finally {
      setEnviandoId(null);
    }
  };

  const loadPropostas = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Proposta[] | { results: Proposta[] }>('/crm-vendas/propostas/');
      setPropostas(normalizeListResponse(res.data));
      setError(null);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Erro ao carregar propostas.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadOportunidades = useCallback(async () => {
    try {
      const res = await apiClient.get<OportunidadeOption[] | { results: OportunidadeOption[] }>(
        '/crm-vendas/oportunidades/'
      );
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
      const res = await apiClient.get<OportunidadeItem[] | { results: OportunidadeItem[] }>(
        `/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidadeId}`
      );
      setItensOportunidade(normalizeListResponse(res.data));
    } catch {
      setItensOportunidade([]);
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
      const res = await apiClient.get<PropostaTemplate[] | { results: PropostaTemplate[] }>('/crm-vendas/proposta-templates/');
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
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao salvar.');
    } finally {
      setSalvandoPadrao(false);
    }
  }, []);

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
  }, [modalType, formData.oportunidade_id, oportunidades, loadItensOportunidade, loadLeadInfo]);

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
        await apiClient.put(`/crm-vendas/propostas/${selected.id}/`, payload);
      }
      await loadPropostas();
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
      await apiClient.delete(`/crm-vendas/propostas/${selected.id}/`);
      await loadPropostas();
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
                      {/* Mostrar status de assinatura se houver, senão mostrar status normal */}
                      {p.status_assinatura && p.status_assinatura !== 'rascunho' ? (
                        <span className={`inline-block px-2 py-0.5 rounded text-xs ${
                          p.status_assinatura === 'concluido' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' :
                          p.status_assinatura === 'aguardando_vendedor' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700' :
                          p.status_assinatura === 'aguardando_cliente' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700' :
                          'bg-gray-100 dark:bg-gray-700 text-gray-600'
                        }`}>
                          {STATUS_ASSINATURA_LABEL[p.status_assinatura] || p.status_assinatura}
                        </span>
                      ) : (
                        <span className={`inline-block px-2 py-0.5 rounded text-xs ${
                          p.status === 'aceita' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' :
                          p.status === 'rejeitada' ? 'bg-red-100 dark:bg-red-900/30 text-red-700' :
                          p.status === 'enviada' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700' :
                          'bg-gray-100 dark:bg-gray-700 text-gray-600'
                        }`}>
                          {STATUS_LABEL[p.status] || p.status}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-end gap-1 flex-wrap">
                        <BotaoAssinaturaDigital
                          tipoDocumento="proposta"
                          documentoId={p.id}
                          statusAssinatura={p.status_assinatura}
                          leadEmail={p.lead_email}
                          onSucesso={loadPropostas}
                        />
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
                    <p className="text-gray-600 dark:text-gray-400">Deseja excluir &quot;{selected.titulo}&quot;?</p>
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
