'use client';

import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Filter, X } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

const ETAPAS_PADRAO = [
  { stage: 'Prospecção', value: 0 },
  { stage: 'Qualificação', value: 0 },
  { stage: 'Proposta', value: 0 },
  { stage: 'Negociação', value: 0 },
  { stage: 'Fechado (ganho)', value: 0 },
];

interface SalesChartProps {
  data?: { name: string; valor: number; quantidade?: number }[];
  title?: string;
}

interface Vendedor {
  id: number;
  nome: string;
}

export default function SalesChart({ data, title = 'Pipeline por etapa' }: SalesChartProps) {
  const [showFiltros, setShowFiltros] = useState(false);
  const [periodo, setPeriodo] = useState('mes_atual');
  const [vendedorId, setVendedorId] = useState<string>('todos');
  const [status, setStatus] = useState('todas');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [vendedores, setVendedores] = useState<Vendedor[]>([]);
  const [filteredData, setFilteredData] = useState(data);
  const [loading, setLoading] = useState(false);
  
  const isVendedor = authService.isVendedor();

  // Carregar vendedores (apenas para owner/admin)
  useEffect(() => {
    if (!isVendedor) {
      apiClient.get('/crm-vendas/vendedores/')
        .then(res => setVendedores(res.data.results || res.data || []))
        .catch(err => console.error('Erro ao carregar vendedores:', err));
    }
  }, [isVendedor]);

  // Aplicar filtros
  useEffect(() => {
    if (!data) {
      setFilteredData(undefined);
      return;
    }

    // Se não há filtros ativos, usar dados originais
    if (periodo === 'mes_atual' && vendedorId === 'todos' && status === 'todas') {
      setFilteredData(data);
      return;
    }

    // Aplicar filtros
    applyFilters();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [periodo, vendedorId, status, dataInicio, dataFim, data]);

  const applyFilters = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      // Filtro de período
      if (periodo === 'personalizado' && dataInicio && dataFim) {
        params.append('data_inicio', dataInicio);
        params.append('data_fim', dataFim);
      } else if (periodo !== 'mes_atual') {
        params.append('periodo', periodo);
      }
      
      // Filtro de vendedor
      if (vendedorId !== 'todos') {
        params.append('vendedor_id', vendedorId);
      }
      
      // Filtro de status
      if (status !== 'todas') {
        params.append('status', status);
      }

      const response = await apiClient.get(`/crm-vendas/dashboard/?${params.toString()}`);
      const pipelineData = response.data.pipeline_por_etapa || [];
      
      const newData = pipelineData.map((p: { etapa: string; valor: number; quantidade: number }) => ({
        name: getLabelEtapa(p.etapa),
        valor: p.valor,
        quantidade: p.quantidade,
      }));
      
      setFilteredData(newData.length > 0 ? newData : data);
    } catch (error) {
      console.error('Erro ao aplicar filtros:', error);
      setFilteredData(data);
    } finally {
      setLoading(false);
    }
  };

  const getLabelEtapa = (etapa: string): string => {
    const labels: Record<string, string> = {
      prospecting: 'Prospecção',
      qualification: 'Qualificação',
      proposal: 'Proposta',
      negotiation: 'Negociação',
      closed_won: 'Fechado (ganho)',
      closed_lost: 'Fechado (perdido)',
    };
    return labels[etapa] || etapa;
  };

  const limparFiltros = () => {
    setPeriodo('mes_atual');
    setVendedorId('todos');
    setStatus('todas');
    setDataInicio('');
    setDataFim('');
  };

  const temFiltrosAtivos = periodo !== 'mes_atual' || vendedorId !== 'todos' || status !== 'todas';

  const hasData = filteredData && filteredData.length > 0;
  const chartData = hasData
    ? filteredData.map((d) => ({
          stage: d.name,
          value: d.valor,
          Valor: d.valor,
          Oportunidades: d.quantidade ?? 0,
        }))
      : ETAPAS_PADRAO;

  return (
    <div className="bg-blue-50/40 dark:bg-blue-900/10 rounded-2xl border-2 border-blue-200 dark:border-blue-800 border-l-4 border-l-blue-500 shadow-md p-6">
      {/* Header com título e botão de filtros */}
      <div className="flex items-center justify-between mb-5">
        {title && (
          <h2 className="text-lg font-semibold text-blue-800 dark:text-blue-200">
            {title}
          </h2>
        )}
        <div className="flex items-center gap-2">
          {temFiltrosAtivos && (
            <button
              onClick={limparFiltros}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors flex items-center gap-1"
            >
              <X size={14} />
              Limpar
            </button>
          )}
          <button
            onClick={() => setShowFiltros(!showFiltros)}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1 ${
              temFiltrosAtivos
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
            }`}
          >
            <Filter size={14} />
            Filtros
            {temFiltrosAtivos && <span className="ml-1 px-1.5 py-0.5 bg-white/20 rounded-full text-xs">●</span>}
          </button>
        </div>
      </div>

      {/* Painel de Filtros */}
      {showFiltros && (
        <div className="mb-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Filtro de Período */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Período
              </label>
              <select
                value={periodo}
                onChange={(e) => setPeriodo(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                <option value="mes_atual">Este mês</option>
                <option value="ultimos_30_dias">Últimos 30 dias</option>
                <option value="ultimos_90_dias">Últimos 90 dias</option>
                <option value="este_ano">Este ano</option>
                <option value="personalizado">Personalizado</option>
              </select>
            </div>

            {/* Filtro de Vendedor (apenas para owner/admin) */}
            {!isVendedor && (
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Vendedor
                </label>
                <select
                  value={vendedorId}
                  onChange={(e) => setVendedorId(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="todos">Todos os vendedores</option>
                  {vendedores.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.nome}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Filtro de Status */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                <option value="todas">Todas as etapas</option>
                <option value="abertas">Apenas abertas</option>
                <option value="fechadas">Apenas fechadas</option>
              </select>
            </div>
          </div>

          {/* Período Personalizado */}
          {periodo === 'personalizado' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-gray-200 dark:border-gray-700">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Data Início
                </label>
                <input
                  type="date"
                  value={dataInicio}
                  onChange={(e) => setDataInicio(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Data Fim
                </label>
                <input
                  type="date"
                  value={dataFim}
                  onChange={(e) => setDataFim(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Gráfico */}
      <div style={{ width: '100%', height: 320 }} className="bg-white/60 dark:bg-slate-800/60 rounded-xl p-3 relative">
        {loading && (
          <div className="absolute inset-0 bg-white/50 dark:bg-gray-800/50 flex items-center justify-center rounded-xl z-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 12, right: 12, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.4} vertical={false} />
            <XAxis
              dataKey="stage"
              tick={{ fontSize: 12, fill: '#1e40af' }}
              axisLine={{ stroke: '#3b82f6', strokeWidth: 1 }}
              tickLine={false}
              className="text-blue-800 dark:text-blue-300"
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#1e40af' }}
              tickFormatter={(v) => (v >= 1000 ? `R${v / 1000}k` : `R${v}`)}
              axisLine={false}
              tickLine={false}
              className="text-blue-800 dark:text-blue-300"
            />
            <Tooltip
              formatter={(value: number | undefined) => [
                value != null
                  ? new Intl.NumberFormat('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                      minimumFractionDigits: 0,
                    }).format(value)
                  : '',
                'Valor',
              ]}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid rgba(0,0,0,0.08)',
                borderRadius: '12px',
                boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.06)',
                padding: '12px 16px',
              }}
              labelStyle={{ fontWeight: 600, marginBottom: 4 }}
            />
            <Legend wrapperStyle={{ paddingTop: 8 }} />
            <Bar
              dataKey="value"
              fill="#2563eb"
              radius={[8, 8, 0, 0]}
              name="Valor (R$)"
              maxBarSize={56}
              minPointSize={3}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
