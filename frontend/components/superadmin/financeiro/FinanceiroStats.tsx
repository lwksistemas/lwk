/**
 * Componente de estatísticas financeiras
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import { useEffect, useState } from 'react';
import { formatCurrency } from '@/lib/financeiro-helpers';
import type { FinanceiroStats as Stats } from '@/hooks/useFinanceiroStats';

const CHAVE_RESUMO = 'lwk-financeiro-resumo-oculto';

interface FinanceiroStatsProps {
  stats: Stats | null;
  loading: boolean;
}

function StatCard({ title, value, icon }: { title: string; value: string | number; icon: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{value}</p>
        </div>
        <div className="text-3xl">{icon}</div>
      </div>
    </div>
  );
}

export function FinanceiroStats({ stats, loading }: FinanceiroStatsProps) {
  const [oculto, setOculto] = useState(false);

  useEffect(() => {
    setOculto(window.localStorage.getItem(CHAVE_RESUMO) === '1');
  }, []);

  const alternar = () => {
    setOculto((atual) => {
      const proximo = !atual;
      window.localStorage.setItem(CHAVE_RESUMO, proximo ? '1' : '0');
      return proximo;
    });
  };

  return (
    <div className="mb-6">
      <div className="flex justify-end mb-2">
        <button
          type="button"
          onClick={alternar}
          className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          {oculto ? 'Mostrar resumo' : 'Ocultar resumo'}
        </button>
      </div>
      {!oculto && loading && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 animate-pulse">
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      )}
      {!oculto && stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard
            title="Receita Total"
            value={formatCurrency(stats.receita_total)}
            icon="💰"
          />
          <StatCard
            title="Assinaturas Ativas"
            value={stats.assinaturas_ativas}
            icon="✅"
          />
          <StatCard
            title="Pagamentos Pendentes"
            value={stats.pagamentos_pendentes}
            icon="⏳"
          />
          <StatCard
            title="Receita Pendente"
            value={formatCurrency(stats.receita_pendente)}
            icon="💸"
          />
        </div>
      )}
    </div>
  );
}
