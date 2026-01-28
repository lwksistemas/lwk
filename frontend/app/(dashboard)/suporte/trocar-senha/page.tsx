'use client';

import TrocarSenhaForm from '@/components/auth/TrocarSenhaForm';

export default function TrocarSenhaSuportePage() {
  return (
    <TrocarSenhaForm
      userType="suporte"
      endpoint="/superadmin/usuarios/alterar_senha_primeiro_acesso/"
      redirectTo="/suporte/dashboard"
      themeColor="blue"
    />
  );
}
