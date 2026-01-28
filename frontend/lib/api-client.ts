import axios from 'axios';
import { logger } from './logger';
import { getLoginUrl } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cliente específico para APIs da clínica (COM autenticação e X-Loja-ID)
export const clinicaApiClient = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar X-Loja-ID e token JWT
clinicaApiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      // Adicionar X-Loja-ID
      const lojaId = localStorage.getItem('current_loja_id');
      if (lojaId) {
        config.headers['X-Loja-ID'] = lojaId;
        logger.log('🏪 [clinicaApiClient] Adicionando X-Loja-ID:', lojaId);
      }
      
      // Adicionar token JWT para validação de sessão
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    logger.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    logger.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor para clinicaApiClient - trata erros de sessão
clinicaApiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Verificar erros de sessão
    if (error.response?.status === 401) {
      const errorCode = error.response?.data?.code;
      
      if (errorCode === 'DIFFERENT_SESSION' || 
          errorCode === 'NO_SESSION' || 
          errorCode === 'TIMEOUT') {
        
        logger.critical('🚨 Sessão inválida na API clínica:', errorCode);
        
        // Obter URL de login ANTES de limpar
        const loginUrl = getLoginUrl();
        
        // Limpar sessão
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_type');
        localStorage.removeItem('loja_slug');
        localStorage.removeItem('session_id');
        localStorage.removeItem('current_loja_id');
        
        document.cookie = 'user_type=; path=/; max-age=0';
        document.cookie = 'loja_slug=; path=/; max-age=0';
        
        alert(error.response?.data?.message || 'Sua sessão expirou. Faça login novamente.');
        window.location.href = loginUrl;
      }
    }
    return Promise.reject(error);
  }
);

// Request interceptor - adiciona token JWT
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    logger.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    logger.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - refresh token automático e controle de sessão
apiClient.interceptors.response.use(
  (response) => {
    logger.log('API Response:', response.status, response.config.url);
    return response;
  },
  async (error) => {
    logger.error('API Error:', error.response?.status, error.response?.data?.code);
    const originalRequest = error.config;

    // Verificar erros de sessão PRIMEIRO (antes de tentar refresh)
    if (error.response?.status === 401) {
      const errorData = error.response?.data;
      const errorCode = errorData?.code || errorData?.detail?.code;
      const errorMessage = errorData?.message || errorData?.detail?.message || errorData?.detail;
      
      logger.log('🔍 Erro 401:', errorCode);
      
      // Erros de sessão que requerem logout forçado IMEDIATO
      if (errorCode === 'DIFFERENT_SESSION' || 
          errorCode === 'SESSION_CONFLICT' || 
          errorCode === 'TIMEOUT' ||
          errorCode === 'SESSION_TIMEOUT' || 
          errorCode === 'NO_SESSION') {
        
        logger.critical('SESSÃO INVÁLIDA - Logout forçado:', errorCode);
        
        // Obter URL de login ANTES de limpar
        const loginUrl = getLoginUrl();
        
        // Limpar tudo IMEDIATAMENTE
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_type');
        localStorage.removeItem('loja_slug');
        localStorage.removeItem('session_id');
        localStorage.removeItem('current_loja_id');
        
        document.cookie = 'user_type=; path=/; max-age=0';
        document.cookie = 'loja_slug=; path=/; max-age=0';
        
        // Mostrar mensagem ao usuário
        const message = typeof errorMessage === 'string' 
          ? errorMessage 
          : 'Outra sessão foi iniciada em outro dispositivo. Você foi desconectado.';
        
        alert(message);
        window.location.href = loginUrl;
        return Promise.reject(error);
      }
      
      // APENAS tentar refresh token se NÃO for erro de sessão
      if (!originalRequest._retry) {
        originalRequest._retry = true;

        try {
          logger.log('🔄 Tentando refresh token...');
          const refreshToken = localStorage.getItem('refresh_token');
          const accessToken = localStorage.getItem('access_token');
          
          if (!refreshToken) {
            logger.log('❌ Sem refresh token');
            const loginUrl = getLoginUrl();
            localStorage.clear();
            window.location.href = loginUrl;
            return Promise.reject(error);
          }
          
          // Enviar access token atual para validação de sessão única
          const response = await axios.post(
            `${API_URL}/api/auth/token/refresh/`, 
            { refresh: refreshToken },
            { 
              headers: accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}
            }
          );

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          logger.log('✅ Refresh token bem-sucedido');
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        } catch (refreshError: any) {
          logger.error('❌ Refresh token falhou:', refreshError);
          
          // Obter URL de login ANTES de limpar
          const loginUrl = getLoginUrl();
          
          // Verificar se é erro de sessão (outro login detectado)
          const errCode = refreshError.response?.data?.code;
          const errMessage = refreshError.response?.data?.message || refreshError.response?.data?.detail;
          
          if (errCode === 'DIFFERENT_SESSION' || errCode === 'NO_SESSION') {
            logger.critical('🚫 Sessão invalidada - outro login detectado');
            alert(errMessage || 'Sua sessão foi encerrada porque outro login foi detectado.');
          }
          
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user_type');
          localStorage.removeItem('loja_slug');
          localStorage.removeItem('session_id');
          localStorage.removeItem('current_loja_id');
          
          document.cookie = 'user_type=; path=/; max-age=0';
          document.cookie = 'loja_slug=; path=/; max-age=0';
          
          window.location.href = loginUrl;
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;

// ===== HEARTBEAT PARA MANTER SESSÃO ATIVA =====

let heartbeatInterval: NodeJS.Timeout | null = null;

/**
 * Inicia heartbeat automático para manter sessão ativa
 * Envia ping a cada 5 minutos para evitar timeout de inatividade
 */
export function startHeartbeat() {
  // Não iniciar se já estiver rodando
  if (heartbeatInterval) {
    logger.log('⚠️ Heartbeat já está rodando');
    return;
  }
  
  logger.log('💓 Iniciando heartbeat (ping a cada 5 minutos)');
  
  heartbeatInterval = setInterval(async () => {
    try {
      const response = await apiClient.get('/superadmin/lojas/heartbeat/');
      logger.log('💓 Heartbeat OK:', response.data);
    } catch (error: any) {
      logger.error('❌ Heartbeat falhou:', error);
      
      // Se falhar com 401, sessão expirou
      if (error.response?.status === 401) {
        logger.critical('🚨 Sessão expirou - Fazendo logout');
        
        // Obter URL de login ANTES de limpar
        const loginUrl = getLoginUrl();
        
        stopHeartbeat();
        
        // Limpar tudo
        localStorage.clear();
        document.cookie.split(";").forEach((c) => {
          document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });
        
        // Redirecionar para login específico do usuário
        window.location.href = loginUrl;
      }
    }
  }, 5 * 60 * 1000); // 5 minutos
}

/**
 * Para o heartbeat
 */
export function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
    logger.log('💔 Heartbeat parado');
  }
}
