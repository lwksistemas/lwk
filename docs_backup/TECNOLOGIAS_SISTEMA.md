# 🛠️ Tecnologias e Ferramentas do Sistema LWK

**Data**: 17/01/2026  
**Sistema**: LWK Sistemas - Gestão de Lojas Multi-Tenant  
**Versão**: 1.0

---

## 📋 Índice

1. [Visão Geral da Arquitetura](#visão-geral)
2. [Frontend (Interface do Usuário)](#frontend)
3. [Backend (Servidor e Lógica)](#backend)
4. [Banco de Dados](#banco-de-dados)
5. [Hospedagem e Deploy](#hospedagem)
6. [Ferramentas de Desenvolvimento](#ferramentas)
7. [Segurança e Autenticação](#segurança)
8. [Custos Totais](#custos)

---

## 🏗️ Visão Geral da Arquitetura

### Diagrama Completo

```
┌─────────────────────────────────────────────────────────────┐
│                      USUÁRIO FINAL                          │
│                  (Navegador Web)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (Vercel)                         │
│              https://lwksistemas.com.br                     │
│                                                             │
│  Tecnologias:                                               │
│  • Next.js 15.5.9 (Framework React)                        │
│  • React 18 (Biblioteca UI)                                │
│  • TypeScript (Linguagem)                                  │
│  • Tailwind CSS (Estilização)                              │
│  • Vercel (Hospedagem)                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/HTTPS Requests
                         │ (REST API)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (Heroku)                          │
│            https://api.lwksistemas.com.br                   │
│                                                             │
│  Tecnologias:                                               │
│  • Python 3.12 (Linguagem)                                 │
│  • Django 4.2 (Framework Web)                              │
│  • Django REST Framework (API)                             │
│  • Gunicorn (Servidor WSGI)                                │
│  • Heroku (Hospedagem)                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ SQL Queries
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  BANCO DE DADOS                             │
│                                                             │
│  Tecnologia:                                                │
│  • SQLite 3 (Banco de Dados)                               │
│  • Multi-Database (3 bancos isolados)                      │
│    - db_superadmin.sqlite3                                 │
│    - db_suporte.sqlite3                                    │
│    - db_loja_*.sqlite3 (um por loja)                       │
└─────────────────────────────────────────────────────────────┘
```



---

## 💻 FRONTEND (Interface do Usuário)

### 1. Next.js 15.5.9
**O que é**: Framework React para aplicações web modernas  
**Função**: Base do frontend, gerencia rotas, renderização, otimizações  
**Por que usamos**: Melhor framework React, SEO, performance, facilidade

```javascript
// Exemplo de código Next.js
export default function LoginPage() {
  return <div>Página de Login</div>
}
```

**Recursos usados**:
- ✅ App Router (rotas modernas)
- ✅ Server Components
- ✅ Dynamic Routes (/loja/[slug]/login)
- ✅ Middleware (autenticação)
- ✅ Image Optimization

**Custo**: Gratuito (open source)

---

### 2. React 18
**O que é**: Biblioteca JavaScript para criar interfaces  
**Função**: Componentes reutilizáveis, gerenciamento de estado  
**Por que usamos**: Padrão da indústria, grande comunidade

```typescript
// Exemplo de componente React
const Button = () => {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(count + 1)}>
    Cliques: {count}
  </button>
}
```

**Recursos usados**:
- ✅ Hooks (useState, useEffect, useRouter)
- ✅ Components funcionais
- ✅ Context API
- ✅ Suspense

**Custo**: Gratuito (open source)

---

### 3. TypeScript
**O que é**: JavaScript com tipos (mais seguro)  
**Função**: Prevenir erros, autocompletar código  
**Por que usamos**: Código mais confiável, menos bugs

```typescript
// Exemplo TypeScript
interface Loja {
  id: number
  nome: string
  slug: string
  is_active: boolean
}

const lojas: Loja[] = []
```

**Benefícios**:
- ✅ Detecta erros antes de rodar
- ✅ Autocompletar inteligente
- ✅ Refatoração segura
- ✅ Documentação automática

**Custo**: Gratuito (open source)

---

### 4. Tailwind CSS 3
**O que é**: Framework CSS utilitário  
**Função**: Estilização rápida e responsiva  
**Por que usamos**: Produtividade, design consistente

```html
<!-- Exemplo Tailwind -->
<button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Clique Aqui
</button>
```

**Recursos usados**:
- ✅ Utility classes
- ✅ Responsive design
- ✅ Dark mode support
- ✅ Custom colors

**Custo**: Gratuito (open source)



---

## 🔧 BACKEND (Servidor e Lógica)

### 1. Python 3.12
**O que é**: Linguagem de programação  
**Função**: Lógica do servidor, processamento de dados  
**Por que usamos**: Fácil de aprender, poderosa, grande comunidade

```python
# Exemplo Python
def calcular_total(preco, quantidade):
    return preco * quantidade

total = calcular_total(10.50, 3)  # 31.50
```

**Recursos usados**:
- ✅ Type hints
- ✅ List comprehensions
- ✅ Decorators
- ✅ Context managers

**Custo**: Gratuito (open source)

---

### 2. Django 4.2
**O que é**: Framework web Python  
**Função**: Estrutura do backend, ORM, admin, segurança  
**Por que usamos**: Completo, seguro, "batteries included"

```python
# Exemplo Django Model
class Loja(models.Model):
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Recursos usados**:
- ✅ ORM (Object-Relational Mapping)
- ✅ Admin interface
- ✅ Authentication system
- ✅ Migrations
- ✅ Security features (CSRF, XSS, SQL Injection)

**Custo**: Gratuito (open source)

---

### 3. Django REST Framework (DRF)
**O que é**: Biblioteca para criar APIs REST  
**Função**: Endpoints da API, serialização, autenticação  
**Por que usamos**: Padrão para APIs Django, muito completo

```python
# Exemplo DRF ViewSet
class LojaViewSet(viewsets.ModelViewSet):
    queryset = Loja.objects.all()
    serializer_class = LojaSerializer
    permission_classes = [IsAuthenticated]
```

**Recursos usados**:
- ✅ ViewSets e Routers
- ✅ Serializers
- ✅ Authentication (JWT)
- ✅ Permissions
- ✅ Pagination
- ✅ Throttling

**Custo**: Gratuito (open source)

---

### 4. Simple JWT
**O que é**: Biblioteca para autenticação JWT  
**Função**: Tokens de acesso, refresh tokens  
**Por que usamos**: Autenticação stateless, segura

```python
# Exemplo JWT
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Recursos**:
- ✅ Access tokens (1 hora)
- ✅ Refresh tokens (7 dias)
- ✅ Token rotation
- ✅ Blacklist

**Custo**: Gratuito (open source)

---

### 5. Gunicorn
**O que é**: Servidor WSGI Python  
**Função**: Servir aplicação Django em produção  
**Por que usamos**: Robusto, performático, padrão da indústria

```bash
# Configuração Gunicorn
gunicorn config.wsgi \
  --workers 2 \
  --threads 4 \
  --worker-class gthread
```

**Configuração atual**:
- ✅ 2 workers (processos)
- ✅ 4 threads por worker
- ✅ 8 threads total
- ✅ Timeout 30s

**Custo**: Gratuito (open source)



---

## 💾 BANCO DE DADOS

### SQLite 3
**O que é**: Banco de dados relacional embutido  
**Função**: Armazenar dados (lojas, usuários, produtos, etc)  
**Por que usamos**: Simples, sem servidor separado, bom para começar

```sql
-- Exemplo SQL
SELECT * FROM superadmin_loja 
WHERE is_active = 1 
ORDER BY created_at DESC;
```

**Arquitetura Multi-Database**:
```
db_superadmin.sqlite3    → Gerenciamento geral
db_suporte.sqlite3       → Sistema de chamados
db_loja_harmonis.sqlite3 → Dados da loja Harmonis
db_loja_felix.sqlite3    → Dados da loja Felix
...
```

**Vantagens**:
- ✅ Zero configuração
- ✅ Arquivo único
- ✅ Rápido para leitura
- ✅ Backup simples (copiar arquivo)

**Limitações**:
- ⚠️ Máximo 50 requisições/segundo
- ⚠️ Não ideal para >50 lojas
- ⚠️ Sem replicação nativa

**Custo**: Gratuito (open source)

**Migração futura**: PostgreSQL (quando atingir 40+ lojas)

---

## 🌐 HOSPEDAGEM E DEPLOY

### 1. Vercel (Frontend)
**O que é**: Plataforma de hospedagem para frontend  
**Função**: Hospedar Next.js, CDN global, SSL  
**Por que usamos**: Melhor para Next.js, otimizações automáticas

**Plano**: Pro ($20/mês)

**Recursos**:
- ✅ CDN global (150+ localizações)
- ✅ SSL/HTTPS automático
- ✅ Deploy automático (Git push)
- ✅ Preview deployments
- ✅ Analytics
- ✅ Edge Network
- ✅ Image optimization
- ✅ 6.000 builds/mês
- ✅ 1 TB bandwidth/mês

**Comandos**:
```bash
vercel --prod  # Deploy para produção
vercel logs    # Ver logs
```

**URL**: https://lwksistemas.com.br

---

### 2. Heroku (Backend)
**O que é**: Plataforma de hospedagem para backend  
**Função**: Hospedar Django, executar Python  
**Por que usamos**: Fácil de usar, suporte Python/Django

**Plano**: Hobby ($7/mês)

**Recursos**:
- ✅ 512 MB RAM
- ✅ 1 CPU core
- ✅ SSL/HTTPS
- ✅ Git deployment
- ✅ Logs
- ✅ Metrics
- ✅ Add-ons disponíveis

**Comandos**:
```bash
git push heroku master  # Deploy
heroku logs --tail      # Ver logs
heroku ps               # Ver status
```

**URL**: https://api.lwksistemas.com.br

---

### 3. Registro.br (Domínio)
**O que é**: Registro de domínio .com.br  
**Função**: Domínio personalizado  
**Por que usamos**: Domínio brasileiro, confiável

**Custo**: ~$3/mês (R$ 40/ano)

**Configuração DNS**:
```
lwksistemas.com.br        → Vercel (Frontend)
api.lwksistemas.com.br    → Heroku (Backend)
```



---

## 🛠️ FERRAMENTAS DE DESENVOLVIMENTO

### 1. Git
**O que é**: Sistema de controle de versão  
**Função**: Gerenciar código, histórico de mudanças  
**Por que usamos**: Padrão da indústria, essencial

```bash
git add .
git commit -m "feat: nova funcionalidade"
git push origin master
```

**Custo**: Gratuito

---

### 2. GitHub
**O que é**: Plataforma de hospedagem de código  
**Função**: Repositório remoto, colaboração  
**Por que usamos**: Integração com Vercel/Heroku

**Custo**: Gratuito (repositório privado)

---

### 3. VS Code / Kiro
**O que é**: Editor de código  
**Função**: Escrever e editar código  
**Por que usamos**: Melhor editor, extensões, integração Git

**Custo**: Gratuito

---

### 4. npm (Node Package Manager)
**O que é**: Gerenciador de pacotes JavaScript  
**Função**: Instalar dependências do frontend  

```bash
npm install          # Instalar dependências
npm run dev          # Rodar em desenvolvimento
npm run build        # Build para produção
```

**Custo**: Gratuito

---

### 5. pip (Python Package Manager)
**O que é**: Gerenciador de pacotes Python  
**Função**: Instalar dependências do backend  

```bash
pip install -r requirements.txt  # Instalar dependências
pip freeze > requirements.txt    # Salvar dependências
```

**Custo**: Gratuito

---

## 🔒 SEGURANÇA E AUTENTICAÇÃO

### 1. JWT (JSON Web Tokens)
**O que é**: Padrão de autenticação  
**Função**: Tokens de acesso seguros  

```
Header.Payload.Signature
eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Configuração**:
- ✅ Access token: 1 hora
- ✅ Refresh token: 7 dias
- ✅ Rotation automática
- ✅ Blacklist após logout

---

### 2. HTTPS/SSL
**O que é**: Protocolo seguro  
**Função**: Criptografar comunicação  

**Implementação**:
- ✅ Vercel: SSL automático (Let's Encrypt)
- ✅ Heroku: SSL automático
- ✅ Certificados renovados automaticamente

---

### 3. CORS (Cross-Origin Resource Sharing)
**O que é**: Política de segurança  
**Função**: Controlar quem pode acessar a API  

```python
CORS_ALLOWED_ORIGINS = [
    'https://lwksistemas.com.br',
]
```

---

### 4. Django Security Features
**Recursos de segurança**:
- ✅ CSRF Protection
- ✅ XSS Protection
- ✅ SQL Injection Protection
- ✅ Clickjacking Protection
- ✅ Password hashing (PBKDF2)
- ✅ Session security



---

## 📦 BIBLIOTECAS E DEPENDÊNCIAS

### Frontend (package.json)
```json
{
  "dependencies": {
    "next": "15.5.9",           // Framework React
    "react": "^18",             // Biblioteca UI
    "react-dom": "^18",         // React para web
    "typescript": "^5",         // Tipagem
    "tailwindcss": "^3",        // CSS
    "autoprefixer": "^10",      // CSS prefixes
    "postcss": "^8"             // CSS processor
  }
}
```

### Backend (requirements.txt)
```txt
Django==4.2.11                    # Framework web
djangorestframework==3.14.0       # API REST
djangorestframework-simplejwt==5.3.1  # JWT
django-cors-headers==4.3.1        # CORS
django-tenants==3.5.0             # Multi-tenant
psycopg2-binary==2.9.9            # PostgreSQL (futuro)
python-decouple==3.8              # Variáveis ambiente
gunicorn==21.2.0                  # Servidor WSGI
whitenoise==6.6.0                 # Static files
dj-database-url==2.1.0            # Database config
```

---

## 💰 CUSTOS TOTAIS

### Custos Mensais

```
┌─────────────────────────────────────────────────┐
│  INFRAESTRUTURA                                 │
├─────────────────────────────────────────────────┤
│  Vercel Pro (Frontend)         $20/mês          │
│  Heroku Hobby (Backend)        $7/mês           │
│  Domínio .com.br               $3/mês           │
├─────────────────────────────────────────────────┤
│  TOTAL                         $30/mês          │
│                                (R$ 150/mês)     │
└─────────────────────────────────────────────────┘
```

### Custos Anuais

```
Vercel:    $20 × 12 = $240/ano
Heroku:    $7 × 12  = $84/ano
Domínio:   $40/ano
─────────────────────────────
TOTAL:     $364/ano (R$ 1.820/ano)
```

### Breakdown Percentual

```
Vercel (Frontend):     67% ($20)
Heroku (Backend):      23% ($7)
Domínio:               10% ($3)
```

### Ferramentas Gratuitas

```
✅ Next.js          - $0
✅ React            - $0
✅ TypeScript       - $0
✅ Tailwind CSS     - $0
✅ Django           - $0
✅ Python           - $0
✅ SQLite           - $0
✅ Git              - $0
✅ GitHub           - $0
✅ VS Code          - $0
✅ npm              - $0
✅ pip              - $0
─────────────────────────
Total Economizado: Milhares de dólares!
```

---

## 📊 COMPARAÇÃO COM ALTERNATIVAS

### Frontend Hosting

| Plataforma | Custo/mês | CDN | SSL | Next.js |
|------------|-----------|-----|-----|---------|
| **Vercel** | $20 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| Netlify | $19 | ✅ | ✅ | ⭐⭐⭐⭐ |
| AWS | $10-30 | ✅ | ✅ | ⭐⭐ |
| Heroku | $7 | ❌ | ✅ | ⭐⭐ |

### Backend Hosting

| Plataforma | Custo/mês | RAM | CPU | Python |
|------------|-----------|-----|-----|--------|
| **Heroku** | $7 | 512MB | 1 | ⭐⭐⭐⭐⭐ |
| Railway | $5 | 512MB | 1 | ⭐⭐⭐⭐ |
| Render | $7 | 512MB | 1 | ⭐⭐⭐⭐ |
| AWS | $15+ | 1GB | 1 | ⭐⭐⭐ |

### Banco de Dados

| Banco | Custo/mês | Escalabilidade | Complexidade |
|-------|-----------|----------------|--------------|
| **SQLite** | $0 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| PostgreSQL | $0-50 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| MySQL | $0-50 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| MongoDB | $0-60 | ⭐⭐⭐⭐⭐ | ⭐⭐ |



---

## 🎯 STACK TECNOLÓGICO RESUMIDO

### Frontend Stack
```
┌─────────────────────────────────┐
│  FRONTEND                       │
├─────────────────────────────────┤
│  Framework:    Next.js 15       │
│  Biblioteca:   React 18         │
│  Linguagem:    TypeScript       │
│  Estilo:       Tailwind CSS     │
│  Hospedagem:   Vercel Pro       │
│  Custo:        $20/mês          │
└─────────────────────────────────┘
```

### Backend Stack
```
┌─────────────────────────────────┐
│  BACKEND                        │
├─────────────────────────────────┤
│  Linguagem:    Python 3.12      │
│  Framework:    Django 4.2       │
│  API:          DRF 3.14         │
│  Servidor:     Gunicorn         │
│  Hospedagem:   Heroku Hobby     │
│  Custo:        $7/mês           │
└─────────────────────────────────┘
```

### Database Stack
```
┌─────────────────────────────────┐
│  BANCO DE DADOS                 │
├─────────────────────────────────┤
│  Tipo:         SQLite 3         │
│  Arquitetura:  Multi-Database   │
│  Bancos:       3+ isolados      │
│  Hospedagem:   Heroku (mesmo)   │
│  Custo:        $0 (incluído)    │
└─────────────────────────────────┘
```

---

## 🚀 FLUXO DE DESENVOLVIMENTO

### 1. Desenvolvimento Local
```bash
# Frontend
cd frontend
npm install
npm run dev  # http://localhost:3000

# Backend
cd backend
pip install -r requirements.txt
python manage.py runserver  # http://localhost:8000
```

### 2. Commit e Push
```bash
git add .
git commit -m "feat: nova funcionalidade"
git push origin master
```

### 3. Deploy Automático
```bash
# Frontend (Vercel)
cd frontend
vercel --prod

# Backend (Heroku)
git push heroku master
```

### 4. Verificação
```bash
# Testar frontend
curl https://lwksistemas.com.br

# Testar backend
curl https://api.lwksistemas.com.br/api/
```

---

## 📈 EVOLUÇÃO FUTURA

### Quando Migrar Tecnologias?

#### PostgreSQL (Banco de Dados)
```
Migrar quando:
✅ 40+ lojas ativas
✅ 1000+ requisições/minuto
✅ Precisar de replicação
✅ Precisar de full-text search

Custo adicional: $0-50/mês
```

#### Redis (Cache)
```
Migrar quando:
✅ 50+ lojas ativas
✅ Precisar de cache distribuído
✅ Precisar de sessions compartilhadas
✅ Precisar de pub/sub

Custo adicional: $10-30/mês
```

#### CDN para Assets
```
Migrar quando:
✅ Muitas imagens/vídeos
✅ Tráfego internacional alto
✅ Precisar de edge caching

Custo adicional: $10-50/mês
```

#### Upgrade Heroku
```
Migrar quando:
✅ 50+ lojas ativas
✅ CPU/RAM insuficiente
✅ Precisar de mais workers

Standard-1X: $25/mês (+$18)
Standard-2X: $50/mês (+$43)
```

---

## 🎓 RECURSOS DE APRENDIZADO

### Documentação Oficial

```
Next.js:     https://nextjs.org/docs
React:       https://react.dev
TypeScript:  https://typescriptlang.org/docs
Tailwind:    https://tailwindcss.com/docs
Django:      https://docs.djangoproject.com
DRF:         https://django-rest-framework.org
Python:      https://docs.python.org
Vercel:      https://vercel.com/docs
Heroku:      https://devcenter.heroku.com
```

### Tutoriais Recomendados

```
Next.js:     https://nextjs.org/learn
React:       https://react.dev/learn
Django:      https://docs.djangoproject.com/en/4.2/intro/tutorial01/
Python:      https://docs.python.org/3/tutorial/
```

---

## ✅ CHECKLIST DE TECNOLOGIAS

### Frontend
- [x] Next.js 15.5.9
- [x] React 18
- [x] TypeScript 5
- [x] Tailwind CSS 3
- [x] Vercel (hospedagem)

### Backend
- [x] Python 3.12
- [x] Django 4.2
- [x] Django REST Framework 3.14
- [x] Simple JWT 5.3
- [x] Gunicorn 21.2
- [x] Heroku (hospedagem)

### Banco de Dados
- [x] SQLite 3
- [x] Multi-database architecture
- [ ] PostgreSQL (futuro)
- [ ] Redis (futuro)

### DevOps
- [x] Git
- [x] GitHub
- [x] Vercel CLI
- [x] Heroku CLI
- [x] npm
- [x] pip

### Segurança
- [x] JWT Authentication
- [x] HTTPS/SSL
- [x] CORS
- [x] Django Security
- [x] Password Hashing

---

## 🎯 CONCLUSÃO

### Stack Escolhido

O sistema LWK usa um **stack moderno e eficiente**:

**Frontend**: Next.js + React + TypeScript + Tailwind  
**Backend**: Python + Django + DRF  
**Database**: SQLite (multi-database)  
**Hosting**: Vercel + Heroku  

### Vantagens

```
✅ Tecnologias modernas e populares
✅ Grande comunidade e suporte
✅ Fácil de aprender e manter
✅ Boa performance
✅ Custo acessível ($30/mês)
✅ Escalável (pode crescer)
✅ Seguro (boas práticas)
```

### Custo Total

```
Infraestrutura:  $30/mês (R$ 150/mês)
Ferramentas:     $0/mês (todas gratuitas!)
─────────────────────────────────────
TOTAL:           $30/mês (R$ 150/mês)
```

---

**Sistema**: LWK Sistemas  
**URLs**:
- Frontend: https://lwksistemas.com.br
- Backend: https://api.lwksistemas.com.br

**Repositório**: GitHub (privado)  
**Versão**: 1.0  
**Data**: 17/01/2026
