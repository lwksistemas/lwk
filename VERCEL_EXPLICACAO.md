# 📘 O que é Vercel e sua Função no Sistema

**Data**: 17/01/2026  
**Versão**: 1.0

---

## 🎯 O que é Vercel?

**Vercel** é uma plataforma de hospedagem especializada em aplicações **frontend** (interface do usuário). É a empresa criadora do **Next.js**, o framework que usamos no frontend do sistema.

### Analogia Simples
```
Imagine uma loja física:
- VERCEL = A vitrine da loja (o que o cliente vê)
- HEROKU = O estoque e gerenciamento (backend/banco de dados)
```

---

## 🏗️ Função do Vercel no Nosso Sistema

### Arquitetura Atual

```
┌─────────────────────────────────────────────────────────┐
│                    USUÁRIO FINAL                        │
│              (Cliente no navegador)                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  VERCEL (Frontend)                      │
│         https://lwksistemas.com.br                      │
│                                                         │
│  • Hospeda o código Next.js/React                      │
│  • Serve páginas HTML, CSS, JavaScript                 │
│  • Interface visual (botões, formulários, etc)         │
│  • Otimização automática de imagens                    │
│  • CDN global (carrega rápido no mundo todo)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Faz requisições HTTP
                     ↓
┌─────────────────────────────────────────────────────────┐
│                HEROKU (Backend)                         │
│         https://api.lwksistemas.com.br                  │
│                                                         │
│  • Hospeda o código Python/Django                      │
│  • Processa lógica de negócio                          │
│  • Gerencia banco de dados SQLite                      │
│  • APIs REST (endpoints)                               │
│  • Autenticação JWT                                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 O que o Vercel Faz Especificamente?

### 1. Hospedagem do Frontend
```
Vercel hospeda:
✅ Páginas Next.js (React)
✅ Arquivos HTML, CSS, JavaScript
✅ Imagens e assets estáticos
✅ Rotas dinâmicas (/loja/[slug]/login)
```

### 2. Deploy Automático
```bash
# Quando você faz deploy:
cd frontend
vercel --prod

# Vercel automaticamente:
1. Faz build do Next.js (npm run build)
2. Otimiza o código (minificação, tree-shaking)
3. Distribui para CDN global
4. Atualiza o domínio lwksistemas.com.br
5. Gera certificado SSL (HTTPS)
```

### 3. CDN Global (Content Delivery Network)
```
Sem CDN (servidor único):
Brasil → Servidor EUA → 200ms de latência

Com CDN Vercel:
Brasil → Servidor São Paulo → 20ms de latência
EUA → Servidor Nova York → 15ms de latência
Europa → Servidor Londres → 18ms de latência

Resultado: Site 10x mais rápido!
```

### 4. Otimizações Automáticas
```
Vercel faz automaticamente:
✅ Compressão de imagens (WebP, AVIF)
✅ Code splitting (carrega só o necessário)
✅ Cache inteligente
✅ Pré-renderização de páginas estáticas
✅ Certificado SSL gratuito
✅ HTTP/2 e HTTP/3
```

---

## 💰 Custos do Vercel

### Plano Atual: **Pro ($20/mês)**

```
┌─────────────────────────────────────────────────────┐
│              PLANO VERCEL PRO                       │
├─────────────────────────────────────────────────────┤
│  Custo:              $20/mês (R$ 100/mês)          │
│  Domínio Custom:     ✅ Incluído                   │
│  SSL/HTTPS:          ✅ Gratuito                   │
│  CDN Global:         ✅ Incluído                   │
│  Builds:             6.000/mês                     │
│  Bandwidth:          1 TB/mês                      │
│  Imagens:            5.000 otimizações/mês         │
│  Suporte:            Email                         │
└─────────────────────────────────────────────────────┘
```

### Comparação de Planos

| Recurso | Hobby (Grátis) | Pro ($20/mês) | Enterprise |
|---------|----------------|---------------|------------|
| **Domínio Custom** | ❌ Não | ✅ Sim | ✅ Sim |
| **Builds/mês** | 100 | 6.000 | Ilimitado |
| **Bandwidth** | 100 GB | 1 TB | Ilimitado |
| **Membros Team** | 1 | 10 | Ilimitado |
| **Suporte** | Community | Email | Prioritário |
| **Analytics** | Básico | Avançado | Enterprise |
| **Custo** | $0 | $20/mês | Custom |

### Por que Usamos o Plano Pro?

```
✅ Domínio customizado (lwksistemas.com.br)
✅ Mais builds (6.000 vs 100)
✅ Mais bandwidth (1 TB vs 100 GB)
✅ Suporte profissional
✅ Analytics avançado
✅ Múltiplos membros no time
```

---

## 🔄 Fluxo de Funcionamento

### Quando um Usuário Acessa o Sistema

```
1. Usuário digita: https://lwksistemas.com.br
   ↓
