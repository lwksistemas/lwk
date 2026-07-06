/**
 * Serviço de Autenticação
 * Sistema multi-tenant com suporte a SuperAdmin, Suporte e Lojas
 * Versão: 2.0 - Corrigido para usar sessionStorage e cookies
 */

import apiClient from './api-client';
import { clearAssinaturaAvisoDismissKeys } from '@/lib/assinatura-aviso';
import { clearStoreBlockedMark } from '@/lib/loja-bloqueio-inadimplencia';
import { syncCrmPermissoesSession } from '@/lib/crm-permissoes';
import { USE_JWT_HTTPONLY_COOKIES } from './auth-cookies';

export type UserType = 'superadmin' | 'suporte' | 'loja';

interface LoginCredentials {
  username: string;
  password: string;
  cpf_cnpj?: string;
  otp_code?: string;
  backup_code?: string;
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
      let payload: Record<string, string> = {
        username: credentials.username,
        password: credentials.password,
      };
      if (credentials.otp_code?.trim()) {
        payload.otp_code = credentials.otp_code.trim();
      }
      if (credentials.backup_code?.trim()) {
        payload.backup_code = credentials.backup_code.trim();
      }

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

      // Limpar flags de vendedor ANTES de processar novo login
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('is_vendedor');
        sessionStorage.removeItem('current_vendedor_id');
      }

      if (!USE_JWT_HTTPONLY_COOKIES) {
        this.setToken(data.access);
        this.setRefreshToken(data.refresh);
      }
      if (responseUserType) this.setUserType(responseUserType);
      if (lojaSlug) this.setLojaSlug(lojaSlug);
      if (typeof window !== 'undefined' && lojaId) {
        sessionStorage.setItem('current_loja_id', String(lojaId));
      }
      
      // Só setar is_vendedor se vier EXPLICITAMENTE como true do backend
      if ((data as any).is_vendedor === true) {
        sessionStorage.setItem('is_vendedor', '1');
        if (typeof (data as any).vendedor_id === 'number') {
          sessionStorage.setItem('current_vendedor_id', String((data as any).vendedor_id));
        }
      }
      
      // Setar is_gerente se vier do backend
      if ((data as any).is_gerente === true) {
        sessionStorage.setItem('is_gerente', '1');
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
      }

      return data;
    } catch (error: any) {
      const data = error.response?.data;
      if (data?.mfa_required || data?.code === 'MFA_REQUIRED') {
        const err = new Error(data.error || 'Informe o código do autenticador.');
        (err as Error & { mfaRequired?: boolean }).mfaRequired = true;
        throw err;
      }
      if (data?.code === 'ACCOUNT_LOCKED') {
        throw new Error(data.error || 'Conta temporariamente bloqueada. Tente mais tarde.');
      }
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
      try {
        apiClient.post('/auth/logout/').catch(() => {});
      } catch {
        /* ignore */
      }

      sessionStorage.removeItem(this.TOKEN_KEY);
      sessionStorage.removeItem(this.REFRESH_KEY);
      sessionStorage.removeItem(this.USER_TYPE_KEY);
      sessionStorage.removeItem(this.LOJA_SLUG_KEY);
      sessionStorage.removeItem('is_vendedor');
      sessionStorage.removeItem('is_gerente');
      sessionStorage.removeItem('current_vendedor_id');
      sessionStorage.removeItem(this.INTERNAL_NAV_KEY);
      sessionStorage.removeItem('current_loja_id');
      sessionStorage.removeItem('session_id');
      sessionStorage.removeItem('crm_acesso_total');
      sessionStorage.removeItem('crm_permissoes');
      sessionStorage.removeItem('crm_permissoes_synced');
      clearAssinaturaAvisoDismissKeys();
      clearStoreBlockedMark();
      
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
   * Define o token de acesso (apenas sessionStorage — sem persistência em localStorage)
   */
  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(this.TOKEN_KEY, token);
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
   * Verifica se o usuário é Gerente de Vendas (tem acesso completo como owner)
   */
  isGerente(): boolean {
    if (typeof window === 'undefined') return false;
    return sessionStorage.getItem('is_gerente') === '1';
  }

  /**
   * Verifica se o usuário é owner (administrador da loja)
   * Owner nunca é marcado como vendedor, mesmo se tiver grupo Gerente de Vendas
   */
  isOwner(): boolean {
    if (typeof window === 'undefined') return false;
    // Se não é vendedor, é owner (administrador)
    return sessionStorage.getItem('is_vendedor') !== '1';
  }

  /**
   * Verifica se o usuário tem acesso administrativo completo
   * (Owner ou Gerente de Vendas)
   */
  hasAdminAccess(): boolean {
    return this.isOwner() || this.isGerente();
  }

  /**
   * Sincroniza sessionStorage com GET /crm-vendas/me/.
   * Deve remover is_vendedor quando o backend retorna false (ex.: dono da loja com vínculo de vendedor),
   * senão um valor antigo esconde NFS-e, backup, etc. na tela de configurações.
   */
  syncCrmMeFlags(d: {
    is_vendedor?: boolean;
    vendedor_id?: number | null;
    acesso_total?: boolean;
    permissoes?: string[];
  }): void {
    if (typeof window === 'undefined') return;
    if (d.is_vendedor === true && typeof d.vendedor_id === 'number') {
      sessionStorage.setItem('is_vendedor', '1');
      sessionStorage.setItem('current_vendedor_id', String(d.vendedor_id));
    } else {
      sessionStorage.removeItem('is_vendedor');
      if (typeof d.vendedor_id === 'number') {
        sessionStorage.setItem('current_vendedor_id', String(d.vendedor_id));
      } else {
        sessionStorage.removeItem('current_vendedor_id');
      }
    }
    syncCrmPermissoesSession({
      acesso_total: d.acesso_total,
      permissoes: d.permissoes,
    });
  }

  /**
   * Obtém o ID do vendedor logado (quando is_vendedor=true).
   * Usado para associar oportunidades/leads ao vendedor ao criar.
   */
  getVendedorId(): number | null {
    if (typeof window === 'undefined') return null;
    const id = sessionStorage.getItem('current_vendedor_id');
    if (!id) return null;
    const n = parseInt(id, 10);
    return Number.isNaN(n) ? null : n;
  }

  /**
   * Define o ID do vendedor logado.
   * Usado para sincronizar vendedor_id com backend após login ou criação de oportunidade.
   * 
   * IMPORTANTE: NÃO seta is_vendedor=1 se o usuário já for owner.
   * Owner pode ter vendedor_id (para fazer vendas) mas continua sendo owner (acesso total).
   */
  setVendedorId(vendedorId: number): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('current_vendedor_id', String(vendedorId));
      // Só marca como vendedor se NÃO for owner
      // Owner já tem is_vendedor !== '1' do login
      const isAlreadyVendedor = sessionStorage.getItem('is_vendedor') === '1';
      if (isAlreadyVendedor) {
        // Já é vendedor, mantém
        sessionStorage.setItem('is_vendedor', '1');
      }
      // Se não é vendedor (owner), NÃO seta is_vendedor
    }
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

/** Alinha sessionStorage e cookie com o slug da URL (middleware + RouteGuard). */
export function syncLojaTenantSlug(slug: string): void {
  if (typeof window === 'undefined' || !slug?.trim()) return;
  const s = slug.trim();
  const stored = authService.getLojaSlug();
  if (stored === s) return;
  authService.setLojaSlug(s);
  document.cookie = `loja_slug=${encodeURIComponent(s)}; path=/; max-age=86400; SameSite=Lax`;
}

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
