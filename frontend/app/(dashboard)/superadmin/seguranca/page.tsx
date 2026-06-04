'use client';

import MfaSecurityPanel from '@/components/auth/MfaSecurityPanel';

export default function SuperAdminSegurancaPage() {
  return (
    <MfaSecurityPanel
      theme="purple"
      title="Segurança da conta"
      subtitle="Autenticação em duas etapas (Super Admin)"
      backHref="/superadmin/dashboard"
      backLabel="Painel"
    />
  );
}
