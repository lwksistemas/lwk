'use client';

import TrocarSenhaForm from '@/components/auth/TrocarSenhaForm';

export default function TrocarSenhaSuperAdminPage() {
  return (
    <TrocarSenhaForm
      userType="superadmin"
      endpoint="/superadmin/usuarios/alterar_senha_primeiro_acesso/"
      redirectTo="/superadmin/dashboard"
      themeColor="purple"
    />
  );
}
