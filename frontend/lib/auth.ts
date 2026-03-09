/**
 * Serviço de Autenticação
 * Sistema multi-tenant com suporte a SuperAdmin, Suporte e Lojas
 * Versão: 2.0 - Corrigido para usar sessionStorage e cookies
 */

import apiClient from './api-client';

export type UserType = 'superadmin' | 'suporte' | 'loja';

interface LoginCredentials {
  username: string;
  password: string;
  cpf_cnpj?: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
  user_type: UserType;
  loja_slug?: string;
  precisa_trocar_senha?: boolean;
}

class AuthService {
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_KEY = 'refresh_token';
  private readonly USER_TYPE_KEY = 'user_type';
  private readonly LOJA_SLUG_KEY = 'loja_slug';
  private readonly INTERNAL_NAV_KEY = 'internal_navigation';

  /**
   * Realiza login no sistema
   */
  async login(
    credentials: LoginCredentials,
    userType: UserType,
    slug?: string
  ): Promise<LoginResponse> {
    try {
      let endpoint = '';
      let payload: any = {
        username: credentials.username,
        password: credentials.password,
      };

      // Definir endpoint baseado no tipo de usuário
    switch (userType) {
      case 'superadmin':
        endpoint = '/auth/superadmin/login/';
          payload.cpf_cnpj = credentials.cpf_cnpj;
        break;
      case 'suporte':
        endpoint = '/auth/suporte/login/';
          payload.cpf_cnpj = credentials.cpf_cnpj;
        break;
      case 'loja':
          if (!slug) {
            throw new Error('Slug da loja é obrigatório');
          }
        endpoint = '/auth/loja/login/';
          payload.loja_slug = slug;
          payload.cpf_cnpj = credentials.cpf_cnpj;
        break;
        default:
          throw new Error('Tipo de usuário inválido');
      }

      const response = await apiClient.post(endpoint, payload);
      const data: LoginResponse = response.data;

      // user_type/loja_slug podem vir no topo ou dentro de user/loja (compatível com backend antigo)
      const responseUserType = data.user_type ?? (data as any).user?.user_type;
      const lojaSlug = data.loja_slug ?? (data as any).loja?.slug;
      const lojaId = (data as any).loja?.id;

      console.log('✅ Login bem-sucedido:', {
        user_type: responseUserType,
        loja_slug: lojaSlug,
        loja_id: lojaId,
        precisa_trocar_senha: data.precisa_trocar_senha
      });

      // Salvar tokens e informações do usuário no sessionStorage
      this.setToken(data.access);
      this.setRefreshToken(data.refresh);
      if (responseUserType) this.setUserType(responseUserType);
      if (lojaSlug) this.setLojaSlug(lojaSlug);
      if (typeof window !== 'undefined' && lojaId) {
        sessionStorage.setItem('current_loja_id', String(lojaId));
      }
      if ((data as any).is_vendedor === true) {
        sessionStorage.setItem('is_vendedor', '1');
      } else {
        sessionStorage.removeItem('is_vendedor');
      }

      // Salvar session_id se vier do backend
      if (typeof window !== 'undefined' && (data as any).session_id) {
        sessionStorage.setItem('session_id', (data as any).session_id);
      }

      // Também salvar nos cookies para o middleware (só se tiver responseUserType)
      if (typeof document !== 'undefined' && responseUserType) {
        const cookieOptions = 'path=/; max-age=86400; SameSite=Lax'; // 24 horas
        document.cookie = `user_type=${responseUserType}; ${cookieOptions}`;
        if (lojaSlug) {
          document.cookie = `loja_slug=${lojaSlug}; ${cookieOptions}`;
        }
        console.log('🍪 Cookies definidos:', {
          user_type: responseUserType,
          loja_slug: lojaSlug
        });
      }

      return data;
    } catch (error: any) {
      console.error('Erro no login:', error);
      
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else if (error.message) {
        throw new Error(error.message);
      } else {
        throw new Error('Erro ao fazer login. Tente novamente.');
      }
    }
  }

  /**
   * Realiza logout do sistema
   */
  logout(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem(this.TOKEN_KEY);
      sessionStorage.removeItem(this.REFRESH_KEY);
      sessionStorage.removeItem(this.USER_TYPE_KEY);
      sessionStorage.removeItem(this.LOJA_SLUG_KEY);
      sessionStorage.removeItem('is_vendedor');
      sessionStorage.removeItem(this.INTERNAL_NAV_KEY);
      localStorage.removeItem('token');
      
      // Limpar cookies também
      if (typeof document !== 'undefined') {
        document.cookie = 'user_type=; path=/; max-age=0';
        document.cookie = 'loja_slug=; path=/; max-age=0';
        document.cookie = 'loja_usa_crm=; path=/; max-age=0';
      }
    }
  }

  /**
   * Verifica se o usuário está autenticado
   */
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  /**
   * Obtém o token de acesso
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return sessionStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Define o token de acesso (sessionStorage + localStorage para abas novas)
   */
  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(this.TOKEN_KEY, token);
      localStorage.setItem('token', token);
    }
  }

  /**
   * Obtém o refresh token
   */
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return sessionStorage.getItem(this.REFRESH_KEY);
  }

  /**
   * Define o refresh token
   */
  setRefreshToken(token: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(this.REFRESH_KEY, token);
    }
  }

  /**
   * Obtém o tipo de usuário
   */
  getUserType(): UserType | null {
    if (typeof window === 'undefined') return null;
    return sessionStorage.getItem(this.USER_TYPE_KEY) as UserType | null;
  }

  /**
   * Define o tipo de usuário
   */
  setUserType(userType: UserType): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(this.USER_TYPE_KEY, userType);
    }
  }

  /**
   * Verifica se o usuário é vendedor (grupo vendedor do CRM)
   */
  isVendedor(): boolean {
    if (typeof window === 'undefined') return false;
    return sessionStorage.getItem('is_vendedor') === '1';
  }

  /**
   * Obtém o slug da loja
   */
  getLojaSlug(): string | null {
    if (typeof window === 'undefined') return null;
    return sessionStorage.getItem(this.LOJA_SLUG_KEY);
  }

  /**
   * Define o slug da loja
   */
  setLojaSlug(slug: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(this.LOJA_SLUG_KEY, slug);
    }
  }

  /**
   * Verifica se é navegação interna (para evitar logout em redirects)
   */
  isInternalNavigation(): boolean {
    if (typeof window === 'undefined') return false;
    return sessionStorage.getItem(this.INTERNAL_NAV_KEY) === 'true';
  }

  /**
   * Marca como navegação interna
   */
  markInternalNavigation(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(this.INTERNAL_NAV_KEY, 'true');
      // Remove após 2 segundos
      setTimeout(() => {
        sessionStorage.removeItem(this.INTERNAL_NAV_KEY);
      }, 2000);
    }
  }
}

// Exportar instância única
export const authService = new AuthService();

// Exportar função helper para marcar navegação interna
export const markInternalNavigation = () => authService.markInternalNavigation();

// Exportar função helper para obter URL de login baseado no tipo de usuário
export const getLoginUrl = (userType?: UserType, slug?: string): string => {
  switch (userType) {
    case 'superadmin':
      return '/superadmin/login';
    case 'suporte':
      return '/suporte/login';
    case 'loja':
      return slug ? `/loja/${slug}/login` : '/';
    default:
      return '/';
  }
};
