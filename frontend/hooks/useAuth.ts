/**
 * Hook customizado para autenticação
 * Fornece informações do usuário e funções de autenticação
 */

import { useState, useEffect } from 'react';
import { getUser, isAuthenticated, logout as authLogout, type User } from '@/lib/auth';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = () => {
    const isAuth = isAuthenticated();
    setAuthenticated(isAuth);

    if (isAuth) {
      const userData = getUser();
      setUser(userData);
    }

    setLoading(false);
  };

  const logout = () => {
    authLogout();
  };

  const isAdmin = user?.is_admin || false;
  const isRecepcao = user?.is_recepcao || false;
  const isProfissional = user?.is_profissional || false;

  return {
    user,
    loading,
    authenticated,
    isAdmin,
    isRecepcao,
    isProfissional,
    logout,
  };
}
