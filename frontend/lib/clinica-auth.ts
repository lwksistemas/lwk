/**
 * Serviço de Autenticação
 * Gerencia tokens JWT e informações do usuário
 */

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  cargo: 'admin' | 'recepcao' | 'profissional';
  cargo_display: string;
  is_admin: boolean;
  is_recepcao: boolean;
  is_profissional: boolean;
  professional_info?: {
    id: number;
    name: string;
    specialty: string;
  };
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

/**
 * Salvar token no localStorage
 */
export function saveToken(access: string, refresh: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }
}

/**
 * Obter access token
 */
export function getAccessToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
}

/**
 * Obter refresh token
 */
export function getRefreshToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('refresh_token');
  }
  return null;
}

/**
 * Salvar informações do usuário
 */
export function saveUser(user: User) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('user', JSON.stringify(user));
  }
}

/**
 * Obter informações do usuário
 */
export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
  }
  return null;
}

/**
 * Verificar se está autenticado
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

/**
 * Verificar se é admin
 */
export function isAdmin(): boolean {
  const user = getUser();
  return user?.is_admin || false;
}

/**
 * Verificar se é recepção
 */
export function isRecepcao(): boolean {
  const user = getUser();
  return user?.is_recepcao || false;
}

/**
 * Verificar se é profissional
 */
export function isProfissional(): boolean {
  const user = getUser();
  return user?.is_profissional || false;
}

/**
 * Logout
 */
export async function logout() {
  if (typeof window !== 'undefined') {
    const refreshToken = getRefreshToken();
    
    // Tentar fazer logout no backend
    if (refreshToken) {
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clinica-beleza/auth/logout/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAccessToken()}`,
          },
          body: JSON.stringify({ refresh: refreshToken }),
        });
      } catch (error) {
        console.error('Erro ao fazer logout:', error);
      }
    }
    
    // Limpar localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('token'); // Token antigo (compatibilidade)
    
    // Redirecionar para login
    window.location.href = '/login';
  }
}

/**
 * Refresh do token
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  
  if (!refreshToken) {
    return null;
  }
  
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clinica-beleza/auth/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access);
      return data.access;
    }
    
    // Se falhar, fazer logout
    logout();
    return null;
  } catch (error) {
    console.error('Erro ao refresh token:', error);
    logout();
    return null;
  }
}

/**
 * Fazer requisição autenticada
 */
export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let token = getAccessToken();
  
  if (!token) {
    throw new Error('Não autenticado');
  }
  
  // Adicionar token no header
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  
  let response = await fetch(url, { ...options, headers });
  
  // Se token expirou, tentar refresh
  if (response.status === 401) {
    token = await refreshAccessToken();
    
    if (token) {
      // Tentar novamente com novo token
      headers.Authorization = `Bearer ${token}`;
      response = await fetch(url, { ...options, headers });
    }
  }
  
  return response;
}
