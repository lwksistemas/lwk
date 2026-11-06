'use client';

import { useParams } from 'next/navigation';
import ConfirmarSenhaSistema from '@/components/auth/ConfirmarSenhaSistema';

export default function RecuperarSenhaLojaPage() {
  const params = useParams();
  const slug = typeof params.slug === 'string' ? params.slug : '';
  return (
    <ConfirmarSenhaSistema
      loginPath={slug ? `/loja/${slug}/login` : '/login'}
      endpoint="/superadmin/lojas/confirmar_recuperacao_senha/"
    />
  );
}
