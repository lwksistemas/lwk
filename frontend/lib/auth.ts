import apiClient from './api-client';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  session_id?: string;
  session_timeout_minutes?: number;
  user?: {
    id: number;
    username: string;
    email: string;
    is_superuser: boolean;
  };
}

export type UserType = 'superadmin' | 'suporte' | 'loja';

// Configuração de timeout de inatividade (30 minutos)
const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutos em milissegundos
let inactivityTimer: NodeJS.Timeout | null = null;

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
      
      const { access, refresh, session_id, session_timeout_minutes, user } = response.data;
      
      if (!access || !refresh) {
        console.error('Tokens inválidos recebidos:', { access: !!access, refresh: !!refresh });
        throw new Error('Tokens inválidos recebidos do servidor');
      }
      
      // Salvar no localStorage
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_type', userType);
      
      if (session_id) {
        localStorage.setItem('session_id', session_id);
      }
      
      if (lojaSlug) {
        localStorage.setItem('loja_slug', lojaSlug);
      }
      
      // Salvar também nos cookies para o middleware do Next.js
      // Usar Secure apenas em produção (HTTPS)
      const isProduction = window.location.protocol === 'https:';
      const secureFlag = isProduction ? '; Secure' : '';
      const cookieOptions = `path=/; max-age=86400; SameSite=Lax${secureFlag}`;
      
      document.cookie = `user_type=${userType}; ${cookieOptions}`;
      
      if (lojaSlug) {
        document.cookie = `loja_slug=${lojaSlug}; ${cookieOptions}`;
      }
      
      console.log('✅ Tokens e cookies salvos:', {
        userType,
        lojaSlug: lojaSlug || 'N/A',
        isProduction,
        cookies: document.cookie
      });
      console.log(`Sessão criada: ${session_id}, timeout: ${session_timeout_minutes} minutos`);
      
      // Iniciar monitoramento de inatividade
      authService.startInactivityMonitor();
      
      // Verificar se os tokens foram realmente salvos
      const savedAccess = localStorage.getItem('access_token');
      const savedRefresh = localStorage.getItem('refresh_token');
      console.log('Verificação tokens salvos:', { 
        access: savedAccess ? 'OK' : 'FALHOU', 
        refresh: savedRefresh ? 'OK' : 'FALHOU' 
      });
      
      return response.data;
    } catch (error: any) {
      console.error('Erro no AuthService.login:', error);
      
      // Verificar se é erro de sessão conflitante
      if (error.response?.data?.code === 'SESSION_CONFLICT') {
        throw new Error('Você já está logado em outro dispositivo. Faça logout lá primeiro.');
      }
      
      throw error;
    }
  },

  async logout() {
    try {
      // Chamar endpoint de logout no backend
      await apiClient.post('/auth/logout/');
    } catch (error) {
      console.error('Erro ao fazer logout no backend:', error);
    }
    
    // Limpar localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('loja_slug');
    localStorage.removeItem('session_id');
    
    // Limpar cookies
    document.cookie = 'user_type=; path=/; max-age=0';
    document.cookie = 'loja_slug=; path=/; max-age=0';
    
    // Parar monitoramento de inatividade
    authService.stopInactivityMonitor();
  },

  forceLogout(reason?: string) {
    console.log('🚨 FORCE LOGOUT:', reason);
    
    // Limpar tudo
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('loja_slug');
    localStorage.removeItem('session_id');
    
    document.cookie = 'user_type=; path=/; max-age=0';
    document.cookie = 'loja_slug=; path=/; max-age=0';
    
    authService.stopInactivityMonitor();
    
    // Redirecionar para home
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  },

  startInactivityMonitor() {
    // Limpar timer anterior se existir
    authService.stopInactivityMonitor();
    
    // Função para resetar o timer
    const resetTimer = () => {
      if (inactivityTimer) {
        clearTimeout(inactivityTimer);
      }
      
      inactivityTimer = setTimeout(() => {
        console.log('⏰ Timeout de inatividade atingido (30 minutos)');
        authService.forceLogout('Sessão expirou por inatividade');
      }, INACTIVITY_TIMEOUT);
    };
    
    // Eventos que indicam atividade do usuário
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    events.forEach(event => {
      document.addEventListener(event, resetTimer, true);
    });
    
    // Iniciar o timer
    resetTimer();
    
    console.log('✅ Monitoramento de inatividade iniciado (30 minutos)');
  },

  stopInactivityMonitor() {
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
      inactivityTimer = null;
    }
    
    // Remover event listeners
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    const resetTimer = () => {}; // Função vazia para remover
    
    events.forEach(event => {
      document.removeEventListener(event, resetTimer, true);
    });
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

  getSessionId(): string | null {
    return localStorage.getItem('session_id');
  },
};
