'use client';

import { useParams } from 'next/navigation';
import { LoginConfigPageContent } from '@/components/clinica-beleza/login-config-page/LoginConfigPageContent';
import type { LoginColorPreset } from '@/components/clinica-beleza/login-config-page/login-config-page-types';

const CORES_PRE_DEFINIDAS: LoginColorPreset[] = [
  { nome: 'Burgundy', primaria: '#8B3D52', secundaria: '#6B2F40' },
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
  { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
  { nome: 'Laranja', primaria: '#F97316', secundaria: '#EA580C' },
];

export default function ClinicaBelezaConfiguracoesLoginPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;

  return (
    <LoginConfigPageContent
      slug={slug}
      apiPath="/crm-vendas/login-config/"
      backHref={base}
      accentColor={'var(--cb-primary, #8B3D52)'}
      defaultPrimary="#8B3D52"
      defaultSecondary="#6B2F40"
      colorPresets={CORES_PRE_DEFINIDAS}
      backgroundDescription="Opcional — se vazio, usa a imagem padrão do tipo de loja (ex.: clínica de beleza)"
      title="Configurar tela de login"
    />
  );
}
