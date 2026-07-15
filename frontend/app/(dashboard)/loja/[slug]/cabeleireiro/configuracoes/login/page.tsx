'use client';

import { useParams } from 'next/navigation';
import { LoginConfigPageContent } from '@/components/clinica-beleza/login-config-page/LoginConfigPageContent';
import type { LoginColorPreset } from '@/components/clinica-beleza/login-config-page/login-config-page-types';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';

const CORES_PRE_DEFINIDAS: LoginColorPreset[] = [
  { nome: 'Lumina', primaria: '#4A3042', secundaria: '#6B4560' },
  { nome: 'Blush', primaria: '#C4A4B0', secundaria: '#A88494' },
  { nome: 'Burgundy', primaria: '#8B3D52', secundaria: '#6B2F40' },
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
];

export default function SalaoConfigLoginPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/cabeleireiro/configuracoes`;

  return (
    <LoginConfigPageContent
      slug={slug}
      apiPath="/crm-vendas/login-config/"
      backHref={base}
      accentColor={SALAO_PRIMARY}
      defaultPrimary={SALAO_PRIMARY}
      defaultSecondary="#6B4560"
      colorPresets={CORES_PRE_DEFINIDAS}
      backgroundDescription="Opcional — se vazio, usa a imagem padrão do salão"
      title="Configurar tela de login"
    />
  );
}
