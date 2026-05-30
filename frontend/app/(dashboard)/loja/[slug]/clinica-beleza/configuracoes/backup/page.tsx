'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ArrowLeft, Database, Download, Upload, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import BackupButton from '@/components/loja/BackupButton';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';

interface LojaInfo {
  id: number;
  nome: string;
}

export default function ClinicaBelezaBackupPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;
  const [loja, setLoja] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const carregarLoja = async () => {
      if (!slug) {
        setLoading(false);
        return;
      }
      try {
        const { data } = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
        if (data?.id) {
          setLoja({
            id: data.id,
            nome: data.nome || slug.replace(/-/g, ' '),
          });
          sessionStorage.setItem('current_loja_id', String(data.id));
        }
      } catch (error) {
        logger.warn('Erro ao carregar loja:', error);
      } finally {
        setLoading(false);
      }
    };
    carregarLoja();
  }, [slug]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] p-6">
        <div className="text-gray-500 dark:text-gray-400">Carregando...</div>
      </div>
    );
  }

  if (!loja) {
    return (
      <ClinicaBelezaPageContent>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-600 dark:text-red-400">Erro ao carregar informações da loja.</p>
        </div>
      </ClinicaBelezaPageContent>
    );
  }

  return (
    <ClinicaBelezaPageContent className="space-y-6">
      <Link
        href={base}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:underline"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Database size={28} style={{ color: CLINICA_BELEZA_PRIMARY }} />
          Backup de Dados
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Exporte e importe os dados da clínica com segurança
        </p>
      </div>

      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle size={20} className="text-amber-600 shrink-0 mt-0.5" />
          <ul className="text-sm text-amber-800 dark:text-amber-300 space-y-1">
            <li>• O backup inclui pacientes, agenda, procedimentos, financeiro e demais dados da clínica</li>
            <li>• Ao importar, os dados atuais podem ser substituídos</li>
            <li>• Recomendamos backups regulares</li>
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600">
              <Download size={24} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Exportar Backup</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Baixe uma cópia de segurança</p>
            </div>
          </div>
          <ul className="space-y-2 mb-4 text-sm text-gray-600 dark:text-gray-400">
            <li>• Pacientes e profissionais</li>
            <li>• Agenda e procedimentos</li>
            <li>• Financeiro e estoque</li>
          </ul>
          <BackupButton lojaId={loja.id} lojaNome={loja.nome} className="w-full" exportOnly />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600">
              <Upload size={24} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Importar Backup</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Restaure dados anteriores</p>
            </div>
          </div>
          <p className="text-xs text-red-700 dark:text-red-400 mb-4">
            Atenção: a importação pode substituir dados atuais. Use apenas backups desta loja.
          </p>
          <BackupButton lojaId={loja.id} lojaNome={loja.nome} className="w-full" importOnly />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start gap-4 mb-4">
            <div
              className="p-3 rounded-lg text-white"
              style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}33`, color: CLINICA_BELEZA_PRIMARY }}
            >
              <Database size={24} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Backup Automático</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Agende envio por e-mail</p>
            </div>
          </div>
          <BackupButton lojaId={loja.id} lojaNome={loja.nome} className="w-full" configOnly />
        </div>
      </div>
    </ClinicaBelezaPageContent>
  );
}
