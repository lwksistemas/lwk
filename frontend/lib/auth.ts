import apiClient from './api-client';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export type UserType = 'superadmin' | 'suporte' | 'loja';

export const authService = {
  async login(credentials: LoginCredentials, userType: UserType = 'superadmin', lojaSlug?: string): Promise<AuthTokens> {
    console.log('AuthService.login chamado:', { credentials: { username: credentials.username, password: '***' }, userType, lojaSlug });
    
    // Verificar se localStorage está disponível
    if (typeof window === 'undefined' || !window.localStorage) {
      console.error('localStorage não está disponível');
      throw new Error('localStorage não está disponível');
    }
    
    try {
      const response = await apiClient.post<AuthTokens>('/auth/token/', credentials);
      console.log('Login response recebida:', response.status, response.data);
      
      const { access, refresh } = response.data;
      
      if (!access || !refresh) {
        console.error('Tokens inválidos recebidos:', { access: !!access, refresh: !!refresh });
        throw new Error('Tokens inválidos recebidos do servidor');
      }
      
      // Salvar no localStorage
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_type', userType);
      
      if (lojaSlug) {
        localStorage.setItem('loja_slug', lojaSlug);
      }
      
      // Salvar também nos cookies para o middleware do Next.js
      document.cookie = `user_type=${userType}; path=/; max-age=86400; SameSite=Lax`;
      if (lojaSlug) {
        document.cookie = `loja_slug=${lojaSlug}; path=/; max-age=86400; SameSite=Lax`;
      }
      
      console.log('Tokens salvos no localStorage e cookies');
      
      // Verificar se os tokens foram realmente salvos
      const savedAccess = localStorage.getItem('access_token');
      const savedRefresh = localStorage.getItem('refresh_token');
      console.log('Verificação tokens salvos:', { 
        access: savedAccess ? 'OK' : 'FALHOU', 
        refresh: savedRefresh ? 'OK' : 'FALHOU' 
      });
      
      return response.data;
    } catch (error) {
      console.error('Erro no AuthService.login:', error);
      throw error;
    }
  },

  logout() {
    // Limpar localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('loja_slug');
    
    // Limpar cookies
    document.cookie = 'user_type=; path=/; max-age=0';
    document.cookie = 'loja_slug=; path=/; max-age=0';
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },

  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  },

  getUserType(): UserType | null {
    return localStorage.getItem('user_type') as UserType | null;
  },

  getLojaSlug(): string | null {
    return localStorage.getItem('loja_slug');
  },
};
