# Sistema de Redundância LWK Sistemas
## Heroku, Render e Banco Único

**Documento de referência:** como funciona a redundância, o código no frontend e no backend, e a estrutura do sistema.

---

## 1. Visão geral

O sistema usa **dois backends** (API Django) para garantir disponibilidade:

| Papel        | Serviço | URL | Uso |
|--------------|---------|-----|-----|
| **Primário** | Heroku  | `https://lwksistemas-38ad47519238.herokuapp.com` | Sempre tentado primeiro |
| **Backup**   | Render  | `https://lwksistemas-backup.onrender.com`   | Usado quando o primário falha |

O **frontend** (Next.js na Vercel) decide sozinho: se a chamada ao Heroku falhar (rede, timeout, CORS, 5xx), repete a **mesma requisição** no Render. Os dois backends usam o **mesmo banco PostgreSQL**, então os dados são os mesmos.

---

## 2. Estrutura do sistema

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    USUÁRIO / NAVEGADOR                   │
                    └─────────────────────────────┬───────────────────────────┘
                                                  │
                                                  ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │  VERCEL (Frontend Next.js)                               │
                    │  https://lwksistemas.com.br                              │
                    │  - Páginas: loja, superadmin, suporte                    │
                    │  - Cliente API: frontend/lib/api-client.ts (failover)   │
                    └─────────────────────────────┬───────────────────────────┘
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         │ 1) Tenta PRIMÁRIO (Heroku)                     │
                         │ 2) Se falhar → repete no BACKUP (Render)        │
                         └────────────────────────┬────────────────────────┘
                                                  │
              ┌───────────────────────────────────┼───────────────────────────────────┐
              ▼                                                                       ▼
┌─────────────────────────────────────┐                         ┌─────────────────────────────────────┐
│  HEROKU (Backend Django – primário)  │                         │  RENDER (Backend Django – backup)   │
│  lwksistemas-38ad47519238.herokuapp │                         │  lwksistemas-backup-ewgo.onrender   │
│  - Gunicorn, settings_production    │                         │  - Gunicorn, settings_production    │
│  - CORS, OPTIONS preflight OK       │                         │  - CORS, OPTIONS preflight OK       │
└─────────────────┬───────────────────┘                         └─────────────────┬─────────────────┘
                  │                                                                  │
                  │         DATABASE_URL (mesmo valor nos dois)                     │
                  └──────────────────────────────┬──────────────────────────────────┘
                                                  ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │  POSTGRESQL (banco único)                               │
                    │  - Lojas, usuários, superadmin, tenants                  │
                    │  - Heroku e Render leem/escrevem no mesmo banco         │
                    └─────────────────────────────────────────────────────────┘
```

**Resumo:**

- **Vercel:** só entrega o frontend (HTML/JS). Quem chama a API é o navegador.
- **Heroku:** backend principal; recebe a maior parte das requisições.
- **Render:** mesmo código e mesmo `DATABASE_URL`; entra em cena quando o Heroku falha.
- **Banco único:** um só PostgreSQL; evita divergência de dados entre primário e backup.

---

## 3. Fluxo de failover (frontend)

1. O usuário abre uma página (ex.: login da loja ou dashboard).
2. O frontend chama a API **primária** (Heroku), por exemplo:  
   `GET https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/info_publica/?slug=clinica-daniel-5889`
3. Se der **erro** considerado “falha do primário” (veja seção 4), o interceptor do axios:
   - Marca a requisição como “já tentou failover” (`_failoverRetry`).
   - Troca a base URL usada pelo cliente para o **Render**.
   - **Repete a mesma requisição** para o Render.
4. Se o Render responder com sucesso, a resposta é devolvida e a página segue normal.
5. As próximas requisições da mesma sessão seguem indo para o Render até que, após **5 minutos** de sucesso, o frontend volta a tentar o primário (Heroku).

Condições para **não** fazer failover (só para aquela requisição):

- Rotas de loja (`info_publica`, `auth/loja`, etc.) quando a flag `NEXT_PUBLIC_ENABLE_LOJA_FAILOVER` não está `true` (hoje está `true` porque o banco é único).
- Requisição já tentada no backup (`_failoverRetry`).
- Já foram feitas 3 tentativas de failover.
- Não há `NEXT_PUBLIC_API_BACKUP_URL` configurado.

---

## 4. Código do frontend (failover)

Arquivo principal: **`frontend/lib/api-client.ts`**.

### 4.1 Configuração e variáveis de ambiente

```ts
const PRIMARY_API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BACKUP_API = process.env.NEXT_PUBLIC_API_BACKUP_URL;
const ENABLE_LOJA_FAILOVER = process.env.NEXT_PUBLIC_ENABLE_LOJA_FAILOVER === 'true';
const TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000');

