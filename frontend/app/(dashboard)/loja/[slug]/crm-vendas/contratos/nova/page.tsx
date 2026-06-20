'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useCrmLojaInfoPublica } from '@/hooks/useCrmLojaInfoPublica';
import { useCrmLeadEVendedorForm } from '@/hooks/useCrmLeadEVendedorForm';
import { CRM_CONTRATO_STATUS_LABEL as STATUS_LABEL } from '@/lib/crm-constants';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import ContratoFormContent, { type OportunidadeContratoOption } from '@/components/crm-vendas/ContratoFormContent';
import type { FormDataContrato } from '@/components/crm-vendas/modals/ModalContratoForm';

const EMPTY_FORM: FormDataContrato = {
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
};

export default function NovoContratoPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const listPath = `/loja/${slug}/crm-vendas/contratos`;

  const [formData, setFormData] = useState<FormDataContrato>(EMPTY_FORM);
  const [oportunidades, setOportunidades] = useState<OportunidadeContratoOption[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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
    Promise.all([loadLojaInfo(), loadOportunidades(), loadVendedorInfo()]).finally(() => setLoading(false));
  }, [loadLojaInfo, loadOportunidades, loadVendedorInfo]);

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
    try {
      setSubmitting(true);
      await apiClient.post('/crm-vendas/contratos/', {
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
      });
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
    <CrmFormPageShell
      error={formErro}
      saving={submitting}
      saveLabel="Criar contrato"
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
        pageLayout
        hideActions
        vendedorNome={vendedorNome}
      />

      <p className="mt-6 pt-4 border-t border-gray-100 dark:border-[#0d1f3c] text-xs text-gray-500 dark:text-gray-400 text-center">
        Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de
        data, hora e endereço IP.
      </p>
    </CrmFormPageShell>
  );
}
