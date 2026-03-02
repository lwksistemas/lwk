import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { logger } from './logger';
import { getLoginUrl } from './auth';

// ===== CONFIGURAÇÃO DE FAILOVER (v750) =====
const PRIMARY_API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BACKUP_API = process.env.NEXT_PUBLIC_API_BACKUP_URL;
const ENABLE_LOJA_FAILOVER = process.env.NEXT_PUBLIC_ENABLE_LOJA_FAILOVER === 'true';
const TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000');

// Controle de failover
let currentAPI = PRIMARY_API;
let failoverCount = 0;
let lastFailoverTime: number | null = null;
const MAX_FAILOVER_ATTEMPTS = 3;
const RECOVERY_TIME = 5 * 60 * 1000; // 5 minutos

const API_URL = currentAPI;
const API_BASE = API_URL.endsWith('/api') ? API_URL : `${API_URL}/api`;

const SESSION_CODES = [
  'DIFFERENT_SESSION', 'NO_SESSION', 'TIMEOUT',
  'SESSION_CONFLICT', 'SESSION_TIMEOUT',
] as const;

/** Limpa tokens/sessão e redireciona para login. Exportado para uso em fetch() (ex.: clinica-beleza). */
export function clearSessionAndRedirect(loginUrl: string, message?: string) {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
  sessionStorage.removeItem('user_type');
  sessionStorage.removeItem('loja_slug');
  sessionStorage.removeItem('session_id');
  sessionStorage.removeItem('current_loja_id');
  document.cookie = 'user_type=; path=/; max-age=0';
  document.cookie = 'loja_slug=; path=/; max-age=0';
  if (message && typeof window !== 'undefined') alert(message);
  if (typeof window !== 'undefined') window.location.href = loginUrl;
}

/** URL de login para redirecionar (usa storage antes de limpar). Exportado para uso em fetch(). */
export function getLoginUrlForRedirect(): string {
  if (typeof window === 'undefined') return '/';
  const userType = sessionStorage.getItem('user_type');
  const lojaSlug = sessionStorage.getItem('loja_slug');
  return getLoginUrl(userType as 'superadmin' | 'suporte' | 'loja' | undefined, lojaSlug || undefined);
}

/** Adiciona X-Loja-ID / X-Tenant-Slug e Authorization em todas as requisições de loja. */
function addLojaAuthHeaders(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  if (typeof window === 'undefined') return config;
  const lojaId = sessionStorage.getItem('current_loja_id');
  if (lojaId) {
    config.headers.set('X-Loja-ID', lojaId);
  } else {
    const lojaSlug = sessionStorage.getItem('loja_slug');
    if (lojaSlug) config.headers.set('X-Tenant-Slug', lojaSlug);
  }
  const token = sessionStorage.getItem('access_token');
  if (token) config.headers.set('Authorization', `Bearer ${token}`);
  logger.log('API Request:', config.method?.toUpperCase(), config.url);
  return config;
}

/** Trata 507 (limite de armazenamento). */
function handle507(error: { response?: { status?: number; data?: { error?: string } } }): boolean {
  if (error.response?.status === 507) {
    const msg = error.response?.data?.error || 'Limite de armazenamento da loja atingido. Entre em contato com o suporte.';
    if (typeof window !== 'undefined') alert(msg);
    return true;
  }
  return false;
}

