# 🚨 ERRO CRÍTICO DE SEGURANÇA - ISOLAMENTO DE DADOS v258

## ⚠️ PROBLEMA GRAVE DETECTADO

**Descrição:** Dashboard da loja "harmonis-000172" está mostrando dados de administrador de **OUTRA LOJA**:
- Nome: Daniela Rodrigues Franco de Oliveira Godoy
- Email: danidanidani.rfoliveira@gmail.com
- Cargo: 👤 Administrador
- Tipo: Clínica de Estética / Enterprise

**Impacto:** CRÍTICO - Violação de isolamento de dados entre lojas

## 🔍 ANÁLISE DO PROBLEMA

### 1. Arquitetura de Isolamento

O sistema usa `LojaIsolationMixin` + `LojaIsolationManager` para isolar dados:

```python
# backend/clinica_estetica/models.py
class Funcionario(LojaIsolationMixin, models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    cargo = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)
    
    objects = LojaIsolationManager()  # ✅ Manager correto
```

### 2. Como Funciona o Isolamento

```python
# backend/core/mixins.py - LojaIsolationManager
def get_queryset(self):
    loja_id = get_current_loja_id()  # Pega do contexto da thread
    
    if loja_id:
        return super().get_queryset().filter(loja_id=loja_id)
    
    # SEGURANÇA: Se não há loja, retorna vazio
    return super().get_queryset().none()
```

### 3. Middleware de Segurança

```python
# backend/tenants/middleware.py
def _get_tenant_slug(self, request):
    # 1. PRIORIDADE: X-Loja-ID header
    loja_id = request.headers.get('X-Loja-ID')
    
    if loja_id:
        loja = Loja.objects.get(id=int(loja_id))
        
        # ✅ VALIDAÇÃO DE SEGURANÇA
        if not request.user.is_superuser:
            if loja.owner_id != request.user.id:
                logger.critical("🚨 VIOLAÇÃO DE SEGURANÇA")
                return None  # Bloqueia acesso
        
        return loja.slug
```

## 🐛 POSSÍVEIS CAUSAS

### Causa 1: sessionStorage com loja_id errado
**Problema:** Frontend pode estar enviando `X-Loja-ID` de outra loja

**Verificar:**
```javascript
// No console do navegador
console.log(sessionStorage.getItem('current_loja_id'));
console.log(sessionStorage.getItem('loja_slug'));
```

**Solução:**
```javascript
// Limpar e recarregar
sessionStorage.clear();
location.reload();
```

### Causa 2: Middleware não está validando corretamente
**Problema:** Validação de segurança pode estar falhando silenciosamente

**Verificar logs do backend:**
```bash
heroku logs --tail --app lwksistemas
# Procurar por: "🚨 VIOLAÇÃO DE SEGURANÇA"
```

### Causa 3: Contexto da thread não está sendo limpo
**Problema:** `_thread_locals.current_loja_id` pode estar "vazando" entre requisições

**Solução:** Adicionar limpeza no middleware:
```python
def __call__(self, request):
    try:
        # ... código existente ...
        response = self.get_response(request)
        return response
    finally:
        # Limpar contexto após requisição
        set_current_loja_id(None)
        set_current_tenant_db('default')
```

### Causa 4: Usuário tem acesso a múltiplas lojas
**Problema:** Se o mesmo email está cadastrado como admin em múltiplas lojas

**Verificar no backend:**
```python
# Django shell
from clinica_estetica.models import Funcionario
Funcionario.objects.all_without_filter().filter(
    email='danidanidani.rfoliveira@gmail.com',
    is_admin=True
).values('id', 'loja_id', 'nome', 'email')
```

## 🔧 SOLUÇÃO IMEDIATA

### 1. Limpar cache do navegador
```
Ctrl + Shift + Delete
Limpar: Cache, Cookies, Dados de sites
```

### 2. Fazer logout e login novamente
```
1. Sair do sistema
2. Limpar sessionStorage
3. Fazer login novamente
```

### 3. Verificar logs do backend
```bash
heroku logs --tail --app lwksistemas | grep "VIOLAÇÃO"
```

## 🛡️ CORREÇÃO PERMANENTE

### Opção 1: Adicionar validação extra no ViewSet

```python
# backend/clinica_estetica/views.py
class FuncionarioViewSet(BaseModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Garantir isolamento por loja"""
        queryset = super().get_queryset()
        
        # Validação extra de segurança
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        
        if not loja_id:
            logger.critical("🚨 Tentativa de acesso sem loja_id no contexto")
            return queryset.none()
        
        # Filtro já é aplicado pelo LojaIsolationManager,
        # mas adicionar log para debug
        logger.info(f"✅ Filtrando funcionários por loja_id={loja_id}")
        return queryset
```

### Opção 2: Adicionar limpeza de contexto no middleware

```python
# backend/tenants/middleware.py
def __call__(self, request):
    try:
        # Código existente...
        response = self.get_response(request)
        return response
    finally:
        # ✅ IMPORTANTE: Limpar contexto após cada requisição
        set_current_loja_id(None)
        set_current_tenant_db('default')
        logger.debug("🧹 Contexto limpo após requisição")
```

### Opção 3: Validar owner no frontend

```typescript
// frontend/lib/api-client.ts
function addLojaAuthHeaders(config: InternalAxiosRequestConfig) {
  const lojaId = sessionStorage.getItem('current_loja_id');
  const userEmail = sessionStorage.getItem('user_email');
  
  if (lojaId) {
    config.headers.set('X-Loja-ID', lojaId);
    config.headers.set('X-User-Email', userEmail); // Para validação extra
  }
  
  return config;
}
```

## 📊 CHECKLIST DE VERIFICAÇÃO

- [ ] Verificar sessionStorage no navegador
- [ ] Limpar cache e cookies
- [ ] Fazer logout/login
- [ ] Verificar logs do backend
- [ ] Confirmar que X-Loja-ID está correto
- [ ] Verificar se usuário tem acesso a múltiplas lojas
- [ ] Adicionar limpeza de contexto no middleware
- [ ] Adicionar logs extras para debug
- [ ] Testar isolamento com múltiplos usuários

## 🔗 ARQUIVOS RELACIONADOS

- `backend/tenants/middleware.py` - Middleware de isolamento
- `backend/core/mixins.py` - LojaIsolationMixin e Manager
- `backend/clinica_estetica/models.py` - Modelo Funcionario
- `backend/clinica_estetica/views.py` - FuncionarioViewSet
- `frontend/lib/api-client.ts` - Headers X-Loja-ID
- `frontend/app/(dashboard)/loja/[slug]/dashboard/page.tsx` - Definição de current_loja_id

---

**Status:** 🚨 CRÍTICO - REQUER AÇÃO IMEDIATA  
**Data:** 2026-02-02  
**Versão:** v258  
**Prioridade:** P0 - SEGURANÇA
