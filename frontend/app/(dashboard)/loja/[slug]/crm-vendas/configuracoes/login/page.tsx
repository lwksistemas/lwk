'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { LoginConfigPageContent } from '@/components/clinica-beleza/login-config-page/LoginConfigPageContent';
import type { LoginColorPreset } from '@/components/clinica-beleza/login-config-page/login-config-page-types';

const CORES_PRE_DEFINIDAS: LoginColorPreset[] = [
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
  { nome: 'Vermelho', primaria: '#EF4444', secundaria: '#DC2626' },
  { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
  { nome: 'Laranja', primaria: '#F97316', secundaria: '#EA580C' },
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
];

export default function ConfiguracoesLoginPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/crm-vendas/configuracoes`;

  useEffect(() => {
    if (authService.isVendedor()) {
      router.replace(`/loja/${slug}/crm-vendas`);
    }
  }, [router, slug]);

  if (authService.isVendedor()) return null;

  return (
    <LoginConfigPageContent
      slug={slug}
      apiPath="/crm-vendas/login-config/"
      backHref={base}
      accentColor="#10B981"
      defaultPrimary="#10B981"
      defaultSecondary="#059669"
      colorPresets={CORES_PRE_DEFINIDAS}
    />
  );
}
