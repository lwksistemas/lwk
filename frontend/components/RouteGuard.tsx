'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { authService, UserType } from '@/lib/auth';

interface RouteGuardProps {
  children: React.ReactNode;
  allowedUserType: UserType;
  requiredSlug?: string; // Para lojas
}

/**
 * Componente de proteção de rotas
 * Garante que apenas usuários do tipo correto podem acessar a rota
 */
export default function RouteGuard({ children, allowedUserType, requiredSlug }: RouteGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  
  useEffect(() => {
    const checkAccess = () => {
      const userType = authService.getUserType();
      const lojaSlug = authService.getLojaSlug();
      
      // Se não está autenticado, permitir (será tratado por outro guard)
      if (!userType) {
        return;
      }
      
      // Verificar se o tipo de usuário está correto
      if (userType !== allowedUserType) {
        // Redirecionar para o dashboard correto
        switch (userType) {
          case 'superadmin':
            router.replace('/superadmin/dashboard');
            break;
          case 'suporte':
            router.replace('/suporte/dashboard');
            break;
          case 'loja':
            if (lojaSlug) {
              router.replace(`/loja/${lojaSlug}/dashboard`);
            } else {
              router.replace('/');
            }
            break;
          default:
            router.replace('/');
        }
        return;
      }
      
      // Se é loja, verificar se está tentando acessar outra loja
      if (allowedUserType === 'loja' && requiredSlug && lojaSlug && requiredSlug !== lojaSlug) {
        router.replace(`/loja/${lojaSlug}/dashboard`);
        return;
      }
    };
    
    checkAccess();
  }, [pathname, allowedUserType, requiredSlug, router]);
  
  return <>{children}</>;
}
