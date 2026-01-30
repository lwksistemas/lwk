import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { logger } from './logger';
import { getLoginUrl } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const SESSION_CODES = [
  'DIFFERENT_SESSION', 'NO_SESSION', 'TIMEOUT',
  'SESSION_CONFLICT', 'SESSION_TIMEOUT',
] as const;

function clearSessionAndRedirect(loginUrl: string, message?: string) {
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
  error: { response?: { data?: { code?: string; message?: string; detail?: unknown } }; config?: { _retry?: boolean; headers?: { Authorization?: string } } },
  apiInstance: AxiosInstance
): Promise<unknown> {
  const originalRequest = error.config;
  const errorData = error.response?.data;
  const errorCode = errorData?.code || (errorData?.detail as { code?: string })?.code;
  const errorMessage = errorData?.message || (errorData?.detail as { message?: string })?.message || errorData?.detail;

  if (errorCode && SESSION_CODES.includes(errorCode as (typeof SESSION_CODES)[number])) {
    logger.critical('Sessão inválida:', errorCode);
    const loginUrl = getLoginUrl();
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
        clearSessionAndRedirect(getLoginUrl());
        return Promise.reject(error);
      }
      const response = await axios.post(
        `${API_URL}/api/auth/token/refresh/`,
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
      clearSessionAndRedirect(getLoginUrl());
      return Promise.reject(refreshError);
    }
  }
  return Promise.reject(error);
}

/** Cria instância base (baseURL, timeout, JSON). */
function createApiInstance(): AxiosInstance {
  return axios.create({
    baseURL: `${API_URL}/api`,
    headers: { 'Content-Type': 'application/json' },
    timeout: 20000,
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
      return response;
    },
    async (error) => {
      logger.error('API Error:', error.response?.status, error.response?.data?.code);
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
        clearSessionAndRedirect(getLoginUrl());
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
