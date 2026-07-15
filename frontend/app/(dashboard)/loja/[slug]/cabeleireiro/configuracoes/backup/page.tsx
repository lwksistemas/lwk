'use client';

import { useParams } from 'next/navigation';
import { LojaBackupStandardContent } from '@/components/loja/LojaBackupStandardContent';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import { useLojaInfoPublica } from '@/hooks/useLojaInfoPublica';

export default function SalaoBackupPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/cabeleireiro/configuracoes`;
  const { loja, loading, error } = useLojaInfoPublica(slug);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] p-6">
        <div className="text-gray-500">Carregando...</div>
      </div>
    );
  }

  if (!loja || error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-600">Erro ao carregar informações da loja.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6">
      <LojaBackupStandardContent
        loja={loja}
        backHref={base}
        subtitle="Exporte e importe os dados do salão com segurança"
        accentColor={SALAO_PRIMARY}
        warningItems={[
          'O backup inclui clientes, agenda, serviços, profissionais e demais dados do salão',
          'Ao importar, os dados atuais podem ser substituídos',
          'Recomendamos backups regulares',
        ]}
        exportBullets={['Clientes e profissionais', 'Agenda e serviços', 'Configurações da loja']}
      />
    </div>
  );
}
