import axios from 'axios';
import { logger } from './logger';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cliente específico para APIs da clínica (sem autenticação)
export const clinicaApiClient = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - adiciona token JWT
apiClient.interceptors.request.use(
  (config) => {
    // Não enviar token para APIs da clínica (elas usam AllowAny)
    if (!config.url?.includes('/clinica/')) {
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
        
        // Limpar tudo IMEDIATAMENTE
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_type');
        localStorage.removeItem('loja_slug');
        localStorage.removeItem('session_id');
        
        document.cookie = 'user_type=; path=/; max-age=0';
        document.cookie = 'loja_slug=; path=/; max-age=0';
        
        // Mostrar mensagem ao usuário
        const message = typeof errorMessage === 'string' 
          ? errorMessage 
          : 'Outra sessão foi iniciada em outro dispositivo. Você foi desconectado.';
        
        alert(message);
        window.location.href = '/';
        return Promise.reject(error);
      }
      
      // APENAS tentar refresh token se NÃO for erro de sessão
      if (!originalRequest._retry) {
        originalRequest._retry = true;

        try {
          logger.log('🔄 Tentando refresh token...');
          const refreshToken = localStorage.getItem('refresh_token');
          
          if (!refreshToken) {
            logger.log('❌ Sem refresh token');
            localStorage.clear();
            window.location.href = '/';
            return Promise.reject(error);
          }
          
          const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          logger.log('✅ Refresh token bem-sucedido');
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          logger.error('❌ Refresh token falhou:', refreshError);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/';
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
