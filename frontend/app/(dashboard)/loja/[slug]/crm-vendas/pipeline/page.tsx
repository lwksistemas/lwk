'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { DollarSign } from 'lucide-react';
import PipelineBoard from '@/components/crm-vendas/PipelineBoard';

interface Oportunidade {
  id: number;
  titulo: string;
  valor: string;
  etapa: string;
  lead_nome: string;
  vendedor_nome?: string;
}

export default function CrmVendasPipelinePage() {
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<Oportunidade[] | { results: Oportunidade[] }>('/crm-vendas/oportunidades/')
      .then((res) => {
        const data = res.data;
        setOportunidades(
          Array.isArray(data)
            ? data
            : (data as { results: Oportunidade[] }).results ?? []
        );
      })
      .catch((err) => {
        setError(
          err.response?.data?.detail || 'Erro ao carregar oportunidades.'
        );
      })
      .finally(() => setLoading(false));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <DollarSign className="w-7 h-7" />
        Pipeline de vendas
      </h1>
      <PipelineBoard oportunidades={oportunidades} loading={loading} />
    </div>
  );
}
