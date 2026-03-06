'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import StatCard from '@/components/crm-vendas/StatCard';
import SalesChart from '@/components/crm-vendas/SalesChart';

interface DashboardData {
  leads: number;
  oportunidades: number;
  receita: number;
  pipeline_aberto: number;
  taxa_conversao: number;
  pipeline_por_etapa: { etapa: string; valor: number; quantidade: number }[];
  atividades_hoje: unknown[];
  performance_vendedores: { id: number; nome: string; receita_mes: number }[];
}

function formatMoney(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export default function CrmVendasDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<DashboardData>('/crm-vendas/dashboard/')
      .then((res) => setData(res.data))
      .catch((err) => {
        setError(err.response?.data?.detail || 'Erro ao carregar dashboard.');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-gray-500 dark:text-gray-400">Carregando...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300">
        {error}
      </div>
    );
  }

  if (!data) return null;

  const chartData =
    data.pipeline_por_etapa?.map((p) => ({
      name: p.etapa.replace(/_/g, ' '),
      valor: p.valor,
      quantidade: p.quantidade,
    })) ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Dashboard de Vendas
      </h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Receita do mês" value={formatMoney(data.receita)} />
        <StatCard title="Novos Leads" value={String(data.leads)} />
        <StatCard title="Negócios em aberto" value={String(data.oportunidades)} />
        <StatCard title="Taxa de conversão" value={`${data.taxa_conversao}%`} />
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-4">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
          Pipeline aberto
        </h3>
        <p className="text-2xl font-bold text-green-600 dark:text-green-400">
          {formatMoney(data.pipeline_aberto)}
        </p>
      </div>

      {chartData.length > 0 && (
        <SalesChart data={chartData} title="Pipeline por etapa" />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.performance_vendedores && data.performance_vendedores.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
              Performance por vendedor (mês)
            </h3>
            <ul className="space-y-2">
              {data.performance_vendedores.map((v) => (
                <li
                  key={v.id}
                  className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-0"
                >
                  <span className="text-gray-900 dark:text-white">{v.nome}</span>
                  <span className="font-medium text-green-600 dark:text-green-400">
                    {formatMoney(v.receita_mes)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.atividades_hoje && data.atividades_hoje.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
              Atividades de hoje
            </h3>
            <ul className="space-y-2">
              {(
                data.atividades_hoje as {
                  id: number;
                  titulo: string;
                  tipo: string;
                  data: string;
                }[]
              ).map((a) => (
                <li
                  key={a.id}
                  className="flex justify-between items-center py-1 text-sm"
                >
                  <span className="text-gray-700 dark:text-gray-300">
                    {a.titulo}
                  </span>
                  <span className="text-gray-500 capitalize">{a.tipo}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