/** Trata 401: sessão inválida (logout) ou refresh token e repete a requisição. */
async function handle401(
  error: { response?: { data?: { code?: string; message?: string; detail?: unknown } }; config?: { _retry?: boolean; headers?: { Authorization?: string }; url?: string } },
  apiInstance: AxiosInstance
): Promise<unknown> {
  const originalRequest = error.config;
  const errorData = error.response?.data;
  const errorCode = errorData?.code || (errorData?.detail as { code?: string })?.code;
  const errorMessage = errorData?.message || (errorData?.detail as { message?: string })?.message || errorData?.detail;

  // Se for erro de login (endpoints de autenticação), NÃO redirecionar
  // Deixar a página de login tratar o erro
  const isLoginEndpoint = originalRequest?.url?.includes('/login') || originalRequest?.url?.includes('/token');
  if (isLoginEndpoint) {
    logger.log('Erro 401 em endpoint de login - não redirecionar');
    return Promise.reject(error);
  }

  if (errorCode && SESSION_CODES.includes(errorCode as (typeof SESSION_CODES)[number])) {
    logger.critical('Sessão inválida:', errorCode);
    const loginUrl = getLoginUrlForRedirect();
    clearSessionAndRedirect(
      loginUrl,
      typeof errorMessage === 'string' ? errorMessage : 'Sua sessão expirou. Faça login novamente.'
    );
    return Promise.reject(error);
  }

  if (originalRequest && !originalRequest._retry) {
    originalRequest._retry = true;
    try {
      logger.log('Tentando refresh token...');
      const refreshToken = sessionStorage.getItem('refresh_token');
      const accessToken = sessionStorage.getItem('access_token');
      if (!refreshToken) {
        clearSessionAndRedirect(getLoginUrlForRedirect());
        return Promise.reject(error);
      }
      const response = await axios.post(
        `${API_BASE}/auth/token/refresh/`,
        { refresh: refreshToken },
        { headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {} }
      );
      const { access } = response.data;
      sessionStorage.setItem('access_token', access);
      originalRequest.headers = originalRequest.headers || {};
      originalRequest.headers.Authorization = `Bearer ${access}`;
      logger.log('Refresh OK, repetindo requisição');
      return apiInstance(originalRequest);
    } catch (refreshError: unknown) {
      logger.error('Refresh token falhou:', refreshError);
      const re = refreshError as { response?: { data?: { code?: string; message?: string; detail?: string } } };
      const errCode = re.response?.data?.code;
      const errMessage = re.response?.data?.message || re.response?.data?.detail;
      if (errCode === 'DIFFERENT_SESSION' || errCode === 'NO_SESSION') {
        alert(errMessage || 'Sua sessão foi encerrada. Faça login novamente.');
      }
      clearSessionAndRedirect(getLoginUrlForRedirect());
      return Promise.reject(refreshError);
    }
  }
  return Promise.reject(error);
}

/** Cria instância base (baseURL, timeout, JSON). */
function createApiInstance(): AxiosInstance {
  const baseURL = currentAPI.endsWith('/api') ? currentAPI : `${currentAPI}/api`;
  return axios.create({
    baseURL,
    headers: { 'Content-Type': 'application/json' },
    timeout: TIMEOUT,
  });
}

/** Aplica interceptors de loja (request: headers; response: 507 e 401+refresh). */
function applyLojaInterceptors(instance: AxiosInstance) {
  instance.interceptors.request.use(
    (config) => addLojaAuthHeaders(config),
    (err) => {
      logger.error('API Request Error:', err);
      return Promise.reject(err);
    }
  );
  instance.interceptors.response.use(
    (response) => {
      logger.log('API Response:', response.status, response.config.url);
      
      // ✅ FAILOVER v750: Se sucesso e estamos no backup, tentar voltar ao primary após 5 minutos
      if (BACKUP_API && currentAPI === BACKUP_API && lastFailoverTime) {
        const timeSinceFailover = Date.now() - lastFailoverTime;
        if (timeSinceFailover >= RECOVERY_TIME) {
          logger.log('✅ Voltando para API primária após 5 minutos de sucesso');
          currentAPI = PRIMARY_API;
          failoverCount = 0;
          lastFailoverTime = null;
          // Recriar instâncias com nova baseURL
          const newInstance = createApiInstance();
          applyLojaInterceptors(newInstance);
          Object.assign(apiClient, newInstance);
          Object.assign(clinicaApiClient, newInstance);
        }
      }
      
      return response;
    },
    async (error) => {
      logger.error('API Error:', error.response?.status, error.response?.data?.code);
      
      // ✅ FAILOVER v750: Detectar falhas e tentar backup (inclui CORS/rede quando primária indisponível)
      const originalRequest = error.config;
      const isNetworkOrCors =
        error.code === 'ECONNABORTED' ||
        error.code === 'ERR_NETWORK' ||
        error.code === 'ETIMEDOUT' ||
        !error.response ||
        (error.response?.status >= 500 && error.response?.status < 600) ||
        (typeof error.message === 'string' && (
          error.message.includes('Network Error') ||
          error.message.includes('Failed to fetch') ||
          error.message.includes('CORS') ||
          error.message.includes('Access-Control')
        ));
      const requestUrl = (originalRequest?.baseURL || '') + (originalRequest?.url || '');
      const isLojaRoute =
        requestUrl.includes('info_publica') ||
        requestUrl.includes('auth/loja') ||
        requestUrl.includes('lojas/verificar_senha') ||
        requestUrl.includes('lojas/recuperar_senha');
      const shouldFailover =
        BACKUP_API &&
        !originalRequest?._failoverRetry &&
        currentAPI === PRIMARY_API &&
        failoverCount < MAX_FAILOVER_ATTEMPTS &&
        isNetworkOrCors &&
        (!isLojaRoute || ENABLE_LOJA_FAILOVER);

      if (shouldFailover && originalRequest) {
        failoverCount++;
        lastFailoverTime = Date.now();
        originalRequest._failoverRetry = true;

        // Sempre visível no console (inclusive produção) para teste de failover
        console.warn(`⚠️ API primária falhou (${error.code || error.response?.status || 'CORS/rede'}), tentando backup (${failoverCount}/${MAX_FAILOVER_ATTEMPTS})...`);

        // Mudar para backup
        currentAPI = BACKUP_API;
        const backupBaseURL = BACKUP_API.endsWith('/api') ? BACKUP_API : `${BACKUP_API}/api`;
        originalRequest.baseURL = backupBaseURL;

        // Recriar instâncias com nova baseURL
        const newInstance = createApiInstance();
        applyLojaInterceptors(newInstance);
        Object.assign(apiClient, newInstance);
        Object.assign(clinicaApiClient, newInstance);

        try {
          console.warn('🔄 Repetindo requisição no servidor backup...');
          const res = await instance(originalRequest);
          console.warn('API Response:', res.status, res.config.url);
          return res;
        } catch (backupError) {
          console.error('❌ Servidor backup também falhou:', backupError);
          return Promise.reject(backupError);
        }
      }
      
      if (handle507(error)) return Promise.reject(error);
      if (error.response?.status === 401) {
        return handle401(error, instance);
      }
      return Promise.reject(error);
    }
  );
}

