import apiClient, { startHeartbeat, stopHeartbeat } from './api-client';
import { logger } from './logger';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  session_id?: string;
  session_timeout_minutes?: number;
  precisa_trocar_senha?: boolean;
  user?: {
    id: number;
    username: string;
    email: string;
    is_superuser: boolean;
    user_type?: string;
  };
  loja?: {
    id: number;
    slug: string;
    nome: string;
    tipo_loja?: string;
  };
}

export type UserType = 'superadmin' | 'suporte' | 'loja';

// Configuração de timeout de inatividade (60 minutos = 1 hora)
const INACTIVITY_TIMEOUT = 60 * 60 * 1000;
let inactivityTimer: NodeJS.Timeout | null = null;
let resetTimerFn: (() => void) | null = null;

// Handlers para logout ao fechar aba
let beforeUnloadHandler: ((e: BeforeUnloadEvent) => void) | null = null;
let pageHideHandler: ((e: PageTransitionEvent) => void) | null = null;

// URL da API para logout via beacon
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Flag para saber se está no meio de navegação interna
let navigationInProgress = false;

/**
 * Retorna a URL de login correta baseada no tipo de usuário
 * Deve ser chamada ANTES de limpar a sessão
 */
export function getLoginUrl(): string {
  const userType = sessionStorage.getItem('user_type');
  const lojaSlug = sessionStorage.getItem('loja_slug');
  
  switch (userType) {
    case 'superadmin':
      return '/superadmin/login';
    case 'suporte':
      return '/suporte/login';
    case 'loja':
      return lojaSlug ? `/loja/${lojaSlug}/login` : '/';
    default:
      return '/';
  }
}

/**
 * Limpa toda a sessão do usuário
 * Centraliza a lógica de limpeza para evitar duplicação
 */
function clearSession() {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
  sessionStorage.removeItem('user_type');
  sessionStorage.removeItem('loja_slug');
  sessionStorage.removeItem('session_id');
  sessionStorage.removeItem('current_loja_id');
  
  document.cookie = 'user_type=; path=/; max-age=0';
  document.cookie = 'loja_slug=; path=/; max-age=0';
}

/**
 * Faz logout via sendBeacon (funciona ao fechar aba)
 * sendBeacon é a única forma confiável de enviar dados ao fechar a página
 */
function logoutViaBeacon() {
  // Não fazer logout se navegação interna está em progresso
  if (navigationInProgress) {
    logger.log('🔄 Navegação interna em progresso - NÃO fazer logout');
    return;
  }
  
  const accessToken = sessionStorage.getItem('access_token');
  
  if (accessToken) {
    logger.log('🚪 Logout via beacon (aba sendo fechada)');
    
    // Usar sendBeacon para garantir que a requisição seja enviada
    const logoutUrl = `${API_URL}/api/auth/logout/beacon/`;
    const data = JSON.stringify({ token: accessToken });
    
    const sent = navigator.sendBeacon(logoutUrl, new Blob([data], { type: 'application/json' }));
    
    if (sent) {
      logger.log('✅ Beacon de logout enviado');
    } else {
      logger.error('❌ Falha ao enviar beacon de logout');
    }
    
    clearSession();
  }
}

/**
 * Marca o início de uma navegação interna
 * Deve ser chamado ANTES de qualquer window.location ou router.push
 */
export function markInternalNavigation() {
  navigationInProgress = true;
  logger.log('🔄 Navegação interna marcada');
  
  // Auto-reset após 5 segundos (caso a navegação falhe)
  setTimeout(() => {
    navigationInProgress = false;
  }, 5000);
}

/**
 * Registra os handlers para logout ao fechar aba
 * Usa 'pagehide' que é o evento mais confiável para detectar fechamento
 */
function registerCloseHandlers() {
  unregisterCloseHandlers();
  
  // pagehide é mais confiável que beforeunload
  pageHideHandler = (e: PageTransitionEvent) => {
    // persisted === true significa que a página pode ser restaurada (back/forward cache)
    // persisted === false significa que a página está sendo descarregada definitivamente
    if (!e.persisted) {
      logoutViaBeacon();
    }
  };
  
  window.addEventListener('pagehide', pageHideHandler);
  logger.log('✅ Handler de logout ao fechar aba registrado');
}

