'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Monitor } from 'lucide-react';
import { useRadiologiaCrud } from '@/hooks/useRadiologiaCrud';
import type { Equipamento } from '@/lib/radiologia-types';

const MODALIDADE: Record<string, string> = {
  US: 'Ultrassom',
  DX: 'Raio-X',
  MG: 'Mamógrafo',
  CR: 'CR / Digitalizador',
  CT: 'Tomógrafo',
  MR: 'Ressonância',
};

export default function RadiologiaEquipamentosPage() {
  const slug = useParams().slug as string;
  const { items, loading, error } = useRadiologiaCrud<Equipamento>(
    '/radiologia/equipamentos/',
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="flex w-full max-w-full flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Monitor className="hidden h-6 w-6 sm:block" />
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Equipamentos</h1>
              <p className="text-xs text-white/80">Máquinas liberadas para esta clínica</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href={`/loja/${slug}/radiologia`} className="inline-flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25">
              <ArrowLeft className="h-4 w-4" /> Voltar
            </Link>
          </div>
        </div>
      </header>

      <main className="w-full max-w-full px-4 py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}
        {loading ? (
          <div className="flex justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" /></div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-gray-800">
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3">AE Title</th>
                  <th className="px-4 py-3">Fabricante</th>
                  <th className="px-4 py-3">Modelo</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((e) => (
                  <tr key={e.id} className="border-b border-gray-100 hover:bg-gray-50 dark:border-gray-800">
                    <td className="px-4 py-3 font-medium">{e.nome}</td>
                    <td className="px-4 py-3">{MODALIDADE[e.modality] || e.modality}</td>
                    <td className="px-4 py-3 font-mono text-xs">{e.ae_title}</td>
                    <td className="px-4 py-3">{e.fabricante || '—'}</td>
                    <td className="px-4 py-3">{e.modelo || '—'}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
                        Liberada
                      </span>
                    </td>
                  </tr>
                ))}
                {!items.length && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-gray-500">
                      Nenhuma máquina liberada nesta clínica.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
