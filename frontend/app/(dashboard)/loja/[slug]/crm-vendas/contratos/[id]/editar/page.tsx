'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail } from '@/lib/crm-utils';
import {
  deveConfirmarReenvioAssinatura,
  executarReenvioAssinatura,
  mensagemErroReenvioAssinatura,
  textoConfirmacaoReenvioAssinatura,
} from '@/lib/crm-reenviar-assinatura';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { CRM_CONTRATO_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import { useToast } from '@/components/ui/Toast';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import CrmConfirmActionModal from '@/components/crm-vendas/CrmConfirmActionModal';
import ContratoFormContent, { type OportunidadeContratoOption } from '@/components/crm-vendas/ContratoFormContent';
import type { FormDataContrato } from '@/components/crm-vendas/modals/ModalContratoForm';
import { EMPTY_FORM_CONTRATO } from '@/components/crm-vendas/modals/ModalContratoForm';
import { emitenteFieldsFromApi, emitentePayloadFromForm } from '@/lib/crm-emitente-loja';

interface Contrato {
  id: number;
  oportunidade: number;
  numero: string;
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

export default function EditarContratoPage() {
  const toast = useToast();
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const id = parseInt(String(params?.id ?? ''), 10);
  const listPath = `/loja/${slug}/crm-vendas/contratos`;

  const [formData, setFormData] = useState<FormDataContrato>(EMPTY_FORM_CONTRATO);
  const [statusAssinaturaAntes, setStatusAssinaturaAntes] = useState<string | undefined>();
  const [oportunidades, setOportunidades] = useState<OportunidadeContratoOption[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reenvioPendente, setReenvioPendente] = useState(false);
  const [reenviando, setReenviando] = useState(false);

  const { lojaInfo, loadLojaInfo } = useCrmLojaInfoPublica(slug);
  const { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo } = useCrmLeadEVendedorForm(
    formData,
    setFormData,
  );

  const loadOportunidades = useCallback(async () => {
    try {
      const res = await apiClient.get<OportunidadeContratoOption[] | { results: OportunidadeContratoOption[] }>(
        '/crm-vendas/oportunidades/?etapa=closed_won',
      );
      setOportunidades(normalizeListResponse(res.data));
    } catch {
      setOportunidades([]);
    }
  }, []);

  useEffect(() => {
    if (isNaN(id)) {
      router.replace(listPath);
      return;
    }
    let cancelled = false;
    Promise.all([
      apiClient.get<Contrato>(`/crm-vendas/contratos/${id}/`),
      loadOportunidades(),
      loadLojaInfo(),
      loadVendedorInfo(),
    ])
      .then(([contratoRes]) => {
        if (cancelled) return;
        const c = contratoRes.data;
        setStatusAssinaturaAntes(c.status_assinatura);
        setFormData({
          oportunidade_id: String(c.oportunidade),
          numero: c.numero || '',
          titulo: c.titulo || '',
          conteudo: c.conteudo || '',
          valor_total: c.valor_total || '',
          desconto_tipo: c.desconto_tipo || 'percentual',
          desconto_valor: String(c.desconto_valor || ''),
          status: c.status || 'rascunho',
          nome_vendedor_assinatura: '',
          nome_cliente_assinatura: '',
          ...emitenteFieldsFromApi(c),
        });
      })
      .catch(() => {
        if (!cancelled) router.replace(listPath);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id, listPath, loadLojaInfo, loadOportunidades, loadVendedorInfo, router]);

  useEffect(() => {
    if (!formData?.oportunidade_id || oportunidades.length === 0) return;
    const opp = oportunidades.find((o) => String(o.id) === formData.oportunidade_id);
    if (opp?.lead) {
      loadLeadInfo(opp.lead);
    } else {
      setLeadInfo(null);
    }
  }, [formData?.oportunidade_id, oportunidades, loadLeadInfo, setLeadInfo]);

  const handleOportunidadeChange = (oppId: string) => {
    const opp = oportunidades.find((o) => String(o.id) === oppId);
    setFormData((f) => ({
      ...f,
      oportunidade_id: oppId,
      valor_total: opp?.valor ? String(opp.valor) : f.valor_total,
    }));
    if (opp?.lead) {
      loadLeadInfo(opp.lead);
    } else {
      setLeadInfo(null);
    }
  };

  const handleSave = async () => {
    setFormErro(null);
    if (!formData.titulo.trim()) {
      setFormErro('Título é obrigatório');
      return;
    }
    if (!formData.oportunidade_id) {
      setFormErro('Selecione uma oportunidade fechada como ganha');
      return;
    }
    if (formData.emitente_personalizado && !formData.emitente_nome.trim()) {
      setFormErro('Informe o nome do emitente personalizado');
      return;
    }
    try {
      setSubmitting(true);
      await apiClient.put(`/crm-vendas/contratos/${id}/`, {
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
      <ContratoFormContent
        form={formData}
        enviando={submitting}
        lojaInfo={lojaInfo}
        leadInfo={leadInfo}
        oportunidades={oportunidades}
        statusOpcoes={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))}
        onFormChange={setFormData}
        onOportunidadeChange={handleOportunidadeChange}
        onSubmit={(e) => {
          e.preventDefault();
          void handleSave();
        }}
        isEdit
        pageLayout
        hideActions
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
      message={textoConfirmacaoReenvioAssinatura('contrato', statusAssinaturaAntes)}
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
          const msg = await executarReenvioAssinatura('contrato', id);
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
