# 🔒 ANÁLISE DE SEGURANÇA - ISOLAMENTO ENTRE LOJAS v258

## 🎯 OBJETIVO

Analisar e corrigir possíveis falhas de segurança no isolamento de dados entre lojas para prevenir vazamento de informações.

## 🔍 ARQUITETURA DE ISOLAMENTO

### 1. Camadas de Proteção

```
┌─────────────────────────────────────────────────────┐
│ CAMADA 1: Middleware (TenantMiddleware)            │
│ - Detecta loja pela URL/Header                     │
│ - Define loja_id no contexto da thread             │
│ - Valida que usuário pertence à loja               │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ CAMADA 2: LojaIsolationManager                     │
│ - Filtra automaticamente por loja_id               │
│ - Retorna queryset vazio se não há contexto        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ CAMADA 3: LojaIsolationMixin                       │
│ - Valida loja_id ao salvar                         │
│ - Impede salvar em outra loja                      │
│ - Impede deletar dados de outra loja               │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ CAMADA 4: ViewSets                                  │
│ - Usa queryset com LojaIsolationManager            │
│ - Validação extra de segurança                     │
└─────────────────────────────────────────────────────┘
```

## 🚨 VULNERABILIDADES IDENTIFICADAS

### ❌ VULNERABILIDADE 1: Contexto não é limpo entre requisições

**Problema:**
```python
# backend/tenants/middleware.py (ANTES)
def __call__(self, request):
    # Define contexto
    set_current_loja_id(loja_id)
    
    response = self.get_response(request)
    return response
    # ❌ Contexto NÃO é limpo!
```

**Risco:** Thread pode reutilizar loja_id de requisição anterior

**Impacto:** CRÍTICO - Vazamento de dados entre lojas

**Status:** ✅ CORRIGIDO

**Correção:**
```python
def __call__(self, request):
    try:
        set_current_loja_id(loja_id)
        response = self.get_response(request)
        return response
    finally:
        # ✅ Limpar contexto após cada requisição
        set_current_loja_id(None)
        set_current_tenant_db('default')
```

### ❌ VULNERABILIDADE 2: BaseModelViewSet não valida loja_id

**Problema:**
```python
# backend/core/views.py (ANTES)
class BaseModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = self.queryset
        if hasattr(self.queryset.model, 'is_active'):
            queryset = queryset.filter(is_active=True)
        return queryset
        # ❌ Não valida loja_id!
```

**Risco:** Se LojaIsolationManager falhar, dados de todas as lojas são retornados

**Impacto:** CRÍTICO - Vazamento de dados

**Status:** ⚠️ PARCIALMENTE CORRIGIDO (apenas FuncionarioViewSet)

**Correção necessária:**
```python
class BaseModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = self.queryset
        
        # ✅ Validação de segurança
        if hasattr(self.queryset.model, 'loja_id'):
            from tenants.middleware import get_current_loja_id
            loja_id = get_current_loja_id()
            
            if not loja_id:
                logger.critical("🚨 Tentativa de acesso sem loja_id")
                return queryset.none()
        
        if hasattr(self.queryset.model, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset
```

### ❌ VULNERABILIDADE 3: Validação de owner não cobre todos os casos

**Problema:**
```python
# backend/tenants/middleware.py
def _get_tenant_slug(self, request):
    # 1. X-Loja-ID: ✅ Valida owner
    # 2. X-Tenant-Slug: ✅ Valida owner
    # 3. Query param: ❌ NÃO valida owner
    # 4. URL path: ❌ NÃO valida owner
    # 5. Subdomain: ❌ NÃO valida owner
```

**Risco:** Usuário pode acessar outra loja via URL direta

**Impacto:** ALTO - Acesso não autorizado

**Status:** ⚠️ REQUER CORREÇÃO

### ❌ VULNERABILIDADE 4: Modelos sem LojaIsolationManager

**Problema:** Alguns modelos podem não estar usando o manager correto

**Risco:** Queries retornam dados de todas as lojas

**Impacto:** CRÍTICO - Vazamento de dados

**Status:** ⚠️ REQUER VERIFICAÇÃO

## 🔧 CORREÇÕES NECESSÁRIAS

### CORREÇÃO 1: Validar owner em TODOS os métodos de detecção

