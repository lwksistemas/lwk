'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail, gerarTituloProposta, fetchCrmOportunidade } from '@/lib/crm-utils';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import { useToast } from '@/components/ui/Toast';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import PropostaFormContent from '@/components/crm-vendas/PropostaFormContent';
import type {
  FormDataProposta,
  CrmOportunidadeItem,
  CrmPropostaTemplate,
} from '@/lib/crm-proposta-form-types';
import { EMPTY_FORM_PROPOSTA } from '@/lib/crm-proposta-form-types';
import { emitentePayloadFromForm } from '@/lib/crm-emitente-loja';
import { conteudoComDescricoes } from '@/lib/crm-proposta-conteudo';
import { avisoTemplatesDaPrestadora, carregarTemplatesDaPrestadora } from '@/lib/crm-proposta-templates';

export default function NovaPropostaPage() {
  const toast = useToast();
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const listPath = `/loja/${slug}/crm-vendas/propostas`;

  const [formData, setFormData] = useState<FormDataProposta>({ ...EMPTY_FORM_PROPOSTA });
  const [itensOportunidade, setItensOportunidade] = useState<CrmOportunidadeItem[]>([]);
  const [marcaPrestadora, setMarcaPrestadora] = useState('');
  const [prestadoraId, setPrestadoraId] = useState<number | null>(null);
  const [templates, setTemplates] = useState<CrmPropostaTemplate[]>([]);
  const templateAplicado = useRef('');
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
      const itens = normalizeListResponse(res.data);
      setItensOportunidade(itens);
      setFormData((f) => ({ ...f, conteudo: conteudoComDescricoes(f.conteudo, itens) }));
    } catch {
      setItensOportunidade([]);
    }
  }, []);

  useEffect(() => {
    loadLojaInfo();
    loadVendedorInfo();
  }, [loadLojaInfo, loadVendedorInfo]);

  const handleOportunidadeChange = useCallback(
    async (id: string) => {
      setFormData((f) => ({ ...f, oportunidade_id: id }));
      if (!id) {
        setItensOportunidade([]);
        setLeadInfo(null);
        setMarcaPrestadora('');
        setPrestadoraId(null);
        setTemplates([]);
        return;
      }
      try {
        const opp = await fetchCrmOportunidade(id);
        const idPrestadora = opp.empresa_prestadora ?? null;
        setMarcaPrestadora(opp.empresa_prestadora_nome || '');
        setPrestadoraId(idPrestadora);
        const lista = await carregarTemplatesDaPrestadora(idPrestadora);
        setTemplates(lista);
        const padrao = lista.find((t) => t.is_padrao);
        setFormData((f) => {
          const nomeVendedor = (opp.vendedor_nome || '').trim();
          const podeTrocar = !f.conteudo.trim() || f.conteudo === templateAplicado.current;
          const conteudo = podeTrocar ? (padrao?.conteudo || '') : f.conteudo;
          if (podeTrocar) templateAplicado.current = conteudo;
          return {
            ...f,
            oportunidade_id: id,
            conteudo,
            valor_total: opp.valor ? String(opp.valor) : f.valor_total,
            nome_vendedor_assinatura: nomeVendedor || f.nome_vendedor_assinatura,
          };
        });
        await loadItensOportunidade(id);
        if (opp.lead) {
          loadLeadInfo(opp.lead);
        } else {
          setLeadInfo(null);
        }
      } catch {
        setLeadInfo(null);
        setTemplates([]);
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
  }, [leadInfo]);

  const handleSalvarComoPadrao = useCallback(async (conteudo: string) => {
    try {
      setSalvandoPadrao(true);
      await apiClient.patch('/crm-vendas/config/', { proposta_conteudo_padrao: conteudo });
      toast.success('Proposta padrão salva.');
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
    } finally {
      setSalvandoPadrao(false);
    }
  }, [toast]);

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
    if (formData.emitente_personalizado && !formData.emitente_nome.trim()) {
      setFormErro('Informe o nome do emitente personalizado');
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
        ...emitentePayloadFromForm(formData),
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
        marcaPrestadora={marcaPrestadora}
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
        templateAusente={avisoTemplatesDaPrestadora({
          temOportunidade: Boolean(formData.oportunidade_id),
          prestadoraId,
          prestadoraNome: marcaPrestadora,
          quantidade: templates.length,
        })}
        onSelecionarTemplate={(conteudo) => {
          templateAplicado.current = conteudo;
          setFormData((f) => ({
            ...f,
            conteudo: conteudoComDescricoes(conteudo, itensOportunidade),
          }));
        }}
        vendedorNome={vendedorNome}
      />

      <p className="mt-6 pt-4 border-t border-gray-100 dark:border-[#0d1f3c] text-xs text-gray-500 dark:text-gray-400 text-center">
        Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de
        data, hora e endereço IP.
      </p>
    </CrmFormPageShell>
  );
}