export const apiClient = createApiInstance();
applyLojaInterceptors(apiClient);

export const clinicaApiClient = createApiInstance();
applyLojaInterceptors(clinicaApiClient);

export default apiClient;

// ===== FAILOVER STATUS (v750) =====

/** Retorna status atual do failover */
export function getFailoverStatus() {
  return {
    currentAPI,
    isPrimary: currentAPI === PRIMARY_API,
    isBackup: currentAPI === BACKUP_API,
    failoverCount,
    lastFailoverTime,
    hasBackup: !!BACKUP_API,
  };
}

/**
 * Força uso da API primária (Heroku). Usar ao entrar em páginas de loja:
 * o backup (Render) não tem os dados das lojas; lojas devem sempre usar a API principal.
 */
export function resetToPrimaryAPI(): void {
  if (currentAPI === PRIMARY_API) return;
  currentAPI = PRIMARY_API;
  failoverCount = 0;
  lastFailoverTime = null;
  const newInstance = createApiInstance();
  applyLojaInterceptors(newInstance);
  Object.assign(apiClient, newInstance);
  Object.assign(clinicaApiClient, newInstance);
}

/** Verifica health do servidor atual */
export async function checkHealth(): Promise<{ healthy: boolean; api: string; error?: string }> {
  try {
    const response = await axios.get(`${currentAPI}/api/health/`, { timeout: 5000 });
    return {
      healthy: response.data.status === 'healthy',
      api: currentAPI,
    };
  } catch (error) {
    return {
      healthy: false,
      api: currentAPI,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// ===== HEARTBEAT =====

let heartbeatInterval: ReturnType<typeof setInterval> | null = null;

export function startHeartbeat() {
  if (heartbeatInterval) {
    logger.log('Heartbeat já está rodando');
    return;
  }
  logger.log('Iniciando heartbeat (5 min)');
  heartbeatInterval = setInterval(async () => {
    try {
      await apiClient.get('/superadmin/lojas/heartbeat/');
    } catch (err: unknown) {
      logger.error('Heartbeat falhou:', err);
      const e = err as { response?: { status?: number } };
      if (e.response?.status === 401) {
        stopHeartbeat();
        clearSessionAndRedirect(getLoginUrlForRedirect());
      }
    }
  }, 5 * 60 * 1000);
}

export function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
    logger.log('Heartbeat parado');
  }
}