/**
 * Remove os handlers de logout
 */
function unregisterCloseHandlers() {
  if (pageHideHandler) {
    window.removeEventListener('pagehide', pageHideHandler);
    pageHideHandler = null;
  }
  if (beforeUnloadHandler) {
    window.removeEventListener('beforeunload', beforeUnloadHandler);
    beforeUnloadHandler = null;
  }
  logger.log('🗑️ Handlers de logout removidos');
}

export const authService = {
  async login(credentials: LoginCredentials, userType: UserType = 'superadmin', lojaSlug?: string): Promise<AuthTokens> {
    logger.log('AuthService.login:', { username: credentials.username, userType, lojaSlug });
    
    // Verificar se sessionStorage está disponível (sessão encerra ao fechar aba/navegador)
    if (typeof window === 'undefined' || !window.sessionStorage) {
      logger.error('sessionStorage não está disponível');
      throw new Error('sessionStorage não está disponível');
    }
    
    // Determinar endpoint correto baseado no tipo de usuário
    let endpoint = '/auth/token/';
    
    switch (userType) {
      case 'superadmin':
        endpoint = '/auth/superadmin/login/';
        break;
      case 'suporte':
        endpoint = '/auth/suporte/login/';
        break;
      case 'loja':
        endpoint = '/auth/loja/login/';
        break;
    }
    
    logger.log(`🔐 Endpoint: ${endpoint}`);
    
    try {
      // Preparar dados de login
      const loginData: any = { ...credentials };
      
      // Se for loja, adicionar slug
      if (userType === 'loja' && lojaSlug) {
        loginData.loja_slug = lojaSlug;
      }
      
      const response = await apiClient.post<AuthTokens>(endpoint, loginData);
      logger.log('Login response:', response.status);
      
      const { access, refresh, session_id, session_timeout_minutes, user, loja } = response.data;
      
      if (!access || !refresh) {
        logger.error('Tokens inválidos:', { access: !!access, refresh: !!refresh });
        throw new Error('Tokens inválidos recebidos do servidor');
      }
      
      // Validar que o user_type retornado corresponde ao esperado
      if (user && user.user_type && user.user_type !== userType) {
        logger.critical(`Tipo de usuário não corresponde! Esperado: ${userType}, Recebido: ${user.user_type}`);
        throw new Error(`Este usuário não pode fazer login aqui. Use o login de ${user.user_type}.`);
      }
      
      // Salvar no sessionStorage (sessão encerra ao fechar aba/navegador)
      sessionStorage.setItem('access_token', access);
      sessionStorage.setItem('refresh_token', refresh);
      sessionStorage.setItem('user_type', userType);
      
      if (session_id) {
        sessionStorage.setItem('session_id', session_id);
      }
      
      // Se for loja, salvar slug
      if (userType === 'loja') {
        const slugToSave = loja?.slug || lojaSlug;
        if (slugToSave) {
          sessionStorage.setItem('loja_slug', slugToSave);
        }
      }
      
      // Salvar também nos cookies para o middleware do Next.js
      const isProduction = window.location.protocol === 'https:';
      const secureFlag = isProduction ? '; Secure' : '';
      const cookieOptions = `path=/; max-age=86400; SameSite=Lax${secureFlag}`;
      
      document.cookie = `user_type=${userType}; ${cookieOptions}`;
      
      if (userType === 'loja') {
        const slugToSave = loja?.slug || lojaSlug;
        if (slugToSave) {
          document.cookie = `loja_slug=${slugToSave}; ${cookieOptions}`;
        }
      }
      
      logger.log('✅ Sessão criada:', { userType, session_id, timeout: session_timeout_minutes });
      
      // Verificar se precisa trocar senha ANTES de iniciar heartbeat
      const precisaTrocarSenha = response.data.precisa_trocar_senha === true;
      logger.log('🔑 precisa_trocar_senha:', precisaTrocarSenha);
      
      // Só iniciar heartbeat se NÃO precisar trocar senha
      if (!precisaTrocarSenha) {
        // Iniciar monitoramento de inatividade (1 hora)
        authService.startInactivityMonitor();
        
        // Iniciar heartbeat para manter sessão ativa
        startHeartbeat();
        
        // Registrar logout ao fechar aba (após delay para permitir redirect)
        setTimeout(() => {
          registerCloseHandlers();
        }, 3000);
      }
      
      // Marcar navegação interna para o redirect que virá
      markInternalNavigation();
      
      return response.data;
    } catch (error: any) {
      logger.error('Erro no login:', error);
      
      // Verificar se é erro de sessão conflitante
      if (error.response?.data?.code === 'SESSION_CONFLICT') {
        throw new Error('Você já está logado em outro dispositivo. Faça logout lá primeiro.');
      }
      
      // Verificar se é erro de endpoint errado
      if (error.response?.data?.code === 'WRONG_LOGIN_ENDPOINT') {
        const correctEndpoint = error.response.data.endpoint_correto;
        const seuTipo = error.response.data.seu_tipo;
        throw new Error(`Este usuário é do tipo "${seuTipo}". Use o login correto.`);
      }
      
      // Verificar se é erro de loja errada
      if (error.response?.data?.code === 'WRONG_STORE') {
        const suaLoja = error.response.data.sua_loja;
        throw new Error(`Você não pode fazer login nesta loja. Sua loja é: ${suaLoja}`);
      }
      
      // Verificar se é erro de credenciais inválidas (401)
      if (error.response?.status === 401) {
        throw new Error('❌ Usuário ou senha incorretos. Verifique suas credenciais e tente novamente.');
      }
      
      // Verificar se há mensagem de erro específica
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      }
      
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      
      throw error;
    }
  },

  async logout() {
    // Remover handler de fechar aba ANTES do logout
    unregisterCloseHandlers();
    
    try {
      await apiClient.post('/auth/logout/');
    } catch (error) {
      logger.error('Erro ao fazer logout:', error);
    }
    
    clearSession();
    authService.stopInactivityMonitor();
    stopHeartbeat();
  },

  forceLogout(reason?: string) {
    logger.critical('FORCE LOGOUT:', reason);
    
    // Obter URL de login ANTES de limpar a sessão
    const loginUrl = getLoginUrl();
    
    // Remover handlers e marcar navegação
    unregisterCloseHandlers();
    markInternalNavigation();
    
    clearSession();
    authService.stopInactivityMonitor();
    stopHeartbeat();
    
    if (typeof window !== 'undefined') {
      window.location.href = loginUrl;
    }
  },

  startInactivityMonitor() {
    authService.stopInactivityMonitor();
    
    resetTimerFn = () => {
      if (inactivityTimer) {
        clearTimeout(inactivityTimer);
      }
      
      inactivityTimer = setTimeout(() => {
        logger.log('⏰ Timeout de inatividade (1 hora)');
        authService.forceLogout('Sessão expirou por inatividade (1 hora sem usar)');
      }, INACTIVITY_TIMEOUT);
    };
    
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
      document.addEventListener(event, resetTimerFn!, true);
    });
    
    resetTimerFn();
    logger.log('✅ Monitoramento de inatividade iniciado');
  },

  stopInactivityMonitor() {
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
      inactivityTimer = null;
    }
    
    if (resetTimerFn) {
      const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
      events.forEach(event => {
        document.removeEventListener(event, resetTimerFn!, true);
      });
      resetTimerFn = null;
    }
  },

  isAuthenticated(): boolean {
    return !!sessionStorage.getItem('access_token');
  },

  getAccessToken(): string | null {
    return sessionStorage.getItem('access_token');
  },

  getUserType(): UserType | null {
    return sessionStorage.getItem('user_type') as UserType | null;
  },

  getLojaSlug(): string | null {
    return sessionStorage.getItem('loja_slug');
  },

  getSessionId(): string | null {
    return sessionStorage.getItem('session_id');
  },
};
