'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import {
  getCrmApiErrorDetail,
  fetchCrmOportunidade,
  formatOportunidadeVinculoLabel,
  normalizeListResponse,
} from '@/lib/crm-utils';
import {
  deveConfirmarReenvioAssinatura,
  executarReenvioAssinatura,
  mensagemErroReenvioAssinatura,
  textoConfirmacaoReenvioAssinatura,
} from '@/lib/crm-reenviar-assinatura';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { CRM_PROPOSTA_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import { useToast } from '@/components/ui/Toast';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import CrmConfirmActionModal from '@/components/crm-vendas/CrmConfirmActionModal';
import PropostaFormContent from '@/components/crm-vendas/PropostaFormContent';
import type {
  FormDataProposta,
  CrmOportunidadeItem,
  CrmPropostaTemplate,
} from '@/lib/crm-proposta-form-types';
import { EMPTY_FORM_PROPOSTA } from '@/lib/crm-proposta-form-types';
import { emitenteFieldsFromApi, emitentePayloadFromForm } from '@/lib/crm-emitente-loja';

interface Proposta {
  id: number;
  oportunidade: number;
  oportunidade_titulo?: string;
  lead_nome?: string;
  conta_nome?: string;
  titulo: string;
  conteudo: string;
  valor_total: string | null;
  desconto_tipo: 'percentual' | 'valor';
  desconto_valor: string;
  status: string;
  status_assinatura?: string;
  emitente_nome?: string;
  emitente_endereco?: string;
  emitente_cpf_cnpj?: string;
  emitente_responsavel?: string;
  emitente_email?: string;
}

export default function EditarPropostaPage() {
  const toast = useToast();
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const id = parseInt(String(params?.id ?? ''), 10);
  const listPath = `/loja/${slug}/crm-vendas/propostas`;

  const [formData, setFormData] = useState<FormDataProposta>({ ...EMPTY_FORM_PROPOSTA });
  const [statusAssinaturaAntes, setStatusAssinaturaAntes] = useState<string | undefined>();
  const [oportunidadeTituloInicial, setOportunidadeTituloInicial] = useState('');
  const [itensOportunidade, setItensOportunidade] = useState<CrmOportunidadeItem[]>([]);
  const [templates, setTemplates] = useState<CrmPropostaTemplate[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [salvandoPadrao, setSalvandoPadrao] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reenvioPendente, setReenvioPendente] = useState(false);
  const [reenviando, setReenviando] = useState(false);

  const { lojaInfo, loadLojaInfo } = useCrmLojaInfoPublica(slug);
  const { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo } = useCrmLeadEVendedorForm(
    formData,
    setFormData,
  );

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

  useEffect(() => {
    if (isNaN(id)) {
      router.replace(listPath);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [propostaRes] = await Promise.all([
          apiClient.get<Proposta>(`/crm-vendas/propostas/${id}/`),
          loadTemplates(),
          loadLojaInfo(),
          loadVendedorInfo(),
        ]);
        if (cancelled) return;
        const p = propostaRes.data;
        setStatusAssinaturaAntes(p.status_assinatura);
        setOportunidadeTituloInicial(
          formatOportunidadeVinculoLabel({
            titulo: p.oportunidade_titulo,
            lead_nome: p.lead_nome,
            valor: p.valor_total,
            conta_nome: p.conta_nome,
          }),
        );
        setFormData({
          oportunidade_id: String(p.oportunidade),
          titulo: p.titulo || '',
          conteudo: p.conteudo || '',
          valor_total: p.valor_total || '',
          desconto_tipo: p.desconto_tipo || 'percentual',
          desconto_valor: String(p.desconto_valor ?? ''),
          status: p.status || 'rascunho',
          nome_vendedor_assinatura: '',
          nome_cliente_assinatura: '',
          ...emitenteFieldsFromApi(p),
        });
        setLoading(false);

        const oppId = String(p.oportunidade);
        void loadItensOportunidade(oppId);
        void fetchCrmOportunidade(oppId)
          .then((opp) => {
            if (cancelled) return;
            setOportunidadeTituloInicial(
              formatOportunidadeVinculoLabel({
                titulo: opp.titulo,
                lead_nome: opp.lead_nome,
                valor: opp.valor,
                conta_nome: opp.conta_nome,
                empresa_prestadora_nome: opp.empresa_prestadora_nome,
              }),
            );
            if (opp.lead) loadLeadInfo(opp.lead);
            else setLeadInfo(null);
          })
          .catch(() => {
            if (!cancelled) setLeadInfo(null);
          });
      } catch {
        if (!cancelled) router.replace(listPath);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, listPath, loadItensOportunidade, loadLeadInfo, loadLojaInfo, loadTemplates, loadVendedorInfo, router, setLeadInfo]);

  const handleOportunidadeChange = useCallback(
    async (oppId: string) => {
      setFormData((f) => ({ ...f, oportunidade_id: oppId }));
      if (!oppId) {
        setItensOportunidade([]);
        setLeadInfo(null);
        setOportunidadeTituloInicial('');
        return;
      }
      loadItensOportunidade(oppId);
      try {
        const opp = await fetchCrmOportunidade(oppId);
        setOportunidadeTituloInicial(
          formatOportunidadeVinculoLabel({
            titulo: opp.titulo,
            lead_nome: opp.lead_nome,
            valor: opp.valor,
            conta_nome: opp.conta_nome,
            empresa_prestadora_nome: opp.empresa_prestadora_nome,
          }),
        );
        setFormData((f) => ({
          ...f,
          oportunidade_id: oppId,
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

  const handleSalvarComoPadrao = useCallback(
    async (conteudo: string) => {
      try {
        setSalvandoPadrao(true);
        await apiClient.patch('/crm-vendas/config/', { proposta_conteudo_padrao: conteudo });
        toast.success('Proposta padrão salva. O conteúdo será usado em novas propostas.');
      } catch (err: unknown) {
        toast.error(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
      } finally {
        setSalvandoPadrao(false);
      }
    },
    [toast],
  );

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
      await apiClient.put(`/crm-vendas/propostas/${id}/`, {
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
      if (deveConfirmarReenvioAssinatura(statusAssinaturaAntes)) {
        setReenvioPendente(true);
        return;
      }
      router.push(listPath);
    } catch (err: unknown) {
      setFormErro(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-1 items-center justify-center min-h-[calc(100dvh-3.5rem)] bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      </div>
    );
  }

  return (
    <>
    <CrmFormPageShell
      error={formErro}
      saving={submitting}
      saveLabel="Salvar alterações"
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
        isEdit
        oportunidadeTituloInicial={oportunidadeTituloInicial}
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

    <CrmConfirmActionModal
      open={reenvioPendente}
      title="Reenviar assinatura digital?"
      message={textoConfirmacaoReenvioAssinatura('proposta', statusAssinaturaAntes)}
      confirmLabel="Reenviar e-mail"
      variant="primary"
      loading={reenviando}
      onClose={() => {
        if (reenviando) return;
        setReenvioPendente(false);
        router.push(listPath);
      }}
      onConfirm={async () => {
        setReenviando(true);
        try {
          const msg = await executarReenvioAssinatura('proposta', id);
          toast.success(msg);
          setReenvioPendente(false);
          router.push(listPath);
        } catch (err: unknown) {
          toast.error(mensagemErroReenvioAssinatura(err));
        } finally {
          setReenviando(false);
        }
      }}
    />
    </>
  );
}
