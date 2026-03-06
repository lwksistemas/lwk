'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';

interface Lead {
  id: number;
  nome: string;
  empresa: string;
  email: string;
  telefone?: string;
  origem: string;
  status: string;
  valor_estimado?: string;
  created_at: string;
}

export default function CrmVendasLeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<Lead[] | { results: Lead[] }>('/crm-vendas/leads/')
      .then((res) => {
        const data = res.data;
        setLeads(Array.isArray(data) ? data : (data as { results: Lead[] }).results || []);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Erro ao carregar leads.');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-gray-500 dark:text-gray-400">Carregando leads...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Leads
      </h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Nome
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Empresa
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Email
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Origem
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {leads.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="py-8 text-center text-gray-500 dark:text-gray-400"
                  >
                    Nenhum lead cadastrado.
                  </td>
                </tr>
              ) : (
                leads.map((lead) => (
                  <tr
                    key={lead.id}
                    className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                  >
                    <td className="py-3 px-4 text-gray-900 dark:text-white">
                      {lead.nome}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {lead.empresa || '–'}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {lead.email || '–'}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400 capitalize">
                      {lead.origem}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-300 capitalize">
                        {lead.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
