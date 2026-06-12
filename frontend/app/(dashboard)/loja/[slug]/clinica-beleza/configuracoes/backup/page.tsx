'use client';

import { useParams } from 'next/navigation';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import { LojaBackupStandardContent } from '@/components/loja/LojaBackupStandardContent';
import { useLojaInfoPublica } from '@/hooks/useLojaInfoPublica';

export default function ClinicaBelezaBackupPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;
  const { loja, loading, error } = useLojaInfoPublica(slug);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] p-6">
        <div className="text-gray-500 dark:text-gray-400">Carregando...</div>
      </div>
    );
  }

  if (!loja || error) {
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
      <LojaBackupStandardContent
        loja={loja}
        backHref={base}
        subtitle="Exporte e importe os dados da clínica com segurança"
        accentColor={CLINICA_BELEZA_PRIMARY}
        warningItems={[
          'O backup inclui pacientes, agenda, procedimentos, financeiro e demais dados da clínica',
          'Ao importar, os dados atuais podem ser substituídos',
          'Recomendamos backups regulares',
        ]}
        exportBullets={['Pacientes e profissionais', 'Agenda e procedimentos', 'Financeiro e estoque']}
      />
    </ClinicaBelezaPageContent>
  );
}
