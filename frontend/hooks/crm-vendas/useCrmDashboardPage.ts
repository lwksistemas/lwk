'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import {
  Calendar,
  Phone,
  FileText,
  Flag,
  type LucideIcon,
} from 'lucide-react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { normalizeListResponse } from '@/lib/crm-utils';
import { crmLabelsPeriodo, crmPeriodoAnteriorComparavel, calcularVariacaoPct } from '@/lib/crm-periodos';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

function toISO(date: Date): string {
  return date.toISOString().slice(0, 19) + 'Z';
}

export interface DashboardData {
  leads: number;
  oportunidades: number;
  receita: number;
  pipeline_aberto: number;
  oportunidades_em_andamento: number;
  valor_perdido?: number;
  taxa_conversao: number;
  pipeline_por_etapa: { etapa: string; valor: number; quantidade: number }[];
  atividades_hoje: unknown[];
  performance_vendedores: {
    id: number | null;
    nome: string;
    receita_mes: number;
    comissao_mes: number;
  }[];
  comissao_total_mes: number;
}

export interface ProximaAtividade {
  id: number;
  titulo: string;
  tipo: string;
  data: string;
  lead_nome?: string;
  concluido?: boolean;
}

const TIPO_LABEL_DASHBOARD: Record<string, string> = {
  call: 'Ligação',
  meeting: 'Reunião',
  email: 'E-mail',
  task: 'Tarefa',
};

export function iconPorTipoAtividade(tipo: string): LucideIcon {
  const t = (tipo || '').toLowerCase();
  if (t.includes('reunião') || t.includes('reuniao')) return Calendar;
  if (t.includes('ligar') || t.includes('call')) return Phone;
  if (t.includes('proposta') || t.includes('enviar')) return FileText;
  return Flag;
}

export function formatarDataAtividade(dataIso: string): { texto: string; atrasada: boolean } {
  try {
    const date = new Date(dataIso);
    const agora = new Date();
    const hoje = new Date();
    const amanha = new Date(hoje);
    amanha.setDate(amanha.getDate() + 1);
    const atrasada = date.getTime() < agora.getTime();
    const hora = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    if (atrasada) {
      const dia = date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
      return { texto: `Atrasada — ${dia} às ${hora}`, atrasada };
    }
    if (date.toDateString() === hoje.toDateString()) {
      return { texto: `Hoje às ${hora}`, atrasada: false };
    }
    if (date.toDateString() === amanha.toDateString()) {
      return { texto: `Amanhã às ${hora}`, atrasada: false };
    }
    const dia = date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    return { texto: `${dia} às ${hora}`, atrasada: false };
  } catch {
    return { texto: dataIso, atrasada: false };
  }
}

export function labelTipoAtividade(tipo: string): string {
  return TIPO_LABEL_DASHBOARD[tipo] || tipo;
}

export function tituloGraficoPeriodo(periodoFiltro: string): string {
  if (periodoFiltro === 'mes_atual') return 'Mês Atual';
  if (periodoFiltro === 'mes_passado') return 'Mês Passado';
  if (periodoFiltro === 'trimestre_atual') return 'Trimestre';
  return 'Ano';
}

export interface DashboardTrends {
  receita?: { trend?: 'up' | 'down'; trendValue?: string };
  taxaConversao?: { trend?: 'up' | 'down'; trendValue?: string };
}

