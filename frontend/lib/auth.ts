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
    const response = await apiClient.post<AuthTokens>('/auth/token/', credentials);
    const { access, refresh } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user_type', userType);
    
    if (lojaSlug) {
      localStorage.setItem('loja_slug', lojaSlug);
    }
    
    return response.data;
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('loja_slug');
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
