'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import { ArrowLeft } from 'lucide-react';
import PropostaFormContent from '@/components/crm-vendas/PropostaFormContent';
import type { FormDataProposta } from '@/components/crm-vendas/modals/ModalPropostaForm';
import type {
  CrmPropostaOportunidadeOption,
  CrmOportunidadeItem,
  CrmPropostaTemplate,
} from '@/lib/crm-proposta-form-types';

export default function NovaPropostaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
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
  const [oportunidades, setOportunidades] = useState<CrmPropostaOportunidadeOption[]>([]);
  const [loadingOportunidades, setLoadingOportunidades] = useState(true);
  const [itensOportunidade, setItensOportunidade] = useState<CrmOportunidadeItem[]>([]);
  const [propostaConteudoPadrao, setPropostaConteudoPadrao] = useState('');
  const [templates, setTemplates] = useState<CrmPropostaTemplate[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [salvandoPadrao, setSalvandoPadrao] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);

  const { lojaInfo, loadLojaInfo } = useCrmLojaInfoPublica(slug);
  const { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo } = useCrmLeadEVendedorForm(
    formData,
    setFormData
  );

  const loadOportunidades = useCallback(async () => {
    setLoadingOportunidades(true);
    try {
      const res = await apiClient.get<
        CrmPropostaOportunidadeOption[] | { results: CrmPropostaOportunidadeOption[] }
      >('/crm-vendas/oportunidades/');
      setOportunidades(normalizeListResponse(res.data));
    } catch {
      setOportunidades([]);
    } finally {
      setLoadingOportunidades(false);
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

  useEffect(() => {
    loadOportunidades();
    loadLojaInfo();
    loadCrmConfig();
    loadTemplates();
    loadVendedorInfo();
  }, [loadOportunidades, loadLojaInfo, loadCrmConfig, loadTemplates, loadVendedorInfo]);

  useEffect(() => {
    // Carregar template padrão se existir, senão usar proposta_conteudo_padrao
    if (!formData.conteudo) {
      const templatePadrao = templates.find(t => t.is_padrao);
      const conteudoInicial = templatePadrao?.conteudo || propostaConteudoPadrao;
      if (conteudoInicial) {
        setFormData((f) => ({ ...f, conteudo: conteudoInicial }));
      }
    }
    // Intencional: reagir só ao carregar templates/padrão, não a cada tecla em conteudo.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- formData.conteudo omitido de propósito
  }, [templates, propostaConteudoPadrao]);

  useEffect(() => {
    if (formData.oportunidade_id) {
      loadItensOportunidade(formData.oportunidade_id);
      const opp = oportunidades.find((o) => String(o.id) === formData.oportunidade_id);
      if (opp?.lead) {
        loadLeadInfo(opp.lead);
      } else {
        setLeadInfo(null);
      }
    } else {
      setItensOportunidade([]);
      setLeadInfo(null);
    }
  }, [formData.oportunidade_id, oportunidades, loadItensOportunidade, loadLeadInfo, setLeadInfo]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    if (!formData.titulo.trim()) {
      setFormErro('Título é obrigatório');
      return;
    }
    if (!formData.oportunidade_id) {
      setFormErro('Selecione uma oportunidade');
      return;
    }
    try {
      setSubmitting(true);
      await apiClient.post('/crm-vendas/propostas/', {
        oportunidade: parseInt(formData.oportunidade_id, 10),
        titulo: formData.titulo.trim(),
        conteudo: formData.conteudo,
        valor_total: formData.valor_total ? parseFloat(formData.valor_total) : null,
        desconto_tipo: formData.desconto_tipo || 'percentual',
        desconto_valor: formData.desconto_valor ? parseFloat(formData.desconto_valor) : 0,
        status: formData.status,
        nome_vendedor_assinatura: formData.nome_vendedor_assinatura?.trim() || null,
        nome_cliente_assinatura: formData.nome_cliente_assinatura?.trim() || null,
      });
      router.push(`/loja/${slug}/crm-vendas/propostas`);
    } catch (err: unknown) {
      setFormErro(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-full">
      <div className="flex items-center gap-4 mb-6">
        <Link
          href={`/loja/${slug}/crm-vendas/propostas`}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
          aria-label="Voltar"
        >
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">Nova Proposta</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Preencha os dados da proposta comercial
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-[#0d1f3c] p-6 w-full">
          <PropostaFormContent
          form={formData}
          formErro={formErro}
          enviando={submitting}
          lojaInfo={lojaInfo}
          leadInfo={leadInfo}
          oportunidades={oportunidades}
          itensOportunidade={itensOportunidade}
          statusOpcoes={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))}
          onFormChange={setFormData}
          onOportunidadeChange={handleOportunidadeChange}
          onSubmit={handleSubmit}
          isEdit={false}
          loadingOportunidades={loadingOportunidades}
          onSalvarComoPadrao={handleSalvarComoPadrao}
          salvandoPadrao={salvandoPadrao}
          showCancel={true}
          onCancel={() => router.push(`/loja/${slug}/crm-vendas/propostas`)}
          fullWidth
          templates={templates}
          onSelecionarTemplate={(conteudo) => setFormData((f) => ({ ...f, conteudo }))}
          vendedorNome={vendedorNome}
        />
      </div>
    </div>
  );
}
