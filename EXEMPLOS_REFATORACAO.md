# 🔧 EXEMPLOS PRÁTICOS DE REFATORAÇÃO

## 1. REFATORAÇÃO DE MODELOS

### ANTES (Duplicado em 4 apps)
```python
# backend/servicos/models.py
class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# backend/restaurante/models.py
class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### DEPOIS (Modelo base)
```python
# backend/core/models.py
class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class BaseCategoria(BaseModel):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    
    class Meta:
        abstract = True

# backend/servicos/models.py
from core.models import BaseCategoria

class Categoria(BaseCategoria):
    class Meta:
        db_table = 'servicos_categorias'
        ordering = ['nome']

# backend/restaurante/models.py
from core.models import BaseCategoria

class Categoria(BaseCategoria):
    ordem = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'restaurante_categorias'
        ordering = ['ordem', 'nome']
```

---

## 2. REFATORAÇÃO DE VIEWSETS

### ANTES (Repetido 8 vezes)
```python
# backend/servicos/views.py
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

# backend/restaurante/views.py
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
```

### DEPOIS (ViewSet genérico)
```python
# backend/core/views.py
class BaseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(is_active=True)
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_update(self, serializer):
        serializer.save()

# backend/servicos/views.py
from core.views import BaseModelViewSet

class CategoriaViewSet(BaseModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
```

---

## 3. REFATORAÇÃO DE SETTINGS

### ANTES (4 arquivos com 80% duplicação)
```python
# backend/config/settings.py (1200 linhas)
INSTALLED_APPS = [...]
MIDDLEWARE = [...]
REST_FRAMEWORK = {...}
SIMPLE_JWT = {...}
DATABASES = {...}

# backend/config/settings_production.py (150 linhas)
# Duplica 80% de settings.py
INSTALLED_APPS = [...]  # Idêntico
MIDDLEWARE = [...]      # Idêntico
REST_FRAMEWORK = {...}  # Idêntico
SIMPLE_JWT = {...}      # Idêntico
DATABASES = {...}       # Diferente

# backend/config/settings_single_db.py (120 linhas)
# Duplica 70% de settings.py
INSTALLED_APPS = [...]  # Idêntico
MIDDLEWARE = [...]      # Idêntico
REST_FRAMEWORK = {...}  # Idêntico
SIMPLE_JWT = {...}      # Idêntico
DATABASES = {...}       # Diferente
```

### DEPOIS (Arquivo base + overrides)
```python
# backend/config/settings_base.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'stores',
    'products',
    'suporte',
    'tenants',
    'superadmin',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'tenants.middleware.TenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# backend/config/settings.py
from .settings_base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_superadmin.sqlite3',
    },
    'suporte': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_suporte.sqlite3',
    },
}

# backend/config/settings_production.py
from .settings_base import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
    )
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 4. REFATORAÇÃO DE COMPONENTES REACT

### ANTES (Duplicado em 4 páginas)
```typescript
// frontend/app/(auth)/login/page.tsx
export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiClient.post('/auth/token/', {
        username,
        password,
      });
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      router.push('/dashboard');
    } catch (err) {
      setError('Credenciais inválidas');
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Usuário"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Senha"
        />
        {error && <p className="error">{error}</p>}
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

// frontend/app/(auth)/loja/page.tsx
// Código idêntico...

// frontend/app/(auth)/superadmin/page.tsx
// Código idêntico...

// frontend/app/(auth)/suporte/page.tsx
// Código idêntico...
```

### DEPOIS (Componente reutilizável)
```typescript
// frontend/components/auth/LoginForm.tsx
interface LoginFormProps {
  userType: 'superadmin' | 'suporte' | 'loja';
  onSuccess?: (tokens: AuthTokens) => void;
  redirectPath?: string;
}

export function LoginForm({
  userType,
  onSuccess,
  redirectPath = '/dashboard',
}: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiClient.post('/auth/token/', {
        username,
        password,
      });
      
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      localStorage.setItem('user_type', userType);

      if (onSuccess) {
        onSuccess(response.data);
      }

      router.push(redirectPath);
    } catch (err) {
      setError('Credenciais inválidas');
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Usuário"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Senha"
        />
        {error && <p className="error">{error}</p>}
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

// frontend/app/(auth)/login/page.tsx
export default function LoginPage() {
  return <LoginForm userType="superadmin" />;
}

// frontend/app/(auth)/loja/page.tsx
export default function LojaLoginPage() {
  return <LoginForm userType="loja" />;
}

// frontend/app/(auth)/superadmin/page.tsx
export default function SuperAdminLoginPage() {
  return <LoginForm userType="superadmin" />;
}

// frontend/app/(auth)/suporte/page.tsx
export default function SuporteLoginPage() {
  return <LoginForm userType="suporte" />;
}
```

