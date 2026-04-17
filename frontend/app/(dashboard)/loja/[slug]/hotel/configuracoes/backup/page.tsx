'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Database, Download, Upload, ArrowLeft, HardDrive, Shield } from 'lucide-react';
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg">
                <Database className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Backup de Dados</h1>
                <p className="text-white/80 text-sm">Exportar e importar dados do hotel</p>
              </div>
            </div>
            <Link href={`/loja/${slug}/hotel/configuracoes`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1">
              <ArrowLeft className="w-4 h-4" /> Voltar
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Exportar */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
          <div className="h-1.5 bg-gradient-to-r from-emerald-500 to-teal-600" />
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
                <Download className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Exportar Backup</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-4">
                  Baixe um arquivo com todos os dados do hotel: reservas, hóspedes, quartos, tarifas e governança.
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  {lojaId ? (
                    <BackupButton lojaId={lojaId} lojaNome={lojaNome} />
                  ) : (
                    <p className="text-sm text-red-600">Não foi possível identificar a loja.</p>
                  )}
                </div>
                <div className="mt-4 flex items-start gap-2 p-3 bg-emerald-50 dark:bg-emerald-900/10 rounded-lg border border-emerald-200 dark:border-emerald-800/30">
                  <Shield className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mt-0.5 shrink-0" />
                  <p className="text-xs text-emerald-700 dark:text-emerald-300">
                    O backup é gerado com todos os dados da loja e pode ser usado para restauração futura.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Importar */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
          <div className="h-1.5 bg-gradient-to-r from-blue-500 to-indigo-600" />
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                <Upload className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Importar Backup</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-4">
                  Restaurar dados a partir de um arquivo de backup exportado anteriormente.
                </p>
                <button disabled className="px-5 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-lg cursor-not-allowed text-sm font-medium">
                  Em breve
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
          <div className="h-1.5 bg-gradient-to-r from-amber-500 to-orange-600" />
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
                <HardDrive className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Sobre os Backups</h2>
                <ul className="mt-2 space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" /> Recomendamos fazer backup regularmente</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" /> O arquivo contém dados de todas as tabelas do hotel</li>
                  <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" /> Guarde o arquivo em local seguro</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
