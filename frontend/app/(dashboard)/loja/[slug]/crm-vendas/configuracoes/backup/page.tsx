'use client';

import { useParams } from 'next/navigation';
import { LojaBackupStandardContent } from '@/components/loja/LojaBackupStandardContent';
import { useLojaInfoPublica } from '@/hooks/useLojaInfoPublica';

export default function BackupPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const { loja, loading, error } = useLojaInfoPublica(slug);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500 dark:text-gray-400">Carregando...</div>
      </div>
    );
  }

  if (!loja || error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-600 dark:text-red-400">Erro ao carregar informações da loja.</p>
        </div>
      </div>
    );
  }

  return (
    <LojaBackupStandardContent
      loja={loja}
      backHref={`/loja/${slug}/crm-vendas/configuracoes`}
      subtitle="Exporte e importe os dados da sua loja com segurança"
      accentColor="#0176d3"
      cardClass="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6"
      exportButtonClass="w-full !bg-green-600 hover:!bg-green-700"
      importButtonClass="w-full !bg-blue-600 hover:!bg-blue-700"
      autoButtonClass="w-full !bg-purple-600 hover:!bg-purple-700"
      importWarning="Atenção: A importação irá substituir todos os dados atuais. Só é possível importar backups exportados desta loja."
      warningItems={[
        'O backup inclui todos os dados do CRM (leads, oportunidades, atividades, etc.)',
        'Ao importar um backup, os dados atuais serão substituídos',
        'Recomendamos fazer backups regulares dos seus dados',
        'O arquivo de backup é um arquivo .zip compactado',
      ]}
      exportBullets={[
        'Leads e oportunidades',
        'Atividades e calendário',
        'Contas e contatos',
        'Configurações personalizadas',
      ]}
      importBullets={['Arquivo .zip de backup', 'Máximo 50MB', 'Processo pode levar alguns minutos']}
      autoBackupBullets={[
        'Backup diário, semanal ou mensal',
        'Receba por email automaticamente',
        'Configure horário de envio',
        'Backup manual sob demanda',
      ]}
      tips={[
        'Faça backups regulares (recomendamos semanalmente)',
        'Guarde os arquivos de backup em local seguro (nuvem, HD externo)',
        'Teste a restauração periodicamente para garantir que o backup está funcionando',
        'Mantenha múltiplas versões de backup (não sobrescreva o backup anterior)',
      ]}
    />
  );
}
