'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import { parseBlobErrorDetail, type CrmRelatorioComissao } from '@/lib/crm-relatorios';

export type ComissaoConfirmAction =
  | { type: 'excluir'; id: number; numero: string }
  | { type: 'pagamento'; id: number; numero: string }
  | { type: 'reemitir'; id: number; numero: string };

const CONFIRM_COPY: Record<
  ComissaoConfirmAction['type'],
  { title: string; message: (numero: string) => string; confirmLabel: string; variant: 'danger' | 'primary' }
> = {
  excluir: {
    title: 'Excluir relatório',
    message: (numero) => `Deseja excluir o relatório ${numero}?`,
    confirmLabel: 'Excluir',
    variant: 'danger',
  },
  pagamento: {
    title: 'Confirmar pagamento',
    message: (numero) =>
      `Confirmar pagamento do relatório ${numero}? Isso vai emitir a NFS-e automaticamente.`,
    confirmLabel: 'Confirmar pagamento',
    variant: 'primary',
  },
  reemitir: {
    title: 'Reemitir NFS-e',
    message: (numero) => `Reemitir NFS-e para o relatório ${numero}?`,
    confirmLabel: 'Reemitir NFS-e',
    variant: 'primary',
  },
};

export function useCrmRelatoriosComissao(isVendedor: boolean) {
  const toast = useToast();
  const [relatorios, setRelatorios] = useState<CrmRelatorioComissao[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [criando, setCriando] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ComissaoConfirmAction | null>(null);
  const [confirmando, setConfirmando] = useState(false);

  const [formEmpresa, setFormEmpresa] = useState('');
  const [formVendedor, setFormVendedor] = useState('');
  const [formPeriodo, setFormPeriodo] = useState('mes_atual');
  const [formDataInicio, setFormDataInicio] = useState('');
  const [formDataFim, setFormDataFim] = useState('');
  const [formObs, setFormObs] = useState('');

  const loadRelatorios = useCallback(async () => {
    try {
      setLoading(true);
      const { data } = await apiClient.get<{ relatorios?: CrmRelatorioComissao[] }>(
        '/crm-vendas/relatorios-comissao/',
      );
      setRelatorios(data.relatorios || []);
    } catch {
      setRelatorios([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRelatorios();
  }, [loadRelatorios]);

  const buildPayload = useCallback(() => {
    const payload: Record<string, unknown> = {
      empresa_prestadora_id: parseInt(formEmpresa, 10),
      periodo: formPeriodo,
      observacoes: formObs,
    };
    if (formVendedor) payload.vendedor_id = parseInt(formVendedor, 10);
    if (formPeriodo === 'personalizado') {
      payload.data_inicio = formDataInicio;
      payload.data_fim = formDataFim;
    }
    return payload;
  }, [formEmpresa, formVendedor, formPeriodo, formDataInicio, formDataFim, formObs]);

  const validateForm = useCallback(() => {
    if (!formEmpresa) {
      toast.warning('Selecione a empresa prestadora.');
      return false;
    }
    if (formPeriodo === 'personalizado' && (!formDataInicio || !formDataFim)) {
      toast.warning('Informe as datas do período personalizado.');
      return false;
    }
    return true;
  }, [formEmpresa, formPeriodo, formDataInicio, formDataFim, toast]);

  const resetForm = useCallback(() => {
    setShowForm(false);
  }, []);

  const handlePreview = async () => {
    if (!validateForm()) return;
    setCriando(true);
    try {
      const res = await apiClient.post('/crm-vendas/relatorios-comissao/preview/', buildPayload(), {
        responseType: 'blob',
      });
      const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => window.URL.revokeObjectURL(url), 10000);
      toast.success('PDF aberto em nova aba. Revise e confirme o envio abaixo.');
    } catch (err: unknown) {
      const e = err as { response?: { data?: unknown } };
      const msg = await parseBlobErrorDetail(
        e.response?.data,
        getCrmApiErrorDetail(err, 'Erro ao gerar preview.'),
      );
      toast.error(msg);
    } finally {
      setCriando(false);
    }
  };

  const handleCriarEEnviar = async () => {
    if (!validateForm()) return;
    setCriando(true);
    try {
      const { data } = await apiClient.post<{ success?: boolean; message?: string; detail?: string }>(
        '/crm-vendas/relatorios-comissao/criar/',
        buildPayload(),
      );
      if (data.success) {
        toast.success(data.message || 'Relatório criado e enviado para aprovação.');
        resetForm();
        loadRelatorios();
      } else {
        toast.error(data.detail || 'Erro ao criar relatório.');
      }
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao criar relatório.'));
    } finally {
      setCriando(false);
    }
  };

  const handleDownloadPdf = async (id: number) => {
    try {
      const res = await apiClient.get(`/crm-vendas/relatorios-comissao/${id}/pdf/`, { responseType: 'blob' });
      const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => window.URL.revokeObjectURL(url), 10000);
    } catch {
      toast.error('Erro ao baixar PDF.');
    }
  };

  const executeConfirm = async () => {
    if (!confirmAction) return;
    setConfirmando(true);
    try {
      const { type, id } = confirmAction;
      if (type === 'excluir') {
        const { data } = await apiClient.delete<{ success?: boolean; message?: string; detail?: string }>(
          `/crm-vendas/relatorios-comissao/${id}/excluir/`,
        );
        if (data.success) {
          toast.success(data.message || 'Relatório excluído.');
          loadRelatorios();
        } else {
          toast.error(data.detail || 'Erro ao excluir.');
        }
      } else if (type === 'pagamento') {
        const { data } = await apiClient.post<{ success?: boolean; message?: string; detail?: string }>(
          `/crm-vendas/relatorios-comissao/${id}/confirmar-pagamento/`,
        );
        if (data.success) {
          toast.success(data.message || 'Pagamento confirmado.');
          loadRelatorios();
        } else {
          toast.error(data.detail || 'Erro ao confirmar pagamento.');
        }
      } else {
        const { data } = await apiClient.post<{ success?: boolean; message?: string; detail?: string }>(
          `/crm-vendas/relatorios-comissao/${id}/reemitir-nfse/`,
        );
        if (data.success) {
          toast.success(data.message || 'NFS-e reemitida.');
          loadRelatorios();
        } else {
          toast.error(data.detail || 'Erro ao emitir NFS-e.');
        }
      }
      setConfirmAction(null);
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao processar ação.'));
    } finally {
      setConfirmando(false);
    }
  };

  const confirmCopy = confirmAction ? CONFIRM_COPY[confirmAction.type] : null;

  return {
    relatorios,
    loading,
    showForm,
    setShowForm,
    criando,
    confirmAction,
    setConfirmAction,
    confirmando,
    confirmCopy,
    executeConfirm,
    formEmpresa,
    setFormEmpresa,
    formVendedor,
    setFormVendedor,
    formPeriodo,
    setFormPeriodo,
    formDataInicio,
    setFormDataInicio,
    formDataFim,
    setFormDataFim,
    formObs,
    setFormObs,
    loadRelatorios,
    handlePreview,
    handleCriarEEnviar,
    handleDownloadPdf,
    resetForm,
    canCreate: !isVendedor,
  };
}
