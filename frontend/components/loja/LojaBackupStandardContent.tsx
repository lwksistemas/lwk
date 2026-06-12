'use client';

import Link from 'next/link';
import { ArrowLeft, Database, Download, Upload, AlertCircle, Clock } from 'lucide-react';
import BackupButton from '@/components/loja/BackupButton';
import type { LojaInfoPublica } from '@/hooks/useLojaInfoPublica';

export interface LojaBackupStandardContentProps {
  loja: LojaInfoPublica;
  backHref: string;
  subtitle: string;
  accentColor?: string;
  warningItems: string[];
  exportBullets: string[];
  importBullets?: string[];
  autoBackupBullets?: string[];
  tips?: string[];
  exportButtonClass?: string;
  importButtonClass?: string;
  autoButtonClass?: string;
  cardClass?: string;
  importWarning?: string;
}

export function LojaBackupStandardContent({
  loja,
  backHref,
  subtitle,
  accentColor = '#0176d3',
  warningItems,
  exportBullets,
  importBullets,
  autoBackupBullets,
  tips,
  exportButtonClass = 'w-full',
  importButtonClass = 'w-full',
  autoButtonClass = 'w-full',
  cardClass = 'bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6',
  importWarning = 'Atenção: a importação pode substituir dados atuais. Use apenas backups desta loja.',
}: LojaBackupStandardContentProps) {
  return (
    <div className="space-y-6">
      <Link
        href={backHref}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:underline"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Database size={28} style={{ color: accentColor }} />
          Backup de Dados
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{subtitle}</p>
      </div>

      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle size={20} className="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <ul className="text-sm text-amber-800 dark:text-amber-300 space-y-1">
            {warningItems.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className={cardClass}>
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
              <Download size={24} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Exportar Backup</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Baixe uma cópia de segurança</p>
            </div>
          </div>
          <ul className="space-y-2 mb-4 text-sm text-gray-600 dark:text-gray-400">
            {exportBullets.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
          <BackupButton lojaId={loja.id} lojaNome={loja.nome} className={exportButtonClass} exportOnly />
        </div>

        <div className={cardClass}>
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
              <Upload size={24} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Importar Backup</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Restaure dados anteriores</p>
            </div>
          </div>
          <p className="text-xs text-red-700 dark:text-red-400 mb-4">{importWarning}</p>
          {importBullets && importBullets.length > 0 && (
            <ul className="space-y-2 mb-4 text-sm text-gray-600 dark:text-gray-400">
              {importBullets.map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          )}
          <BackupButton lojaId={loja.id} lojaNome={loja.nome} className={importButtonClass} importOnly />
        </div>

        <div className={cardClass}>
          <div className="flex items-start gap-4 mb-4">
            <div
              className="p-3 rounded-lg"
              style={{ backgroundColor: `${accentColor}33`, color: accentColor }}
            >
              <Clock size={24} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Backup Automático</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Agende envio por e-mail</p>
            </div>
          </div>
          {autoBackupBullets && autoBackupBullets.length > 0 && (
            <ul className="space-y-2 mb-4 text-sm text-gray-600 dark:text-gray-400">
              {autoBackupBullets.map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: accentColor }} />
                  {item}
                </li>
              ))}
            </ul>
          )}
          <BackupButton lojaId={loja.id} lojaNome={loja.nome} className={autoButtonClass} configOnly />
        </div>
      </div>

      {tips && tips.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">💡 Dicas de Backup</h3>
          <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
            {tips.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