let currentAPI = PRIMARY_API;
let failoverCount = 0;
let lastFailoverTime: number | null = null;
const MAX_FAILOVER_ATTEMPTS = 3;
const RECOVERY_TIME = 5 * 60 * 1000; // 5 minutos
```

- **PRIMARY_API:** URL base da API primária (Heroku).
- **BACKUP_API:** URL base do backup (Render); se vazio, não há failover.
- **ENABLE_LOJA_FAILOVER:** se `true`, rotas de loja também podem fazer failover (usar só com banco único).
- **TIMEOUT:** timeout das requisições (padrão 10s); após esse tempo, a falha pode disparar o failover.
- **RECOVERY_TIME:** após 5 minutos usando o backup com sucesso, o frontend volta a usar o primário.

### 4.2 Quando a falha é considerada “rede/CORS/5xx”

O failover só ocorre se o erro for tratado como “falha do servidor primário”:

```ts
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
```

Ou seja: timeout, erro de rede, sem resposta, 5xx ou mensagem indicando CORS/rede.

### 4.3 Rotas de loja e flag de failover

```ts
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
```

- Se **ENABLE_LOJA_FAILOVER** for `false`, requisições que forem “rota de loja” **não** disparam failover (evita usar backup com banco diferente).
- Com banco único e `ENABLE_LOJA_FAILOVER=true`, lojas também fazem failover.

### 4.4 Execução do failover (troca para Render e nova tentativa)

```ts
if (shouldFailover && originalRequest) {
  failoverCount++;
  lastFailoverTime = Date.now();
  originalRequest._failoverRetry = true;
  currentAPI = BACKUP_API;
  const backupBaseURL = BACKUP_API.endsWith('/api') ? BACKUP_API : `${BACKUP_API}/api`;
  originalRequest.baseURL = backupBaseURL;
  // Recria instâncias axios com nova baseURL
  const newInstance = createApiInstance();
  applyLojaInterceptors(newInstance);
  Object.assign(apiClient, newInstance);
  Object.assign(clinicaApiClient, newInstance);
  try {
    const res = await instance(originalRequest);
    return res;
  } catch (backupError) {
    return Promise.reject(backupError);
  }
}
```

Ou seja: troca a base para o Render, recria o cliente com essa base e reexecuta a mesma requisição.

### 4.5 Voltar ao primário após 5 minutos

No interceptor de **sucesso**:

```ts
if (BACKUP_API && currentAPI === BACKUP_API && lastFailoverTime) {
  const timeSinceFailover = Date.now() - lastFailoverTime;
  if (timeSinceFailover >= RECOVERY_TIME) {
    currentAPI = PRIMARY_API;
    failoverCount = 0;
    lastFailoverTime = null;
    // Recriar instâncias com baseURL do primário
    const newInstance = createApiInstance();
    applyLojaInterceptors(newInstance);
    Object.assign(apiClient, newInstance);
    Object.assign(clinicaApiClient, newInstance);
  }
}
```

### 4.6 Função para forçar uso do primário (ex.: páginas de loja)

```ts
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
```

Ela é usada ao entrar em páginas de loja (ex.: login) para garantir que, naquele contexto, o próximo request vá ao Heroku. Com banco único e failover de loja habilitado, o backup também pode atender; essa função só “reseta” o estado para preferir o primário de novo.

### 4.7 Variáveis de ambiente (frontend)

No **Vercel** ou em **`.env.production`**:

```env
NEXT_PUBLIC_API_URL=https://lwksistemas-38ad47519238.herokuapp.com/api
NEXT_PUBLIC_API_BACKUP_URL=https://lwksistemas-backup.onrender.com
NEXT_PUBLIC_ENABLE_LOJA_FAILOVER=true
NEXT_PUBLIC_API_TIMEOUT=10000
```

---

## 5. Código do backend (CORS e preflight)

Tanto o Heroku quanto o Render usam **`config.settings_production`** e o mesmo app Django. O que importa para redundância é CORS e o tratamento de OPTIONS.

### 5.1 CORS (settings_production.py)

```python
_DEFAULT_CORS_ORIGINS = [
    'https://lwksistemas.com.br',
    'https://www.lwksistemas.com.br',
]
_raw = os.environ.get('CORS_ORIGINS', '').strip()
CORS_ALLOWED_ORIGINS = [o.strip() for o in _raw.split(',') if o.strip()] if _raw else _DEFAULT_CORS_ORIGINS
CORS_ALLOW_CREDENTIALS = True
```

- Se **CORS_ORIGINS** estiver vazio ou não definido, usa a lista padrão (inclui o domínio do frontend).
- Assim o Render aceita requisições de `https://lwksistemas.com.br` mesmo sem configurar CORS no painel.

