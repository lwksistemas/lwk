'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, FileText } from 'lucide-react';
import { listLaudos } from '@/lib/radiologia-api';
import type { Laudo } from '@/lib/radiologia-types';

export default function RadiologiaLaudosListPage() {
  const slug = useParams().slug as string;
  const [items, setItems] = useState<Laudo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listLaudos()
      .then(setItems)
      .catch(() => setError('Erro ao carregar laudos.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <FileText className="hidden h-6 w-6 sm:block" />
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Laudos</h1>
              <p className="text-xs text-white/80">Estruturados + PDF</p>
            </div>
          </div>
          <Link href={`/loja/${slug}/radiologia`} className="inline-flex w-fit items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25">
            <ArrowLeft className="h-4 w-4" /> Voltar
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" /></div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        ) : items.length === 0 ? (
          <p className="text-center text-gray-500">Nenhum laudo ainda. Abra a partir de um pedido.</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-gray-800">
                  <th className="px-4 py-3">Accession</th>
                  <th className="px-4 py-3">Paciente</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((l) => (
                  <tr key={l.id} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="px-4 py-3 font-mono text-xs">{l.accession_number}</td>
                    <td className="px-4 py-3">{l.paciente_nome}</td>
                    <td className="px-4 py-3 capitalize">{l.status}</td>
                    <td className="px-4 py-3 text-right">
                      <Link className="text-teal-700" href={`/loja/${slug}/radiologia/laudos/${l.id}`}>Abrir</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