```python
def _get_tenant_slug(self, request):
    # ... código existente ...
    
    # 3. Query param - ADICIONAR VALIDAÇÃO
    tenant_slug = request.GET.get('tenant')
    if tenant_slug:
        if not self._validate_user_owns_loja(request, tenant_slug):
            return None
        return tenant_slug
    
    # 4. URL path - ADICIONAR VALIDAÇÃO
    path_parts = request.path.split('/')
    if len(path_parts) >= 3 and path_parts[1] == 'loja':
        tenant_slug = path_parts[2]
        if not self._validate_user_owns_loja(request, tenant_slug):
            return None
        return tenant_slug
    
    # 5. Subdomain - ADICIONAR VALIDAÇÃO
    host = request.get_host().split(':')[0]
    parts = host.split('.')
    if len(parts) > 2:
        tenant_slug = parts[0]
        if not self._validate_user_owns_loja(request, tenant_slug):
            return None
        return tenant_slug
    
    return None

def _validate_user_owns_loja(self, request, tenant_slug):
    """Valida que usuário autenticado é owner da loja"""
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return False
    
    if request.user.is_superuser:
        return True  # SuperAdmin pode acessar qualquer loja
    
    try:
        from superadmin.models import Loja
        loja = Loja.objects.filter(slug__iexact=tenant_slug).first()
        
        if not loja:
            return False
        
        if loja.owner_id != request.user.id:
            logger.critical(
                f"🚨 VIOLAÇÃO: Usuário {request.user.id} tentou "
                f"acessar loja {tenant_slug} (owner: {loja.owner_id})"
            )
            return False
        
        return True
    except Exception as e:
        logger.error(f"Erro ao validar owner: {e}")
        return False
```

### CORREÇÃO 2: Adicionar validação no BaseModelViewSet

```python
class BaseModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = self.queryset
        
        # 🛡️ SEGURANÇA: Validar loja_id para modelos com isolamento
        if hasattr(self.queryset.model, 'loja_id'):
            from tenants.middleware import get_current_loja_id
            import logging
            logger = logging.getLogger(__name__)
            
            loja_id = get_current_loja_id()
            
            if not loja_id:
                logger.critical(
                    f"🚨 [{self.__class__.__name__}] "
                    f"Tentativa de acesso sem loja_id no contexto"
                )
                return queryset.none()
            
            logger.debug(
                f"✅ [{self.__class__.__name__}] "
                f"Filtrando por loja_id={loja_id}"
            )
        
        # Filtro is_active
        if hasattr(self.queryset.model, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset
```

### CORREÇÃO 3: Verificar todos os modelos

```python
# Script para verificar modelos sem LojaIsolationManager
# backend/scripts/verificar_isolamento.py

from django.apps import apps
from core.mixins import LojaIsolationMixin, LojaIsolationManager

def verificar_modelos():
    """Verifica se todos os modelos com loja_id usam LojaIsolationManager"""
    problemas = []
    
    for model in apps.get_models():
        # Verificar se tem loja_id
        if hasattr(model, 'loja_id'):
            # Verificar se usa LojaIsolationMixin
            if not issubclass(model, LojaIsolationMixin):
                problemas.append(f"❌ {model.__name__}: Tem loja_id mas não usa LojaIsolationMixin")
            
            # Verificar se usa LojaIsolationManager
            if not isinstance(model.objects, LojaIsolationManager):
                problemas.append(f"❌ {model.__name__}: Tem loja_id mas não usa LojaIsolationManager")
    
    if problemas:
        print("🚨 PROBLEMAS DE ISOLAMENTO ENCONTRADOS:")
        for p in problemas:
            print(p)
    else:
        print("✅ Todos os modelos estão corretamente isolados")
    
    return problemas

if __name__ == '__main__':
    verificar_modelos()
```

### CORREÇÃO 4: Adicionar testes de segurança

