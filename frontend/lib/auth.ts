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

// Handler para logout ao fechar aba
let beforeUnloadHandler: ((e: BeforeUnloadEvent) => void) | null = null;

// URL da API para logout via beacon
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Limpa toda a sessão do usuário
 * Centraliza a lógica de limpeza para evitar duplicação
 */
function clearSession() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_type');
  localStorage.removeItem('loja_slug');
  localStorage.removeItem('session_id');
  
  document.cookie = 'user_type=; path=/; max-age=0';
  document.cookie = 'loja_slug=; path=/; max-age=0';
}

/**
 * Faz logout via sendBeacon (funciona ao fechar aba)
 * sendBeacon é a única forma confiável de enviar dados ao fechar a página
 */
function logoutViaBeacon() {
  const accessToken = localStorage.getItem('access_token');
  
  if (accessToken) {
    logger.log('🚪 Logout via beacon (aba sendo fechada)');
    
    // Usar sendBeacon para garantir que a requisição seja enviada
    // mesmo quando a página está sendo fechada
    const logoutUrl = `${API_URL}/api/auth/logout/beacon/`;
    const data = JSON.stringify({ token: accessToken });
    
    // sendBeacon retorna true se a requisição foi aceita para envio
    const sent = navigator.sendBeacon(logoutUrl, new Blob([data], { type: 'application/json' }));
    
    if (sent) {
      logger.log('✅ Beacon de logout enviado');
    } else {
      logger.error('❌ Falha ao enviar beacon de logout');
    }
    
    // Limpar sessão localmente
    clearSession();
  }
}

/**
 * Registra o handler para logout ao fechar aba
 */
function registerBeforeUnloadHandler() {
  // Remover handler anterior se existir
  unregisterBeforeUnloadHandler();
  
  beforeUnloadHandler = (e: BeforeUnloadEvent) => {
    logoutViaBeacon();
  };
  
  window.addEventListener('beforeunload', beforeUnloadHandler);
  logger.log('✅ Handler de logout ao fechar aba registrado');
}

/**
 * Remove o handler de logout ao fechar aba
 */
function unregisterBeforeUnloadHandler() {
  if (beforeUnloadHandler) {
    window.removeEventListener('beforeunload', beforeUnloadHandler);
    beforeUnloadHandler = null;
    logger.log('🗑️ Handler de logout ao fechar aba removido');
  }
}

export const authService = {
  async login(credentials: LoginCredentials, userType: UserType = 'superadmin', lojaSlug?: string): Promise<AuthTokens> {
    logger.log('AuthService.login:', { username: credentials.username, userType, lojaSlug });
    
    // Verificar se localStorage está disponível
    if (typeof window === 'undefined' || !window.localStorage) {
      logger.error('localStorage não está disponível');
      throw new Error('localStorage não está disponível');
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
      
      // Salvar no localStorage
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_type', userType);
      
      if (session_id) {
        localStorage.setItem('session_id', session_id);
      }
      
      // Se for loja, salvar slug
      if (userType === 'loja') {
        const slugToSave = loja?.slug || lojaSlug;
        if (slugToSave) {
          localStorage.setItem('loja_slug', slugToSave);
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
        
        // Registrar logout ao fechar aba
        registerBeforeUnloadHandler();
      }
      
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
      
      throw error;
    }
  },

  async logout() {
    // Remover handler de fechar aba ANTES do logout
    // para evitar duplo logout
    unregisterBeforeUnloadHandler();
    
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
    
    // Remover handler de fechar aba
    unregisterBeforeUnloadHandler();
    
    clearSession();
    authService.stopInactivityMonitor();
    stopHeartbeat();
    
    if (typeof window !== 'undefined') {
      window.location.href = '/';
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
