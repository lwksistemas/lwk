'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail, normalizeListResponse } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import { logger } from '@/lib/logger';
import {
  downloadBlobPdf,
  parseBlobErrorDetail,
  type CrmRelatorioDashboardData,
  type CrmRelatorioEmpresaPrestadora,
  type CrmRelatorioVendedor,
} from '@/lib/crm-relatorios';

export function useCrmRelatoriosPage() {
  const toast = useToast();
  const [periodo, setPeriodo] = useState('mes_atual');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [tipoRelatorio, setTipoRelatorio] = useState('vendas_total');
  const [vendedorSelecionado, setVendedorSelecionado] = useState('todos');
  const [empresaPrestadoraSelecionada, setEmpresaPrestadoraSelecionada] = useState('todas');
  const [gerando, setGerando] = useState(false);
  const [vendedores, setVendedores] = useState<CrmRelatorioVendedor[]>([]);
  const [empresasPrestadoras, setEmpresasPrestadoras] = useState<CrmRelatorioEmpresaPrestadora[]>([]);
  const [dashboardData, setDashboardData] = useState<CrmRelatorioDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isVendedor, setIsVendedor] = useState(false);
  const [meuVendedorId, setMeuVendedorId] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const resMe = await apiClient.get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/');
        const isVend = !!resMe.data?.is_vendedor;
        setIsVendedor(isVend);
        setMeuVendedorId(resMe.data?.vendedor_id ?? null);
        try {
          const resV = await apiClient.get<CrmRelatorioVendedor[] | { results: CrmRelatorioVendedor[] }>(
            '/crm-vendas/vendedores/',
          );
          setVendedores(normalizeListResponse(resV.data));
        } catch {
          setVendedores([]);
        }
        try {
          const resEP = await apiClient.get<
            CrmRelatorioEmpresaPrestadora[] | { results: CrmRelatorioEmpresaPrestadora[] }
          >('/crm-vendas/contas/?tipo=prestadora');
          setEmpresasPrestadoras(normalizeListResponse(resEP.data));
        } catch {
          setEmpresasPrestadoras([]);
        }
        const resD = await apiClient.get<CrmRelatorioDashboardData>('/crm-vendas/dashboard/');
        setDashboardData(resD.data);
      } catch (err) {
        logger.warn('Erro ao carregar dados:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (isVendedor && tipoRelatorio === 'vendas_total') {
      setTipoRelatorio('vendas_vendedor');
    }
  }, [isVendedor, tipoRelatorio]);

  const handleGerar = useCallback(
    async (acao: 'pdf' | 'email') => {
      setGerando(true);
      try {
        const vendedorIdPayload = isVendedor
          ? meuVendedorId
          : vendedorSelecionado !== 'todos'
            ? vendedorSelecionado
            : null;
        const empresaPrestadoraPayload =
          empresaPrestadoraSelecionada !== 'todas' ? parseInt(empresaPrestadoraSelecionada, 10) : null;
        const payload: Record<string, unknown> = {
          tipo: tipoRelatorio,
          periodo,
          vendedor_id: vendedorIdPayload,
          empresa_prestadora_id: empresaPrestadoraPayload,
          acao,
        };
        if (periodo === 'personalizado') {
          if (!dataInicio || !dataFim) {
            toast.warning('Informe a data de início e fim para o período personalizado.');
            return;
          }
          payload.data_inicio = dataInicio;
          payload.data_fim = dataFim;
        }

        if (acao === 'pdf') {
          const res = await apiClient.post('/crm-vendas/relatorios/gerar/', payload, { responseType: 'blob' });
          downloadBlobPdf(new Blob([res.data]), `relatorio_${tipoRelatorio}_${periodo}.pdf`);
          toast.success('PDF gerado com sucesso!');
        } else {
          const res = await apiClient.post<{ message?: string }>('/crm-vendas/relatorios/gerar/', payload);
          toast.success(res.data.message || 'Relatório enviado por email!');
        }
      } catch (error: unknown) {
        const err = error as { response?: { data?: unknown } };
        const msg = await parseBlobErrorDetail(
          err.response?.data,
          getCrmApiErrorDetail(error, 'Erro ao gerar relatório.'),
        );
        toast.error(msg);
      } finally {
        setGerando(false);
      }
    },
    [
      isVendedor,
      meuVendedorId,
      vendedorSelecionado,
      empresaPrestadoraSelecionada,
      tipoRelatorio,
      periodo,
      dataInicio,
      dataFim,
      toast,
    ],
  );

  return {
    periodo,
    setPeriodo,
    dataInicio,
    setDataInicio,
    dataFim,
    setDataFim,
    tipoRelatorio,
    setTipoRelatorio,
    vendedorSelecionado,
    setVendedorSelecionado,
    empresaPrestadoraSelecionada,
    setEmpresaPrestadoraSelecionada,
    gerando,
    vendedores,
    empresasPrestadoras,
    dashboardData,
    loading,
    isVendedor,
    handleGerar,
  };
}
