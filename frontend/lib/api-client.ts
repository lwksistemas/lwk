import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { logger } from './logger';
import { getLoginUrl } from './auth';
import { getPrimaryApiRoot, getBackupApiRoot } from './api-base';

// ===== CONFIGURAÇÃO DE FAILOVER (v750) =====
const PRIMARY_API = getPrimaryApiRoot();
const BACKUP_API = getBackupApiRoot() || undefined;
const ENABLE_LOJA_FAILOVER = process.env.NEXT_PUBLIC_ENABLE_LOJA_FAILOVER === 'true';
const TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000');

// ✅ NOVO v787: Suporte para troca manual de servidor
// Rotas de loja SEMPRE usam Heroku (primário); superadmin pode usar Render
function getInitialAPI(): string {
  if (typeof window !== 'undefined') {
    const path = window.location.pathname || '';
    if (path.includes('/loja/')) {
      return PRIMARY_API;
    }
    const savedServer = localStorage.getItem('backend_servidor');
    if (savedServer === 'render' && BACKUP_API) {
      return BACKUP_API;
    }
  }
  return PRIMARY_API;
}

// Controle de failover
let currentAPI = getInitialAPI();
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
  // Fallback: extrair slug da URL quando em /loja/ (evita redirecionar para home no logout)
  if (!lojaSlug && window.location.pathname.includes('/loja/')) {
    const match = window.location.pathname.match(/^\/loja\/([^/]+)/);
    if (match) lojaSlug = match[1];
  }
  // Se estamos em /loja/ e temos slug, tratar como loja mesmo sem user_type (sessão já limpa)
  if (!userType && lojaSlug) userType = 'loja';
  return getLoginUrl(userType || undefined, lojaSlug || undefined);
}

