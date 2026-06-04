'use client';

import MfaSecurityPanel from '@/components/auth/MfaSecurityPanel';

export default function SuporteSegurancaPage() {
  return (
    <MfaSecurityPanel
      theme="blue"
      title="Segurança da conta"
      subtitle="Autenticação em duas etapas (Suporte)"
      backHref="/suporte/dashboard"
      backLabel="Chamados"
    />
  );
}
