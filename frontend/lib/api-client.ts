import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { logger } from './logger';
import { getLoginUrl } from './auth';
import { getPrimaryApiRoot, getPrimaryApiBaseUrl } from './api-base';
import { USE_JWT_HTTPONLY_COOKIES } from './auth-cookies';

const TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '120000', 10);

const SESSION_CODES = [
  'DIFFERENT_SESSION', 'NO_SESSION', 'NO_SESSION_HEADER', 'TIMEOUT',
  'SESSION_CONFLICT', 'SESSION_TIMEOUT', 'SESSION_REPLACED', 'SESSION_DB_ERROR',
] as const;

export { SESSION_CODES };

let sessionLogoutInProgress = false;
let refreshInFlight: Promise<boolean> | null = null;

/** Renova access token (sessionStorage ou cookies httpOnly). Retorna false se falhar. */
export async function tryRefreshAccessToken(): Promise<boolean> {
  if (typeof window === 'undefined') return false;
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const refreshToken = sessionStorage.getItem('refresh_token');
    const accessToken = sessionStorage.getItem('access_token');
    if (!USE_JWT_HTTPONLY_COOKIES && !refreshToken) return false;

    try {
      const base = getPrimaryApiBaseUrl();
      const refreshHeaders: Record<string, string> = {};
      if (accessToken) refreshHeaders.Authorization = `Bearer ${accessToken}`;
      const sessionId = sessionStorage.getItem('session_id');
      if (sessionId) refreshHeaders['X-Session-ID'] = sessionId;
      const response = await axios.post(
        `${base}/auth/token/refresh/`,
        USE_JWT_HTTPONLY_COOKIES ? {} : { refresh: refreshToken },
        { headers: refreshHeaders, withCredentials: USE_JWT_HTTPONLY_COOKIES },
      );
      const { access, refresh: newRefresh } = response.data;
      if (!USE_JWT_HTTPONLY_COOKIES) {
        if (access) sessionStorage.setItem('access_token', access);
        // ROTATE_REFRESH_TOKENS: backend invalida o refresh antigo — persistir o novo.
        if (newRefresh) sessionStorage.setItem('refresh_token', newRefresh);
      }
      return Boolean(access);
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

/** Limpa tokens/sessão e redireciona para login. Exportado para uso em fetch() (ex.: clinica-beleza). */
export async function clearSessionAndRedirect(loginUrl: string, message?: string) {
  if (typeof window !== 'undefined') {
    if (sessionLogoutInProgress) return;
    sessionLogoutInProgress = true;
  }
  if (USE_JWT_HTTPONLY_COOKIES && typeof window !== 'undefined') {
    try {
      const base = getPrimaryApiBaseUrl();
      await axios.post(`${base}/auth/logout/`, {}, { withCredentials: true });
    } catch {
      /* cookies limpos no servidor quando possível */
    }
  }
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
  sessionStorage.removeItem('user_type');
  sessionStorage.removeItem('loja_slug');
  sessionStorage.removeItem('session_id');
  sessionStorage.removeItem('current_loja_id');
  sessionStorage.removeItem('current_vendedor_id');
  document.cookie = 'user_type=; path=/; max-age=0';
  document.cookie = 'loja_slug=; path=/; max-age=0';
  document.cookie = 'loja_usa_crm=; path=/; max-age=0';
  if (message && typeof window !== 'undefined') alert(message);
  if (typeof window !== 'undefined') window.location.href = loginUrl;
}

/** URL de login para redirecionar (usa storage antes de limpar). Exportado para uso em fetch(). */
export function getLoginUrlForRedirect(): string {
  if (typeof window === 'undefined') return '/';
  let userType = sessionStorage.getItem('user_type') as 'superadmin' | 'suporte' | 'loja' | null;
  let lojaSlug = sessionStorage.getItem('loja_slug');
  if (!lojaSlug && window.location.pathname.includes('/loja/')) {
    const match = window.location.pathname.match(/^\/loja\/([^/]+)/);
    if (match) lojaSlug = match[1];
  }
  if (!userType && lojaSlug) userType = 'loja';
  return getLoginUrl(userType || undefined, lojaSlug || undefined);
}

/** Adiciona X-Loja-ID / X-Tenant-Slug e Authorization em todas as requisições de loja. */
function addLojaAuthHeaders(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  if (typeof window === 'undefined') return config;

  const accessToken = USE_JWT_HTTPONLY_COOKIES
    ? null
    : sessionStorage.getItem('access_token');
  const pathLojaMatch = window.location.pathname.match(/^\/loja\/([^/]+)/);
  let lojaSlug: string | null = null;
  if (pathLojaMatch) {
    lojaSlug = pathLojaMatch[1];
    const hasSession = USE_JWT_HTTPONLY_COOKIES
      ? Boolean(sessionStorage.getItem('session_id'))
      : Boolean(accessToken);
    if (hasSession) {
      const stored = sessionStorage.getItem('loja_slug');
      if (stored !== lojaSlug) {
        sessionStorage.setItem('loja_slug', lojaSlug);
        sessionStorage.removeItem('current_loja_id');
      }
    }
  } else {
    lojaSlug = sessionStorage.getItem('loja_slug');
  }
  if (!lojaSlug && accessToken && typeof document !== 'undefined') {
    const m = document.cookie.match(/(?:^|;\s*)loja_slug=([^;]+)/);
    if (m) {
      try {
        lojaSlug = decodeURIComponent(m[1].trim());
      } catch {
        lojaSlug = m[1].trim();
      }
      if (lojaSlug) sessionStorage.setItem('loja_slug', lojaSlug);
    }
  }
  if (lojaSlug) {
    config.headers.set('X-Tenant-Slug', lojaSlug);
  }
  const lojaId = sessionStorage.getItem('current_loja_id');
  const isLojaDashboardComSlug = Boolean(pathLojaMatch && lojaSlug);
  if (lojaId && !isLojaDashboardComSlug) {
    config.headers.set('X-Loja-ID', lojaId);
  }
  if (accessToken) config.headers.set('Authorization', `Bearer ${accessToken}`);
  // Enviar session_id para validação de sessão única no backend
  const sessionId = sessionStorage.getItem('session_id');
  if (sessionId) config.headers.set('X-Session-ID', sessionId);
  if (config.data instanceof FormData) {
    // Deixa o browser definir multipart/form-data com boundary
    if (typeof config.headers?.delete === 'function') {
      config.headers.delete('Content-Type')
    } else if (config.headers) {
      delete config.headers['Content-Type']
    }
  }
  if (process.env.NODE_ENV === 'development') {
    logger.log('API Request:', config.method?.toUpperCase(), config.url);
  }
  return config;
}

function handle507(error: { response?: { status?: number; data?: { error?: string } } }): boolean {
  if (error.response?.status === 507) {
    const msg = error.response?.data?.error || 'Limite de armazenamento da loja atingido. Entre em contato com o suporte.';
    if (typeof window !== 'undefined') alert(msg);
    return true;
  }
  return false;
}

async function handle401(
  error: { response?: { data?: { code?: string; message?: string; detail?: unknown } }; config?: { _retry?: boolean; headers?: { Authorization?: string }; url?: string } },
  apiInstance: AxiosInstance
): Promise<unknown> {
  const originalRequest = error.config;
  const errorData = error.response?.data;
  const errorCode = errorData?.code || (errorData?.detail as { code?: string })?.code;
  const errorMessage = errorData?.message || (errorData?.detail as { message?: string })?.message || errorData?.detail;

  const isLoginEndpoint = originalRequest?.url?.includes('/login') || originalRequest?.url?.includes('/token');
  if (isLoginEndpoint) {
    logger.log('Erro 401 em endpoint de login - não redirecionar');
    return Promise.reject(error);
  }

  if (errorCode && SESSION_CODES.includes(errorCode as (typeof SESSION_CODES)[number])) {
    logger.critical('Sessão inválida:', errorCode);
    const loginUrl = getLoginUrlForRedirect();
    void clearSessionAndRedirect(
      loginUrl,
      typeof errorMessage === 'string' ? errorMessage : 'Sua sessão expirou. Faça login novamente.'
    );
    return Promise.reject(error);
  }

  if (originalRequest && !originalRequest._retry) {
    originalRequest._retry = true;
    const refreshed = await tryRefreshAccessToken();
    if (refreshed) {
      logger.log('Refresh OK, repetindo requisição');
      originalRequest.headers = originalRequest.headers || {};
      const accessToken = sessionStorage.getItem('access_token');
      if (accessToken) {
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
      }
      return apiInstance(originalRequest);
    }
    void clearSessionAndRedirect(
      getLoginUrlForRedirect(),
      'Sessão expirada. Faça login novamente.',
    );
    return Promise.reject(error);
  }
  return Promise.reject(error);
}

function createApiInstance(): AxiosInstance {
  return axios.create({
    baseURL: getPrimaryApiBaseUrl(),
    headers: { 'Content-Type': 'application/json' },
    timeout: TIMEOUT,
    withCredentials: USE_JWT_HTTPONLY_COOKIES,
  });
}

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
      if (process.env.NODE_ENV === 'development') {
        logger.log('API Response:', response.status, response.config.url);
      }
      return response;
    },
    async (error) => {
      const status = error.response?.status;
      const code = error.response?.data?.code;
      const noResponseDetail = `${error.code || 'ERR'} ${error.message || 'sem resposta (rede/CORS ou URL da API)'}`.trim();
      logger.error(
        'API Error:',
        error.response != null ? status : noResponseDetail,
        error.response != null ? (code ?? '') : ''
      );
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

/** @deprecated Use apiClient. */
export const clinicaApiClient = apiClient;

export default apiClient;

export function getCurrentApiBaseUrl(): string {
  return getPrimaryApiBaseUrl();
}

/** Verifica health do backend configurado em NEXT_PUBLIC_API_URL */
export async function checkHealth(): Promise<{ healthy: boolean; api: string; error?: string }> {
  const root = getPrimaryApiRoot();
  const healthUrl = `${getPrimaryApiBaseUrl()}/superadmin/health/`;
  try {
    const response = await axios.get(healthUrl, { timeout: 5000 });
    const ok = response.data?.status === 'healthy' || response.status === 200;
    return { healthy: ok, api: root };
  } catch (error) {
    return {
      healthy: false,
      api: root,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