/** Adiciona X-Loja-ID / X-Tenant-Slug e Authorization em todas as requisições de loja. */
function addLojaAuthHeaders(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  if (typeof window === 'undefined') return config;
  
  // ✅ v1381: Cache-busting para evitar service worker cachear respostas antigas
  // Adicionar timestamp apenas em requisições GET de APIs de dados
  if (config.method === 'get' && config.url && !config.url.includes('_t=')) {
    const separator = config.url.includes('?') ? '&' : '?';
    config.url = `${config.url}${separator}_t=${Date.now()}`;
  }
  
  // Em páginas de loja, SEMPRE usar Heroku - Render não tem dados tenant
  if (window.location.pathname.includes('/loja/') && currentAPI === BACKUP_API) {
    currentAPI = PRIMARY_API;
    failoverCount = 0;
    lastFailoverTime = null;
    updateInstancesBaseURL();
    const base = PRIMARY_API.endsWith('/api') ? PRIMARY_API : `${PRIMARY_API}/api`;
    config.baseURL = base;
  }
  // Slug: em /loja/[slug]/... a URL vence sessionStorage (leitura síncrona). O layout costuma
  // gravar loja_slug depois do primeiro paint — requisições paralelas já disparadas usavam slug
  // antigo → X-Tenant-Slug errado → listas vazias intermitentes (~52 bytes).
  // Só persistir loja_slug no storage com sessão ativa: após logout o storage é limpo e qualquer
  // requisição tardia não deve recolocar o slug (evita piscar da lista / estado estranho no login).
  const accessToken = sessionStorage.getItem('access_token');
  const pathLojaMatch = window.location.pathname.match(/^\/loja\/([^/]+)/);
  let lojaSlug: string | null = null;
  if (pathLojaMatch) {
    lojaSlug = pathLojaMatch[1];
    if (accessToken) {
      const stored = sessionStorage.getItem('loja_slug');
      if (stored !== lojaSlug) {
        sessionStorage.setItem('loja_slug', lojaSlug);
        // Evita current_loja_id de outra loja: backend pode combinar headers de forma
        // que listas CRM voltem vazias (~52 bytes) mesmo com slug certo na URL.
        sessionStorage.removeItem('current_loja_id');
      }
    }
  } else {
    lojaSlug = sessionStorage.getItem('loja_slug');
  }
  // Após logout/login, sessionStorage pode ainda não ter loja_slug na primeira requisição;
  // o login grava cookie loja_slug — usar como fallback (mesmo valor canônico do backend).
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
  // X-Loja-ID: útil fora de /loja/[slug]/… (ex.: fluxos que só têm ID). Dentro de /loja/[slug]/…
  // o slug na URL é a fonte de verdade; ID no sessionStorage pode ficar desatualizado após deploy
  // ou troca de loja e causar resolução errada de tenant → listas CRM vazias “intermitentes”.
  const lojaId = sessionStorage.getItem('current_loja_id');
  const isLojaDashboardComSlug = Boolean(pathLojaMatch && lojaSlug);
  if (lojaId && !isLojaDashboardComSlug) {
    config.headers.set('X-Loja-ID', lojaId);
  }
  if (accessToken) config.headers.set('Authorization', `Bearer ${accessToken}`);
  if (process.env.NODE_ENV === 'development') {
    logger.log('API Request:', config.method?.toUpperCase(), config.url);
  }
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
      if (process.env.NODE_ENV === 'development') {
        logger.log('API Response:', response.status, response.config.url);
      }
      
      // ✅ FAILOVER v750: Se sucesso e estamos no backup, tentar voltar ao primary após 5 minutos
      if (BACKUP_API && currentAPI === BACKUP_API && lastFailoverTime) {
        const timeSinceFailover = Date.now() - lastFailoverTime;
        if (timeSinceFailover >= RECOVERY_TIME) {
          logger.log('✅ Voltando para API primária após 5 minutos de sucesso');
          currentAPI = PRIMARY_API;
          failoverCount = 0;
          lastFailoverTime = null;
          updateInstancesBaseURL();
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
      // Rotas de loja: NUNCA fazer failover para Render - backup não tem dados tenant
      const isOnLojaPage = typeof window !== 'undefined' && window.location.pathname.includes('/loja/');
      const isLojaRoute =
        isOnLojaPage ||
        requestUrl.includes('info_publica') ||
        requestUrl.includes('auth/loja') ||
        requestUrl.includes('lojas/verificar_senha') ||
        requestUrl.includes('lojas/recuperar_senha') ||
        requestUrl.includes('crm-vendas') ||
        requestUrl.includes('notificacoes');
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
        updateInstancesBaseURL();

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

      // Troca automática: 503 do Render (ex: credenciais Google) → tentar Heroku e repetir
      const is503FromBackup =
        BACKUP_API &&
        currentAPI === BACKUP_API &&
        error.response?.status === 503 &&
        !originalRequest?._primaryRetry;
      const detail = (error.response?.data?.detail ?? '') + '';
      const isConfigError = detail.includes('GOOGLE_CLIENT_ID') || detail.includes('configurados');
      if (is503FromBackup && isConfigError && originalRequest) {
        originalRequest._primaryRetry = true;
        console.warn('⚠️ Backup retornou 503 (config). Trocando automaticamente para Heroku...');
        currentAPI = PRIMARY_API;
        failoverCount = 0;
        lastFailoverTime = null;
        const primaryBaseURL = PRIMARY_API.endsWith('/api') ? PRIMARY_API : `${PRIMARY_API}/api`;
        originalRequest.baseURL = primaryBaseURL;
        updateInstancesBaseURL();
        if (typeof window !== 'undefined') {
          localStorage.setItem('backend_servidor', 'heroku');
        }
        try {
          return instance(originalRequest);
        } catch (primaryError) {
          return Promise.reject(primaryError);
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

/** 
 * @deprecated Use apiClient instead. clinicaApiClient is now an alias for apiClient.
 * This will be removed in a future version.
 */
export const clinicaApiClient = apiClient;

/** Atualiza a baseURL das instâncias ao trocar de servidor (evita requisições irem ao servidor errado). */
function updateInstancesBaseURL(): void {
  const baseURL = currentAPI.endsWith('/api') ? currentAPI : `${currentAPI}/api`;
  apiClient.defaults.baseURL = baseURL;
}

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

/** Base URL atual (com /api) para fetch() e outros clientes que não usam apiClient. */
export function getCurrentApiBaseUrl(): string {
  const base = currentAPI.endsWith('/api') ? currentAPI : `${currentAPI}/api`;
  return base;
}

/**
 * ✅ NOVO v787: Permite trocar manualmente o servidor backend.
 * Atualiza defaults.baseURL para as próximas requisições irem ao servidor correto.
 */
export function setBackendServer(serverUrl: string): void {
  currentAPI = serverUrl;
  failoverCount = 0;
  lastFailoverTime = null;
  updateInstancesBaseURL();
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
  updateInstancesBaseURL();
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
