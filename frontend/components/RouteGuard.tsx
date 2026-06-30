'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { authService, UserType } from '@/lib/auth';
import apiClient from '@/lib/api-client';

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
      
      // Se é loja, sincronizar slug da URL quando session ainda não tem (evita bloquear menu)
      if (allowedUserType === 'loja' && requiredSlug) {
        const onAssinaturaPage = pathname.includes('/assinatura');
        if (onAssinaturaPage) {
          return;
        }
        if (!lojaSlug) {
          authService.setLojaSlug(requiredSlug);
          if (typeof document !== 'undefined') {
            document.cookie = `loja_slug=${encodeURIComponent(requiredSlug)}; path=/; max-age=86400; SameSite=Lax`;
          }
          return;
        }
        if (requiredSlug !== lojaSlug) {
          // Atalho na URL (ex.: felix) vs slug real na sessão — na assinatura bloqueada não redirecionar ao CRM
          if (onAssinaturaPage) {
            const lojaId = typeof window !== 'undefined' ? sessionStorage.getItem('current_loja_id') : null;
            if (lojaId) {
              authService.setLojaSlug(requiredSlug);
              if (typeof document !== 'undefined') {
                document.cookie = `loja_slug=${encodeURIComponent(requiredSlug)}; path=/; max-age=86400; SameSite=Lax`;
              }
              return;
            }
          }
          const lojaId = typeof window !== 'undefined' ? sessionStorage.getItem('current_loja_id') : null;
          if (lojaId) {
            apiClient
              .get(`/superadmin/lojas/info_publica/?slug=${encodeURIComponent(requiredSlug)}`)
              .then((res) => {
                if (res.data?.id && String(res.data.id) === lojaId) {
                  authService.setLojaSlug(requiredSlug);
                  if (typeof document !== 'undefined') {
                    document.cookie = `loja_slug=${encodeURIComponent(requiredSlug)}; path=/; max-age=86400; SameSite=Lax`;
                  }
                  return;
                }
                if (!onAssinaturaPage) {
                  router.replace(getLojaDashboardPath(lojaSlug));
                }
              })
              .catch((err: { response?: { data?: { code?: string } } }) => {
                const code = err?.response?.data?.code;
                if (code === 'STORE_BLOCKED_INADIMPLENCIA' || onAssinaturaPage) {
                  authService.setLojaSlug(requiredSlug);
                  return;
                }
                router.replace(getLojaDashboardPath(lojaSlug));
              });
            return;
          }
          if (!onAssinaturaPage) {
            router.replace(getLojaDashboardPath(lojaSlug));
          }
          return;
        }

        // Senha provisória: redirecionar antes de acessar o dashboard
        if (!pathname.includes('/trocar-senha')) {
          apiClient
            .get(`/superadmin/lojas/verificar_senha_provisoria/?slug=${encodeURIComponent(requiredSlug)}`)
            .then((res) => {
              if (res.data?.precisa_trocar_senha === true) {
                router.replace(`/loja/${requiredSlug}/trocar-senha`);
              }
            })
            .catch(() => {});
        }
      }
    };
    
    checkAccess();
  }, [pathname, allowedUserType, requiredSlug, router]);
  
  return <>{children}</>;
}