export function useCrmDashboardPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const { etapasAtivas } = useCRMConfig();
  const isVendedor = authService.isVendedor();

  const [data, setData] = useState<DashboardData | null>(null);
  const [proximasAtividades, setProximasAtividades] = useState<ProximaAtividade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFiltro, setShowFiltro] = useState(false);
  const [periodoFiltro, setPeriodoFiltro] = useState('mes_atual');
  const [trends, setTrends] = useState<DashboardTrends>({});
  const filtroRef = useRef<HTMLDivElement>(null);

  const pipelineMap = useMemo(
    () =>
      new Map(
        (data?.pipeline_por_etapa || []).map((p) => [p.etapa, { valor: p.valor, quantidade: p.quantidade }]),
      ),
    [data?.pipeline_por_etapa],
  );

  const etapasComValor = useMemo(
    () =>
      etapasAtivas().map((e) => ({
        key: e.key,
        label: e.label,
        ...(pipelineMap.get(e.key) || { valor: 0, quantidade: 0 }),
      })),
    [etapasAtivas, pipelineMap],
  );

  const chartData = useMemo(
    () =>
      etapasComValor.map((p) => ({
        name: p.label,
        valor: p.valor,
        quantidade: p.quantidade,
      })),
    [etapasComValor],
  );

  const periodoLabels = useMemo(() => crmLabelsPeriodo(periodoFiltro), [periodoFiltro]);
  const chartTitle = useMemo(() => tituloGraficoPeriodo(periodoFiltro), [periodoFiltro]);

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (filtroRef.current && !filtroRef.current.contains(e.target as Node)) {
      setShowFiltro(false);
    }
  }, []);

  const toggleFiltro = useCallback(() => {
    setShowFiltro((v) => !v);
  }, []);

  const selecionarPeriodo = useCallback((periodo: string) => {
    setPeriodoFiltro(periodo);
    setShowFiltro(false);
  }, []);

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [handleClickOutside]);

  useEffect(() => {
    setLoading(true);
    const inicio = new Date();
    inicio.setHours(0, 0, 0, 0);
    const fim = new Date(inicio);
    fim.setDate(fim.getDate() + 60);

    const anterior = crmPeriodoAnteriorComparavel(periodoFiltro);
    const dashUrl = `/crm-vendas/dashboard/?periodo=${periodoFiltro}`;
    const anteriorUrl = anterior
      ? `/crm-vendas/dashboard/?periodo=${anterior.periodo}${
          anterior.data_inicio && anterior.data_fim
            ? `&data_inicio=${anterior.data_inicio}&data_fim=${anterior.data_fim}`
            : ''
        }`
      : null;

    Promise.allSettled([
      apiClient.get<DashboardData>(dashUrl),
      anteriorUrl ? apiClient.get<DashboardData>(anteriorUrl) : Promise.resolve(null),
      apiClient.get('/crm-vendas/atividades/', {
        params: {
          data_inicio: toISO(inicio),
          data_fim: toISO(fim),
          concluido: 'false',
          page_size: 10,
        },
      }),
    ])
      .then(([dashResult, anteriorResult, ativResult]) => {
        if (dashResult.status === 'rejected') {
          const err = dashResult.reason as { response?: { data?: { detail?: string } } };
          throw new Error(err.response?.data?.detail || 'Erro ao carregar dashboard.');
        }
        const dashData = dashResult.value.data;
        setData(dashData);

        if (
          anteriorResult &&
          anteriorResult.status === 'fulfilled' &&
          anteriorResult.value?.data
        ) {
          const prev = anteriorResult.value.data;
          setTrends({
            receita: calcularVariacaoPct(dashData.receita, prev.receita),
            taxaConversao: calcularVariacaoPct(dashData.taxa_conversao, prev.taxa_conversao),
          });
        } else {
          setTrends({});
        }

        if (ativResult.status === 'fulfilled') {
          const list = normalizeListResponse<ProximaAtividade>(ativResult.value.data);
          list.sort((a, b) => new Date(a.data).getTime() - new Date(b.data).getTime());
          setProximasAtividades(list.slice(0, 5));
        } else {
          setProximasAtividades([]);
        }
      })
      .catch((err: Error) => {
        setError(err.message || 'Erro ao carregar dashboard.');
        setProximasAtividades([]);
      })
      .finally(() => setLoading(false));
  }, [periodoFiltro]);

  return {
    slug,
    isVendedor,
    etapasAtivas,
    data,
    proximasAtividades,
    loading,
    error,
    showFiltro,
    periodoFiltro,
    filtroRef,
    etapasComValor,
    chartData,
    periodoLabels,
    chartTitle,
    trends,
    toggleFiltro,
    selecionarPeriodo,
  };
}