### 5.2 Preflight OPTIONS (SuperAdminSecurityMiddleware)

O navegador envia **OPTIONS** antes de GET/POST cross-origin. Esse request não leva `Authorization`. Se o middleware de segurança retornar 401 para OPTIONS, o navegador interpreta como falha de CORS. Por isso, em **`superadmin/middleware.py`**:

```python
if request.path.startswith('/api/superadmin/'):
    if request.method == 'OPTIONS':
        return self.get_response(request)
```

Ou seja: para rotas `/api/superadmin/`, requisições **OPTIONS** passam direto; o **CorsMiddleware** (que roda antes) responde com 200 e os headers CORS. Assim o preflight passa tanto no Heroku quanto no Render.

### 5.3 Ordem do middleware

Em **settings_production.py**:

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Primeiro: adiciona CORS na resposta
    'tenants.middleware.TenantMiddleware',
    # ...
    'superadmin.middleware.JWTAuthenticationMiddleware',
    'superadmin.middleware.SuperAdminSecurityMiddleware',  # OPTIONS passa aqui
    # ...
]
```

O **CorsMiddleware** deve ficar no topo para que todas as respostas (incluindo as geradas por outros middlewares) recebam os headers CORS quando aplicável.

### 5.4 Banco de dados (banco único)

```python
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=int(os.environ.get('CONN_MAX_AGE', '60')),
        conn_health_checks=True,
    )
}
```

Heroku e Render usam a **mesma** `DATABASE_URL` (configurada em cada painel). Não há código diferente para “primário” ou “backup”; a redundância é só de servidor HTTP, não de banco.

---

## 6. Resumo da estrutura de arquivos

| Onde        | Arquivo / Ajuste | Função na redundância |
|------------|-------------------|------------------------|
| Frontend   | `frontend/lib/api-client.ts` | Failover, timeout, troca para Render, recovery 5 min, `resetToPrimaryAPI` |
| Frontend   | `frontend/.env.production` (ou Vercel) | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_API_BACKUP_URL`, `NEXT_PUBLIC_ENABLE_LOJA_FAILOVER`, `NEXT_PUBLIC_API_TIMEOUT` |
| Frontend   | `frontend/app/(auth)/loja/[slug]/login/page.tsx` | Chama `resetToPrimaryAPI()` ao montar a página de login da loja |
| Frontend   | `frontend/app/(dashboard)/loja/[slug]/layout.tsx` | Chama `resetToPrimaryAPI()` ao entrar em rotas de loja logada |
| Backend    | `backend/config/settings_production.py` | CORS (lista padrão e `CORS_ORIGINS`), usado por Heroku e Render |
| Backend    | `backend/superadmin/middleware.py` | Libera OPTIONS em `/api/superadmin/` para o preflight CORS passar |

---

## 7. Como testar a redundância

1. **Deixar o Heroku parado (apenas para teste):**  
   `heroku ps:scale web=0 --app lwksistemas`
2. Abrir o site (ex.: login da loja ou dashboard) e usar normalmente; no console do navegador podem aparecer avisos de failover.
3. Confirmar no **Render** (Dashboard → Logs) que as requisições estão sendo atendidas pelo backup.
4. **Reativar o Heroku:**  
   `heroku ps:scale web=1 --app lwksistemas`

---

## 8. Gerar PDF a partir deste documento

- **Pandoc (linha de comando):**  
  `pandoc docs/SISTEMA-REDUNDANCIA-HEROKU-RENDER.md -o docs/SISTEMA-REDUNDANCIA-HEROKU-RENDER.pdf`

- **Cursor / VS Code:** extensões como “Markdown PDF” permitem exportar o `.md` para PDF.

- **Navegador:** abrir o `.md` em um visualizador que suporte Markdown e usar “Imprimir → Salvar como PDF”.

---

*Documento gerado para o projeto LWK Sistemas – redundância Heroku + Render com banco único.*