---

## 5. REFATORAÇÃO DE HOOKS

### ANTES (Lógica duplicada em componentes)
```typescript
// frontend/app/(dashboard)/dashboard/page.tsx
export default function DashboardPage() {
  const [stores, setStores] = useState([]);
  const [currentStore, setCurrentStore] = useState(null);

  useEffect(() => {
    loadStores();
  }, []);

  const loadStores = async () => {
    try {
      const response = await apiClient.get('/stores/');
      setStores(response.data.results || response.data);
    } catch (error) {
      console.error('Erro ao carregar lojas:', error);
    }
  };

  const switchStore = (storeId: number) => {
    const store = stores.find((s) => s.id === storeId);
    if (store) {
      setCurrentStore(store);
    }
  };

  return (
    <div>
      {/* Usar stores, currentStore, switchStore */}
    </div>
  );
}

// frontend/app/(dashboard)/loja/page.tsx
// Código idêntico...
```

### DEPOIS (Hook customizado)
```typescript
// frontend/hooks/use-tenant.ts
export function useTenant() {
  const { currentStore, stores, setCurrentStore, setStores } = useTenantStore();

  useEffect(() => {
    if (stores.length === 0) {
      loadStores();
    }
  }, []);

  const loadStores = async () => {
    try {
      const response = await apiClient.get('/stores/');
      setStores(response.data.results || response.data);
    } catch (error) {
      console.error('Erro ao carregar lojas:', error);
    }
  };

  const switchStore = (storeId: number) => {
    const store = stores.find((s) => s.id === storeId);
    if (store) {
      setCurrentStore(store);
    }
  };

  return {
    currentStore,
    stores,
    switchStore,
    loadStores,
  };
}

// frontend/app/(dashboard)/dashboard/page.tsx
export default function DashboardPage() {
  const { stores, currentStore, switchStore } = useTenant();

  return (
    <div>
      {/* Usar stores, currentStore, switchStore */}
    </div>
  );
}

// frontend/app/(dashboard)/loja/page.tsx
export default function LojaPage() {
  const { stores, currentStore, switchStore } = useTenant();

  return (
    <div>
      {/* Usar stores, currentStore, switchStore */}
    </div>
  );
}
```

---

## 6. CONSOLIDAÇÃO DE .ENV

### ANTES (4 arquivos)
```
frontend/.env.local
frontend/.env.local.example
frontend/.env.production
frontend/.env.vercel
```

### DEPOIS (2 arquivos)
```
frontend/.env.example
frontend/.env.local (gitignored)
frontend/.env.production (gitignored)
```

**frontend/.env.example**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=LWK Sistemas
```

**frontend/.env.local** (desenvolvimento)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**frontend/.env.production** (produção)
```
NEXT_PUBLIC_API_URL=https://api.lwksistemas.com
```

---

## 7. LIMPEZA DE CÓDIGO MORTO

### Remover
```bash
# Backend
rm backend/db_*.sqlite3
rm backend/criar_banco_*.py
rm backend/migrar_*.py
rm backend/testar_*.py
rm backend/limpar_*.py
rm backend/*/models_single_db.py

# Frontend
rm frontend/.env.vercel
rm frontend/.env.local.example
```

### Atualizar .gitignore
```
# Backend
*.sqlite3
*.pyc
__pycache__/
.env
.venv/
venv/

# Frontend
.env.local
.env.production
.next/
.vercel/
node_modules/
dist/
build/
```

---

## 📊 IMPACTO DAS MUDANÇAS

### Redução de Código
- **Modelos:** 40% menos linhas
- **Views:** 30% menos linhas
- **Settings:** 60% menos linhas
- **Componentes React:** 50% menos linhas

### Benefícios
- ✅ Manutenção mais fácil
- ✅ Menos bugs
- ✅ Código mais legível
- ✅ Onboarding mais rápido
- ✅ Repositório menor
