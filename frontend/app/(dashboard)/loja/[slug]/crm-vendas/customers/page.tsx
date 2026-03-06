'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';

interface Conta {
  id: number;
  nome: string;
  segmento: string;
  telefone?: string;
  email?: string;
  cidade?: string;
  created_at: string;
}

export default function CrmVendasCustomersPage() {
  const [contas, setContas] = useState<Conta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<Conta[] | { results: Conta[] }>('/crm-vendas/contas/')
      .then((res) => {
        const data = res.data;
        setContas(
          Array.isArray(data) ? data : (data as { results: Conta[] }).results ?? []
        );
      })
      .catch((err) => {
        setError(
          err.response?.data?.detail || 'Erro ao carregar clientes.'
        );
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-gray-500 dark:text-gray-400">
          Carregando clientes...
        </div>
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

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Clientes
      </h1>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Nome
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Segmento
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Email
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Cidade
                </th>
              </tr>
            </thead>
            <tbody>
              {contas.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="py-8 text-center text-gray-500 dark:text-gray-400"
                  >
                    Nenhum cliente cadastrado.
                  </td>
                </tr>
              ) : (
                contas.map((conta) => (
                  <tr
                    key={conta.id}
                    className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                  >
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">
                      {conta.nome}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {conta.segmento || '–'}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {conta.email || '–'}
                    </td>
                    <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                      {conta.cidade || '–'}
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
