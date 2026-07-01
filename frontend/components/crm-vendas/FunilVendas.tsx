'use client';

import { useMemo } from 'react';
import { TrendingUp } from 'lucide-react';
import { formatCrmBrlCompact } from '@/lib/crm-utils';

interface EtapaFunil {
  etapa: string;
  valor: number;
  quantidade: number;
}

interface Props {
  dados: EtapaFunil[];
  etapasConfig: { key: string; label: string }[];
}

const CORES_FUNIL = [
  'bg-blue-500',
  'bg-indigo-500',
  'bg-purple-500',
  'bg-pink-500',
  'bg-orange-500',
  'bg-emerald-500',
  'bg-red-500',
];

export default function FunilVendas({ dados, etapasConfig }: Props) {
  const etapasOrdenadas = useMemo(() => {
    return etapasConfig
      .map((ec) => {
        const d = dados.find((d) => d.etapa === ec.key);
        return {
          key: ec.key,
          label: ec.label,
          quantidade: d?.quantidade || 0,
          valor: d?.valor || 0,
        };
      })
      .filter((e) => e.key !== 'closed_lost'); // Não mostrar perdidas no funil
  }, [dados, etapasConfig]);

  const maxQtd = Math.max(...etapasOrdenadas.map((e) => e.quantidade), 1);
  const total = etapasOrdenadas.reduce((s, e) => s + e.quantidade, 0);

  if (total === 0) {
    return (
      <div className="bg-white dark:bg-[#16325c] rounded-2xl border border-gray-200 dark:border-[#0d1f3c] p-6">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
          <TrendingUp size={16} className="text-[#0176d3]" /> Funil de Vendas
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
          Nenhuma oportunidade no pipeline
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-[#16325c] rounded-2xl border border-gray-200 dark:border-[#0d1f3c] p-6">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
        <TrendingUp size={16} className="text-[#0176d3]" /> Funil de Vendas
        <span className="text-[10px] font-normal text-gray-400 dark:text-gray-500 ml-auto">No período</span>
      </h3>
      <div className="space-y-3">
        {etapasOrdenadas.map((etapa, idx) => {
          const pct = (etapa.quantidade / maxQtd) * 100;
          const cor = CORES_FUNIL[idx % CORES_FUNIL.length];
          return (
            <div key={etapa.key} className="group">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {etapa.label}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-900 dark:text-white">
                    {etapa.quantidade}
                  </span>
                  <span className="text-[10px] text-gray-500 dark:text-gray-400">
                    {formatCrmBrlCompact(etapa.valor)}
                  </span>
                </div>
              </div>
              <div className="h-6 bg-gray-100 dark:bg-gray-700/50 rounded-full overflow-hidden relative">
                <div
                  className={`h-full ${cor} rounded-full transition-all duration-500 flex items-center justify-end pr-2`}
                  style={{ width: `${Math.max(pct, 8)}%` }}
                >
                  {pct > 20 && (
                    <span className="text-[10px] font-bold text-white">
                      {Math.round((etapa.quantidade / total) * 100)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {/* Resumo */}
      <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>Total no pipeline: <strong className="text-gray-900 dark:text-white">{total}</strong></span>
        <span>Valor total: <strong className="text-green-600 dark:text-green-400">{formatCrmBrlCompact(etapasOrdenadas.reduce((s, e) => s + e.valor, 0))}</strong></span>
      </div>
    </div>
  );
}
