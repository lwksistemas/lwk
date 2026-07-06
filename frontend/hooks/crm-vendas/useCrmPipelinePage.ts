'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { fetchAllPaginatedResults, getCrmApiErrorDetail, normalizeListResponse } from '@/lib/crm-utils';
import {
  dataReferenciaOportunidade,
  filtrarOportunidadesPipeline,
  loadOportunidades,
} from '@/lib/crm-pipeline';
import { useToast } from '@/components/ui/Toast';
import {
  CRM_PIPELINE_PERIODO_PADRAO,
  crmDatasPeriodo,
} from '@/lib/crm-periodos';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';

export function useCrmPipelinePage() {
  const toast = useToast();
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const verParam = searchParams.get('ver');

  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [vendedorIdSynced, setVendedorIdSynced] = useState(false);
  const [oportunidadeEditar, setOportunidadeEditar] = useState<Oportunidade | null>(null);
  const [modalCriar, setModalCriar] = useState(false);
  const [initialLeadId, setInitialLeadId] = useState<string | undefined>(undefined);
  const [viewPipeline, setViewPipeline] = useState<'board' | 'list'>('board');
  const [filtroEtapaPipeline, setFiltroEtapaPipeline] = useState('');
  const [filtroVendedor, setFiltroVendedor] = useState('');
  const [vendedores, setVendedores] = useState<{ id: number; nome: string }[]>([]);
  const periodoInicial = crmDatasPeriodo(CRM_PIPELINE_PERIODO_PADRAO);
  const [periodoPipeline, setPeriodoPipeline] = useState(CRM_PIPELINE_PERIODO_PADRAO);
  const [dataInicio, setDataInicio] = useState(periodoInicial?.dataInicio ?? '');
  const [dataFim, setDataFim] = useState(periodoInicial?.dataFim ?? '');
  const [imprimindo, setImprimindo] = useState(false);

  useEffect(() => {
    apiClient
      .get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/')
      .then((res) => {
        const { vendedor_id, is_vendedor } = res.data;
        if (vendedor_id && is_vendedor === true) {
          authService.setVendedorId(vendedor_id);
        } else if (vendedor_id) {
          if (typeof window !== 'undefined') {
            sessionStorage.setItem('current_vendedor_id', String(vendedor_id));
          }
        }
        setVendedorIdSynced(true);
      })
      .catch(() => {
        setVendedorIdSynced(true);
      });
  }, []);

  useEffect(() => {
    if (!vendedorIdSynced) return;
    setLoading(true);
    setError(null);
    let cancelled = false;
    fetchAllPaginatedResults<Oportunidade>('/crm-vendas/oportunidades/')
      .then((items) => {
        if (cancelled) return;
        setOportunidades(items);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(getCrmApiErrorDetail(err, 'Erro ao carregar oportunidades.'));
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [vendedorIdSynced, slug]);

  useEffect(() => {
    apiClient
      .get<{ id: number; nome: string }[] | { results: { id: number; nome: string }[] }>('/crm-vendas/vendedores/')
      .then((res) => setVendedores(normalizeListResponse(res.data)))
      .catch(() => setVendedores([]));
  }, []);

  useEffect(() => {
    if (!verParam) return;
    const id = parseInt(verParam, 10);
    if (isNaN(id)) return;

    const abrirOportunidade = (op: Oportunidade) => {
      const dataRef = dataReferenciaOportunidade(op);
      if (dataRef) {
        setDataInicio((ini) => (!ini || dataRef < ini ? dataRef : ini));
        setDataFim((fim) => (!fim || dataRef > fim ? dataRef : fim));
      }
      setOportunidadeEditar(op);
      router.replace(`/loja/${slug}/crm-vendas/pipeline`, { scroll: false });
    };

    const found = oportunidades.find((o) => o.id === id);
    if (found) {
      abrirOportunidade(found);
      return;
    }
    if (!loading) {
      apiClient
        .get<Oportunidade>(`/crm-vendas/oportunidades/${id}/`)
        .then((res) => abrirOportunidade(res.data))
        .catch(() => {});
    }
  }, [verParam, oportunidades, loading, router, slug]);

  useEffect(() => {
    const leadIdParam = searchParams.get('lead_id');
    if (searchParams.get('novo') === '1') {
      const url = leadIdParam
        ? `/loja/${slug}/crm-vendas/pipeline/nova-oportunidade?lead_id=${leadIdParam}`
        : `/loja/${slug}/crm-vendas/pipeline/nova-oportunidade`;
      router.replace(url);
    }
  }, [searchParams, router, slug]);

  const handleAbrirCriar = () => {
    router.push(`/loja/${slug}/crm-vendas/pipeline/nova-oportunidade`);
  };

  const handleCardClick = (op: Oportunidade) => {
    setOportunidadeEditar(op);
  };

  const handleExportarPDF = () => {
    setImprimindo(true);
    setTimeout(() => {
      window.print();
      setImprimindo(false);
    }, 100);
  };

  const handleModalSuccess = () => {
    loadOportunidades(setOportunidades, setError);
  };

  const selecionarPeriodoPipeline = (periodo: string) => {
    setPeriodoPipeline(periodo);
    if (periodo === 'todos') {
      setDataInicio('');
      setDataFim('');
      return;
    }
    if (periodo === 'personalizado') return;
    const range = crmDatasPeriodo(periodo);
    if (range) {
      setDataInicio(range.dataInicio);
      setDataFim(range.dataFim);
    }
  };

  const alterarDataInicio = (value: string) => {
    setDataInicio(value);
    setPeriodoPipeline('personalizado');
  };

  const alterarDataFim = (value: string) => {
    setDataFim(value);
    setPeriodoPipeline('personalizado');
  };

  const limparPeriodoPipeline = () => {
    selecionarPeriodoPipeline(CRM_PIPELINE_PERIODO_PADRAO);
  };

  const handleEtapaChange = async (opp: Oportunidade, novaEtapa: string) => {
    if (opp.etapa === novaEtapa) return;
    try {
      await apiClient.patch(`/crm-vendas/oportunidades/${opp.id}/`, { etapa: novaEtapa });
      setOportunidades((prev) =>
        prev.map((o) => (o.id === opp.id ? { ...o, etapa: novaEtapa } : o)),
      );
      toast.success('Etapa atualizada.');
    } catch (err) {
      toast.error(getCrmApiErrorDetail(err, 'Não foi possível mover a oportunidade.'));
    }
  };

  const oportunidadesBase = useMemo(
    () =>
      filtrarOportunidadesPipeline(oportunidades, {
        vendedor: filtroVendedor,
        dataInicio,
        dataFim,
      }),
    [oportunidades, filtroVendedor, dataInicio, dataFim],
  );

  const oportunidadesFiltradas = useMemo(
    () =>
      filtrarOportunidadesPipeline(oportunidades, {
        etapa: filtroEtapaPipeline || undefined,
        vendedor: filtroVendedor,
        dataInicio,
        dataFim,
      }),
    [oportunidades, filtroEtapaPipeline, filtroVendedor, dataInicio, dataFim],
  );

  return {
    slug,
    oportunidades,
    loading,
    error,
    oportunidadeEditar,
    setOportunidadeEditar,
    modalCriar,
    setModalCriar,
    initialLeadId,
    viewPipeline,
    setViewPipeline,
    filtroEtapaPipeline,
    setFiltroEtapaPipeline,
    filtroVendedor,
    setFiltroVendedor,
    vendedores,
    periodoPipeline,
    selecionarPeriodoPipeline,
    dataInicio,
    setDataInicio: alterarDataInicio,
    dataFim,
    setDataFim: alterarDataFim,
    limparPeriodoPipeline,
    imprimindo,
    oportunidadesBase,
    oportunidadesFiltradas,
    handleAbrirCriar,
    handleCardClick,
    handleExportarPDF,
    handleModalSuccess,
    handleEtapaChange,
  };
}
