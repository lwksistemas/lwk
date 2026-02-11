"use client";

/**
 * Componente de Proteção de Rotas
 * Verifica autenticação e permissões
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, getUser, type User } from "@/lib/auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredCargo?: 'admin' | 'recepcao' | 'profissional' | 'admin_recepcao';
}

export default function ProtectedRoute({ children, requiredCargo }: ProtectedRouteProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = () => {
    // Verificar se está autenticado
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    // Verificar permissões se necessário
    if (requiredCargo) {
      const user = getUser();
      
      if (!user) {
        router.push('/login');
        return;
      }

      let hasPermission = false;

      switch (requiredCargo) {
        case 'admin':
          hasPermission = user.is_admin;
          break;
        case 'recepcao':
          hasPermission = user.is_recepcao;
          break;
        case 'profissional':
          hasPermission = user.is_profissional;
          break;
        case 'admin_recepcao':
          hasPermission = user.is_admin || user.is_recepcao;
          break;
        default:
          hasPermission = true;
      }

      if (!hasPermission) {
        router.push('/unauthorized');
        return;
      }
    }

    setAuthorized(true);
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-100 via-purple-50 to-white">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Verificando autenticação...</p>
        </div>
      </div>
    );
  }

  if (!authorized) {
    return null;
  }

  return <>{children}</>;
}