```python
# backend/tests/test_isolamento_seguranca.py

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from superadmin.models import Loja
from clinica_estetica.models import Funcionario
from tenants.middleware import TenantMiddleware, set_current_loja_id

User = get_user_model()

class IsolamentoSegurancaTestCase(TestCase):
    def setUp(self):
        # Criar dois usuários e duas lojas
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass')
        
        self.loja1 = Loja.objects.create(
            nome='Loja 1',
            slug='loja1',
            owner=self.user1
        )
        self.loja2 = Loja.objects.create(
            nome='Loja 2',
            slug='loja2',
            owner=self.user2
        )
        
        # Criar funcionários em cada loja
        set_current_loja_id(self.loja1.id)
        self.func1 = Funcionario.objects.create(
            nome='Func 1',
            email='func1@test.com',
            telefone='111',
            cargo='Teste',
            loja_id=self.loja1.id
        )
        
        set_current_loja_id(self.loja2.id)
        self.func2 = Funcionario.objects.create(
            nome='Func 2',
            email='func2@test.com',
            telefone='222',
            cargo='Teste',
            loja_id=self.loja2.id
        )
        
        set_current_loja_id(None)
    
    def test_isolamento_por_loja_id(self):
        """Testa que cada loja só vê seus próprios dados"""
        # Contexto da loja 1
        set_current_loja_id(self.loja1.id)
        funcs = Funcionario.objects.all()
        self.assertEqual(funcs.count(), 1)
        self.assertEqual(funcs.first().id, self.func1.id)
        
        # Contexto da loja 2
        set_current_loja_id(self.loja2.id)
        funcs = Funcionario.objects.all()
        self.assertEqual(funcs.count(), 1)
        self.assertEqual(funcs.first().id, self.func2.id)
        
        # Sem contexto
        set_current_loja_id(None)
        funcs = Funcionario.objects.all()
        self.assertEqual(funcs.count(), 0)  # Deve retornar vazio
    
    def test_nao_pode_salvar_em_outra_loja(self):
        """Testa que não pode salvar dados em outra loja"""
        set_current_loja_id(self.loja1.id)
        
        # Tentar criar funcionário com loja_id diferente
        with self.assertRaises(ValidationError):
            Funcionario.objects.create(
                nome='Hacker',
                email='hacker@test.com',
                telefone='999',
                cargo='Teste',
                loja_id=self.loja2.id  # ❌ Tentando salvar em outra loja
            )
    
    def test_middleware_valida_owner(self):
        """Testa que middleware valida owner da loja"""
        factory = RequestFactory()
        middleware = TenantMiddleware(lambda r: None)
        
        # Usuário 1 tentando acessar loja 2
        request = factory.get('/loja/loja2/dashboard')
        request.user = self.user1
        
        tenant_slug = middleware._get_tenant_slug(request)
        self.assertIsNone(tenant_slug)  # Deve bloquear
```

## 📊 CHECKLIST DE SEGURANÇA

### Middleware
- [x] Limpa contexto após cada requisição
- [ ] Valida owner em TODOS os métodos de detecção
- [ ] Logs de tentativas de violação
- [ ] Rate limiting para tentativas suspeitas

### Models
- [x] Usa LojaIsolationMixin
- [x] Usa LojaIsolationManager
- [ ] Verificar TODOS os modelos
- [ ] Testes automatizados

### ViewSets
- [ ] BaseModelViewSet valida loja_id
- [x] FuncionarioViewSet valida loja_id
- [ ] Todos os ViewSets validam loja_id
- [ ] Logs de acesso

### Frontend
- [x] Envia X-Loja-ID correto
- [x] Limpa sessionStorage ao logout
- [ ] Valida resposta da API
- [ ] Detecta tentativas de acesso não autorizado

## 🚀 PLANO DE AÇÃO

### PRIORIDADE P0 (CRÍTICO)
1. ✅ Limpar contexto no middleware (FEITO)
2. ⏳ Validar owner em todos os métodos
3. ⏳ Adicionar validação no BaseModelViewSet
4. ⏳ Verificar todos os modelos

### PRIORIDADE P1 (ALTO)
5. ⏳ Criar script de verificação
6. ⏳ Adicionar testes automatizados
7. ⏳ Implementar logs de segurança
8. ⏳ Documentar procedimentos

### PRIORIDADE P2 (MÉDIO)
9. ⏳ Rate limiting
10. ⏳ Alertas de segurança
11. ⏳ Auditoria de acessos
12. ⏳ Monitoramento contínuo

---

**Status:** 🚧 EM ANDAMENTO  
**Data:** 2026-02-02  
**Versão:** v258  
**Prioridade:** P0 - CRÍTICO
