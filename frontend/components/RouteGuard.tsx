'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { authService, UserType } from '@/lib/auth';

function getLojaDashboardPath(lojaSlug: string): string {
  if (typeof document === 'undefined') return `/loja/${lojaSlug}/dashboard`;
  return document.cookie.includes('loja_usa_crm=1')
    ? `/loja/${lojaSlug}/crm-vendas`
    : `/loja/${lojaSlug}/dashboard`;
}

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
              router.replace(getLojaDashboardPath(lojaSlug));
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
        router.replace(getLojaDashboardPath(lojaSlug));
        return;
      }
    };
    
    checkAccess();
  }, [pathname, allowedUserType, requiredSlug, router]);
  
  return <>{children}</>;
}
