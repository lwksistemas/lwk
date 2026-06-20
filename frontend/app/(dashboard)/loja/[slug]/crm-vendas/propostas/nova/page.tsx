'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail, gerarTituloProposta, fetchCrmOportunidade } from '@/lib/crm-utils';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import PropostaFormContent from '@/components/crm-vendas/PropostaFormContent';
import type { FormDataProposta } from '@/components/crm-vendas/modals/ModalPropostaForm';
import type {
  CrmOportunidadeItem,
  CrmPropostaTemplate,
} from '@/lib/crm-proposta-form-types';

export default function NovaPropostaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const listPath = `/loja/${slug}/crm-vendas/propostas`;

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
    loadLojaInfo();
    loadCrmConfig();
    loadTemplates();
    loadVendedorInfo();
  }, [loadLojaInfo, loadCrmConfig, loadTemplates, loadVendedorInfo]);

  useEffect(() => {
    if (!formData.conteudo) {
      const templatePadrao = templates.find((t) => t.is_padrao);
      const conteudoInicial = templatePadrao?.conteudo || propostaConteudoPadrao;
      if (conteudoInicial) {
        setFormData((f) => ({ ...f, conteudo: conteudoInicial }));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- formData.conteudo omitido de propósito
  }, [templates, propostaConteudoPadrao]);

  const handleOportunidadeChange = useCallback(
    async (id: string) => {
      setFormData((f) => ({ ...f, oportunidade_id: id }));
      if (!id) {
        setItensOportunidade([]);
        setLeadInfo(null);
        return;
      }
      loadItensOportunidade(id);
      try {
        const opp = await fetchCrmOportunidade(id);
        setFormData((f) => ({
          ...f,
          oportunidade_id: id,
          valor_total: opp.valor ? String(opp.valor) : f.valor_total,
        }));
        if (opp.lead) {
          loadLeadInfo(opp.lead);
        } else {
          setLeadInfo(null);
        }
      } catch {
        setLeadInfo(null);
      }
    },
    [loadItensOportunidade, loadLeadInfo, setLeadInfo],
  );

  useEffect(() => {
    if (!leadInfo) return;
    const tituloGerado = gerarTituloProposta(leadInfo);
    if (tituloGerado) {
      setFormData((f) => ({ ...f, titulo: tituloGerado }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leadInfo]);

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

  const handleSave = async () => {
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
      router.push(listPath);
    } catch (err: unknown) {
      setFormErro(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <CrmFormPageShell
      error={formErro}
      saving={submitting}
      saveLabel="Criar proposta"
      savingLabel="Salvando..."
      onSave={handleSave}
      onCancel={() => router.push(listPath)}
    >
      <PropostaFormContent
        form={formData}
        formErro={formErro}
        enviando={submitting}
        lojaInfo={lojaInfo}
        leadInfo={leadInfo}
        itensOportunidade={itensOportunidade}
        statusOpcoes={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))}
        onFormChange={setFormData}
        onOportunidadeChange={handleOportunidadeChange}
        onSubmit={(e) => {
          e.preventDefault();
          void handleSave();
        }}
        isEdit={false}
        onSalvarComoPadrao={handleSalvarComoPadrao}
        salvandoPadrao={salvandoPadrao}
        pageLayout
        hideError
        hideActions
        templates={templates}
        onSelecionarTemplate={(conteudo) => setFormData((f) => ({ ...f, conteudo }))}
        vendedorNome={vendedorNome}
      />

      <p className="mt-6 pt-4 border-t border-gray-100 dark:border-[#0d1f3c] text-xs text-gray-500 dark:text-gray-400 text-center">
        Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de
        data, hora e endereço IP.
      </p>
    </CrmFormPageShell>
  );
}