2. DNS resolve para Vercel
   ↓
3. Vercel serve a página inicial (HTML/CSS/JS)
   ↓
4. Usuário clica em "SuperAdmin"
   ↓
5. Vercel serve a página /superadmin/login
   ↓
6. Usuário preenche login e senha
   ↓
7. Frontend (Vercel) envia requisição para Backend (Heroku)
   POST https://api.lwksistemas.com.br/api/token/
   ↓
8. Backend (Heroku) valida credenciais
   ↓
9. Backend retorna token JWT
   ↓
10. Frontend armazena token e redireciona para dashboard
    ↓
11. Frontend faz requisições autenticadas para Backend
    GET https://api.lwksistemas.com.br/api/superadmin/lojas/
    Headers: Authorization: Bearer <token>
```

---

## 🆚 Vercel vs Outras Opções

### Comparação com Alternativas

| Plataforma | Custo/mês | Especialidade | Facilidade |
|------------|-----------|---------------|------------|
| **Vercel** | $20 | Next.js/React | ⭐⭐⭐⭐⭐ |
| Netlify | $19 | Jamstack | ⭐⭐⭐⭐ |
| AWS S3 + CloudFront | $5-15 | Geral | ⭐⭐ |
| DigitalOcean | $12 | VPS | ⭐⭐ |
| GitHub Pages | $0 | Sites estáticos | ⭐⭐⭐ |

### Por que Escolhemos Vercel?

```
✅ Criadores do Next.js (melhor integração)
✅ Deploy automático com Git
✅ CDN global incluído
✅ Otimizações automáticas
✅ Zero configuração
✅ Suporte excelente
✅ Analytics integrado
✅ Preview deployments (testar antes de publicar)
```

---

## 📊 Custos Totais do Sistema

### Infraestrutura Atual

```
┌─────────────────────────────────────────────────────┐
│           CUSTOS MENSAIS DO SISTEMA                 │
├─────────────────────────────────────────────────────┤
│  Vercel Pro (Frontend):        $20/mês              │
│  Heroku Hobby (Backend):       $7/mês               │
│  Domínio (.com.br):            ~$3/mês              │
├─────────────────────────────────────────────────────┤
│  TOTAL:                        $30/mês              │
│                                (R$ 150/mês)         │
└─────────────────────────────────────────────────────┘
```

### Breakdown de Custos

```
Frontend (Vercel):     67% ($20)
Backend (Heroku):      23% ($7)
Domínio:               10% ($3)
─────────────────────────────
Total:                100% ($30)
```

---

## 🎯 Benefícios do Vercel

### 1. Performance
```
✅ CDN global (150+ localizações)
✅ Edge Network (servidores próximos ao usuário)
✅ Cache inteligente
✅ HTTP/2 e HTTP/3
✅ Compressão automática (Brotli, Gzip)

