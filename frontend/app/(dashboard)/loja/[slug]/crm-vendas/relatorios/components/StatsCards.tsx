'use client';

import { DollarSign, Users, TrendingUp } from 'lucide-react';

interface Props {
  totalVendas: number;
  vendedoresAtivos: number;
  totalComissoes: number;
  loading: boolean;
}

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);

export function StatsCards({ totalVendas, vendedoresAtivos, totalComissoes, loading }: Props) {
  const cards = [
    { icon: DollarSign, label: 'Total de Vendas (Mês)', value: formatarMoeda(totalVendas), color: 'green' },
    { icon: Users, label: 'Vendedores Ativos', value: String(vendedoresAtivos), color: 'blue' },
    { icon: TrendingUp, label: 'Comissões (Mês)', value: formatarMoeda(totalComissoes), color: 'purple' },
  ];

  const colorMap: Record<string, string> = {
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div key={c.label} className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${colorMap[c.color]}`}><Icon size={20} /></div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">{c.label}</p>
                {loading ? (
                  <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
                ) : (
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{c.value}</p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
