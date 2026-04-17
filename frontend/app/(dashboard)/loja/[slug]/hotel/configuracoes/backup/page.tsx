'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Database } from 'lucide-react';
import Link from 'next/link';
import BackupButton from '@/components/loja/BackupButton';
import apiClient from '@/lib/api-client';

export default function HotelBackupPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [lojaId, setLojaId] = useState<number | null>(null);
  const [lojaNome, setLojaNome] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
        if (data?.id) {
          setLojaId(data.id);
          setLojaNome(data.nome || slug);
          sessionStorage.setItem('current_loja_id', String(data.id));
        }
      } catch { /* fallback */ }
      setLoading(false);
    })();
  }, [slug]);

  if (loading) return <div className="max-w-3xl mx-auto p-6 text-sm text-gray-500">Carregando...</div>;

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Database size={24} className="text-sky-600" /> Backup de Dados
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Exportar e importar dados do hotel</p>
        <Link href={`/loja/${slug}/hotel/configuracoes`} className="text-sm text-sky-700 hover:underline">← Voltar</Link>
      </div>

      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 space-y-4">
        <h2 className="text-lg font-semibold">Exportar Backup</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Baixe um arquivo com todos os dados do hotel: reservas, hóspedes, quartos, tarifas e governança.
        </p>
        {lojaId ? (
          <BackupButton lojaId={lojaId} lojaNome={lojaNome} />
        ) : (
          <p className="text-sm text-red-600">Não foi possível identificar a loja.</p>
        )}
      </div>

      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 space-y-4">
        <h2 className="text-lg font-semibold">Importar Backup</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Em breve: restaurar dados a partir de um arquivo de backup.
        </p>
        <button disabled className="px-4 py-2 bg-gray-300 dark:bg-gray-700 text-gray-500 rounded-lg cursor-not-allowed">
          Em breve
        </button>
      </div>
    </div>
  );
}