Resultado: Site carrega em 200-500ms
```

### 2. Segurança
```
✅ SSL/HTTPS automático (Let's Encrypt)
✅ DDoS protection
✅ Firewall integrado
✅ Headers de segurança automáticos
✅ Isolamento de builds

Resultado: Site seguro por padrão
```

### 3. Escalabilidade
```
✅ Auto-scaling (escala automaticamente)
✅ Suporta milhões de requisições
✅ Zero downtime em deploys
✅ Rollback instantâneo

Resultado: Aguenta picos de tráfego
```

### 4. Developer Experience
```
✅ Deploy em 1 comando (vercel --prod)
✅ Preview deployments (testar antes)
✅ Git integration (deploy automático)
✅ Logs em tempo real
✅ Analytics integrado

Resultado: Desenvolvimento mais rápido
```

---

## 🔍 Monitoramento no Vercel

### Dashboard Vercel

```
Você pode acessar:
https://vercel.com/dashboard

Ver:
✅ Status dos deploys
✅ Logs de build
✅ Analytics de tráfego
✅ Performance metrics
✅ Uso de recursos (bandwidth, builds)
✅ Domínios configurados
```

### Métricas Disponíveis

```
┌─────────────────────────────────────────┐
│  ANALYTICS VERCEL                       │
├─────────────────────────────────────────┤
│  Pageviews:        10.000/mês           │
│  Unique Visitors:  2.500/mês            │
│  Bandwidth Used:   50 GB/1 TB           │
│  Builds Used:      120/6.000            │
│  Avg Load Time:    350ms                │
│  Core Web Vitals:  ✅ Bom               │
└─────────────────────────────────────────┘
```

---

## 🚀 Comandos Úteis do Vercel

### Deploy
```bash
# Deploy para produção
cd frontend
vercel --prod

# Deploy para preview (teste)
vercel

# Ver logs
vercel logs

# Ver domínios
vercel domains ls

# Ver projetos
vercel ls
```

### Configuração
```bash
# Login
vercel login

# Link projeto
vercel link

# Ver variáveis de ambiente
vercel env ls

# Adicionar variável
vercel env add NEXT_PUBLIC_API_URL
```

---

## 🔄 Alternativas ao Vercel (Se Quiser Economizar)

### Opção 1: Netlify (Similar ao Vercel)
```
Custo: $19/mês
Prós: Similar ao Vercel, bom suporte
Contras: Menos otimizado para Next.js
```

### Opção 2: Cloudflare Pages (Mais Barato)
```
Custo: $0-5/mês
Prós: Muito barato, CDN excelente
Contras: Menos features, mais configuração
```

### Opção 3: AWS S3 + CloudFront (Mais Controle)
```
Custo: $5-10/mês
Prós: Muito controle, escalável
Contras: Complexo de configurar
```

### Opção 4: Hospedar no Heroku (Tudo Junto)
```
Custo: $0 (usar mesmo servidor do backend)
Prós: Economiza $20/mês
Contras: Mais lento, sem CDN, menos otimizado
```

---

## 💡 Recomendação

### Manter Vercel Pro?

```
✅ SIM, se:
- Quer melhor performance
- Precisa de CDN global
- Valoriza facilidade de uso
- Tem orçamento de $20/mês
- Quer analytics avançado

❌ NÃO, se:
- Orçamento muito apertado
- Tráfego muito baixo (<100 visitas/dia)
- Pode configurar alternativas
- Não precisa de CDN global
```

### Nossa Recomendação: **MANTER VERCEL PRO**

**Motivos**:
1. Performance excelente (CDN global)
2. Zero configuração (economiza tempo)
3. Otimizações automáticas
4. Suporte profissional
5. Analytics integrado
6. Custo-benefício bom ($20/mês)

**ROI (Retorno sobre Investimento)**:
```
Custo: $20/mês
Benefício: 
- Site 10x mais rápido
- Melhor experiência do usuário
- Mais conversões
- Menos reclamações
- Tempo economizado em configuração

Valor: POSITIVO ✅
```

---

## 📈 Crescimento Futuro

### Quando Migrar de Plano?

```
Manter Pro ($20/mês) até:
✅ 50+ lojas ativas
✅ 10.000+ visitas/mês
✅ 500 GB bandwidth/mês
✅ 3.000 builds/mês

Migrar para Enterprise quando:
🚀 100+ lojas ativas
🚀 50.000+ visitas/mês
🚀 1 TB+ bandwidth/mês
🚀 Precisar de SLA garantido
```

---

## 🎯 Conclusão

### Resumo do Vercel

```
┌─────────────────────────────────────────────────────┐
│  O QUE É:        Plataforma de hospedagem frontend  │
│  FUNÇÃO:         Servir interface do usuário        │
│  CUSTO:          $20/mês (Plano Pro)                │
│  BENEFÍCIOS:     CDN global, otimizações, SSL       │
│  ALTERNATIVAS:   Netlify, Cloudflare, AWS           │
│  RECOMENDAÇÃO:   Manter (bom custo-benefício)       │
└─────────────────────────────────────────────────────┘
```

### Arquitetura Completa

```
USUÁRIO
   ↓
VERCEL (Frontend - $20/mês)
   ↓ API calls
HEROKU (Backend - $7/mês)
   ↓ queries
SQLITE (Banco de Dados - grátis)

Total: $27/mês + $3 domínio = $30/mês
```

---

**Dúvidas?**
- Dashboard Vercel: https://vercel.com/dashboard
- Documentação: https://vercel.com/docs
- Suporte: support@vercel.com

**Status Atual**:
- ✅ Frontend: https://lwksistemas.com.br (Online)
- ✅ Backend: https://api.lwksistemas.com.br (Online)
- ✅ Plano: Vercel Pro ($20/mês)
- ✅ Uso: ~2% do limite mensal
