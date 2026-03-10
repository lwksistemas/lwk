# 📊 Análise de Refatoração - CRM Vendas

**Data:** 10/03/2026  
**App:** `backend/crm_vendas`  
**Objetivo:** Identificar código duplicado, oportunidades de refatoração e otimizações

---

## 📁 ESTRUTURA ATUAL

```
crm_vendas/
├── models.py (274 linhas)
├── views.py (774 linhas)
├── serializers.py (165 linhas)
├── admin.py (35 linhas)
├── signals.py (58 linhas)
├── tasks.py (12 linhas)
├── utils.py (32 linhas)
├── urls.py
├── google_calendar_service.py
├── views_google_calendar.py
└── management/commands/
    └── notificar_tarefas_crm.py
```

**Total:** ~1.350 linhas de código

---

## 🔍 ANÁLISE DE CÓDIGO DUPLICADO

### 1. ❌ CRÍTICO: Método `_bloquear_vendedor` Duplicado (3x)

**Localização:**
- `VendedorViewSet._bloquear_vendedor()` (views.py:30-37)
- `WhatsAppConfigView._bloquear_vendedor()` (views.py:638-644)
- `LoginConfigView._bloquear_vendedor()` (views.py:710-716)

**Código duplicado:**
```python
def _bloquear_vendedor(self, request):
    if get_current_vendedor_id(request) is not None:
        return Response(
            {'detail': 'Vendedores não têm permissão para acessar configurações.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None
```

**Impacto:** 21 linhas duplicadas (7 linhas × 3 ocorrências)

**Solução:** Criar mixin ou decorator reutilizável

---

### 2. ❌ CRÍTICO: Método `_get_loja` Duplicado (2x)

**Localização:**
- `WhatsAppConfigView._get_loja()` (views.py:646-672)
- `LoginConfigView._get_loja()` (views.py:718-744)

**Código duplicado:**
```python
def _get_loja(self, request=None):
    import logging
    logger = logging.getLogger(__name__)
    loja_id = get_current_loja_id()
    if not loja_id and request:
        try:
            lid = request.headers.get('X-Loja-ID')
            if lid:
                loja_id = int(lid)
        except (ValueError, TypeError):
            pass
        if not loja_id:
            slug = (request.headers.get('X-Tenant-Slug') or '').strip()
            if slug:
                from superadmin.models import Loja
                loja = Loja.objects.using('default').filter(slug__iexact=slug).first()
                if loja:
                    loja_id = loja.id
    if not loja_id:
        logger.warning("...: contexto de loja não encontrado")
        return None
    from superadmin.models import Loja
    try:
        return Loja.objects.using('default').get(id=loja_id)
    except Loja.DoesNotExist:
        return None
```

**Impacto:** 54 linhas duplicadas (27 linhas × 2 ocorrências)

**Solução:** Mover para `utils.py` ou criar mixin

---

### 3. ⚠️ MÉDIO: Invalidação de Cache Duplicada

**Localização:**
- `ContaViewSet._invalidate_contas_cache()` (views.py:234-238)
- `AtividadeViewSet._invalidate_atividades_cache()` (views.py:449-455)
- `signals._invalidate_dashboard_cache()` (signals.py:8-17)
- `signals._invalidate_atividades_cache()` (signals.py:20-27)

**Padrão repetido:**
```python
def _invalidate_xxx_cache(self):
    loja_id = get_current_loja_id()
    if loja_id:
        from django.core.cache import cache
        cache.delete(f'crm_xxx:{loja_id}')
```

**Impacto:** ~30 linhas duplicadas

**Solução:** Criar classe `CRMCacheManager` centralizada

---

### 4. ⚠️ MÉDIO: Filtros de Vendedor Duplicados

**Localização:**
- `ContaViewSet.get_queryset()` (views.py:189-196)
- `LeadViewSet.get_queryset()` (views.py:257-264)
- `ContatoViewSet.get_queryset()` (views.py:280-287)
- `OportunidadeViewSet.get_queryset()` (views.py:313-323)
- `AtividadeViewSet.get_queryset()` (views.py:457-464)

**Padrão repetido:**
```python
def get_queryset(self):
    qs = super().get_queryset()
    vendedor_id = get_current_vendedor_id(self.request)
    if vendedor_id is not None:
        qs = qs.filter(Q(...vendedor_id=vendedor_id)...).distinct()
    return qs
```

**Impacto:** ~50 linhas com lógica similar

**Solução:** Criar mixin `VendedorFilterMixin`

---

### 5. ⚠️ MÉDIO: Lógica de Cache em `list()` Duplicada

**Localização:**
- `ContaViewSet.list()` (views.py:198-210)
- `AtividadeViewSet.list()` (views.py:419-435)

**Padrão repetido:**
```python
def list(self, request, *args, **kwargs):
    from django.core.cache import cache
    loja_id = get_current_loja_id()
    vendedor_id = get_current_vendedor_id(request)
    cache_key = f'crm_xxx:{loja_id}:{vendedor_id or "owner"}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)
    response = super().list(request, *args, **kwargs)
    if cache_key and response.status_code == 200:
        cache.set(cache_key, response.data, 120)
    return response
```

**Impacto:** ~30 linhas duplicadas

**Solução:** Criar decorator `@cache_list_response`

---

### 6. ℹ️ BAIXO: Campos Comuns nos Models

**Observação:** Todos os models têm:
```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
objects = LojaIsolationManager()
```

**Status:** ✅ JÁ OTIMIZADO - Herdam de `LojaIsolationMixin`

---

## 📊 RESUMO DE DUPLICAÇÕES

| Tipo | Ocorrências | Linhas Duplicadas | Prioridade |
|------|-------------|-------------------|------------|
| `_bloquear_vendedor` | 3x | 21 | 🔴 CRÍTICA |
| `_get_loja` | 2x | 54 | 🔴 CRÍTICA |
| Invalidação de cache | 4x | 30 | 🟡 MÉDIA |
| Filtros de vendedor | 5x | 50 | 🟡 MÉDIA |
| Cache em `list()` | 2x | 30 | 🟡 MÉDIA |
| **TOTAL** | **16x** | **185 linhas** | - |

**Redução potencial:** ~185 linhas (-14% do código)

---

## 🎯 PLANO DE REFATORAÇÃO

### Fase 1: Criar Mixins e Utilitários (CRÍTICO)

#### 1.1. Criar `CRMPermissionMixin`

**Arquivo:** `backend/crm_vendas/mixins.py` (NOVO)

```python
"""Mixins reutilizáveis para CRM Vendas."""
from rest_framework import status
from rest_framework.response import Response
from .utils import get_current_vendedor_id


class CRMPermissionMixin:
    """Mixin para bloquear acesso de vendedores a configurações."""
    
    def bloquear_vendedor(self, request, mensagem=None):
        """
        Retorna Response 403 se o usuário for vendedor.
        Retorna None se for proprietário (permitido).
        """
        if get_current_vendedor_id(request) is not None:
            msg = mensagem or 'Vendedores não têm permissão para acessar configurações.'
            return Response(
                {'detail': msg},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None
```

**Uso:**
```python
class VendedorViewSet(CRMPermissionMixin, BaseModelViewSet):
    def list(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request)
        if bloqueio:
            return bloqueio
        # ... resto do código
```

**Redução:** 21 linhas → 3 linhas (18 linhas economizadas)

---

#### 1.2. Mover `_get_loja` para `utils.py`

**Arquivo:** `backend/crm_vendas/utils.py`

```python
def get_loja_from_context(request=None):
    """
    Obtém a loja do contexto atual (loja_id, headers ou slug).
    Retorna None se não encontrar.
    """
    import logging
    from superadmin.models import Loja
    from tenants.middleware import get_current_loja_id
    
    logger = logging.getLogger(__name__)
    loja_id = get_current_loja_id()
    
    # Tentar obter de headers se não tiver no contexto
    if not loja_id and request:
        try:
            lid = request.headers.get('X-Loja-ID')
            if lid:
                loja_id = int(lid)
        except (ValueError, TypeError):
            pass
        
        # Fallback: buscar por slug
        if not loja_id:
            slug = (request.headers.get('X-Tenant-Slug') or '').strip()
            if slug:
                loja = Loja.objects.using('default').filter(slug__iexact=slug).first()
                if loja:
                    loja_id = loja.id
    
    if not loja_id:
        logger.warning("get_loja_from_context: contexto de loja não encontrado")
        return None
    
    try:
        return Loja.objects.using('default').get(id=loja_id)
    except Loja.DoesNotExist:
        return None
```

**Uso:**
```python
from .utils import get_loja_from_context

class WhatsAppConfigView(APIView):
    def get(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=404)
        # ... resto do código
```

**Redução:** 54 linhas → 2 linhas (52 linhas economizadas)

---

### Fase 2: Criar Gerenciador de Cache (MÉDIO)

#### 2.1. Criar `CRMCacheManager`

**Arquivo:** `backend/crm_vendas/cache.py` (NOVO)

```python
"""Gerenciador centralizado de cache do CRM Vendas."""
from django.core.cache import cache
from tenants.middleware import get_current_loja_id


class CRMCacheManager:
    """Gerencia cache do CRM Vendas de forma centralizada."""
    
    # Prefixos de cache
    DASHBOARD = 'crm_dashboard'
    CONTAS = 'crm_contas_list'
    ATIVIDADES = 'crm_atividades'
    ATIVIDADES_VERSION = 'crm_atividades_v'
    
    # TTL padrão
    DEFAULT_TTL = 120  # 2 minutos
    
    @classmethod
    def get_cache_key(cls, prefix, loja_id, vendedor_id=None, **kwargs):
        """Gera chave de cache consistente."""
        key = f'{prefix}:{loja_id}'
        if vendedor_id is not None:
            key += f':{vendedor_id}'
        elif 'owner' in kwargs:
            key += ':owner'
        for k, v in sorted(kwargs.items()):
            if k != 'owner':
                key += f':{v}'
        return key
    
    @classmethod
    def invalidate_dashboard(cls, loja_id):
        """Invalida cache do dashboard para todos os vendedores."""
        if not loja_id:
            return
        
        # Invalidar cache do owner
        cache.delete(cls.get_cache_key(cls.DASHBOARD, loja_id, owner=True))
        
        # Invalidar cache de todos os vendedores
        try:
            from superadmin.models import VendedorUsuario
            for vid in VendedorUsuario.objects.filter(loja_id=loja_id).values_list('vendedor_id', flat=True).distinct():
                cache.delete(cls.get_cache_key(cls.DASHBOARD, loja_id, vid))
        except Exception:
            pass
    
    @classmethod
    def invalidate_contas(cls, loja_id):
        """Invalida cache de contas."""
        if loja_id:
            cache.delete(cls.get_cache_key(cls.CONTAS, loja_id))
    
    @classmethod
    def invalidate_atividades(cls, loja_id):
        """Invalida cache de atividades incrementando versão."""
        if not loja_id:
            return
        try:
            v = cache.get(cls.get_cache_key(cls.ATIVIDADES_VERSION, loja_id), 0) + 1
            cache.set(cls.get_cache_key(cls.ATIVIDADES_VERSION, loja_id), v, 86400)
        except Exception:
            pass
    
    @classmethod
    def get_or_set(cls, key, callback, ttl=None):
        """Get or set pattern para cache."""
        cached = cache.get(key)
        if cached is not None:
            return cached, True  # (data, from_cache)
        
        data = callback()
        cache.set(key, data, ttl or cls.DEFAULT_TTL)
        return data, False
```

**Uso em signals:**
```python
from .cache import CRMCacheManager

@receiver(post_save, sender=Lead)
def _on_lead_change(sender, instance, **kwargs):
    CRMCacheManager.invalidate_dashboard(instance.loja_id)
```

**Uso em views:**
```python
from .cache import CRMCacheManager

class ContaViewSet(BaseModelViewSet):
    def perform_create(self, serializer):
        serializer.save()
        CRMCacheManager.invalidate_contas(get_current_loja_id())
```

**Redução:** 30 linhas → 1 linha (29 linhas economizadas)

---

### Fase 3: Criar Mixins de Filtro (MÉDIO)

#### 3.1. Criar `VendedorFilterMixin`

**Arquivo:** `backend/crm_vendas/mixins.py`

```python
class VendedorFilterMixin:
    """Mixin para filtrar queryset por vendedor."""
    
    # Configurar em cada ViewSet
    vendedor_filter_field = 'vendedor_id'  # Campo direto
    vendedor_filter_related = []  # Campos relacionados (ex: ['oportunidades__vendedor_id'])
    
    def filter_by_vendedor(self, queryset):
        """Filtra queryset pelo vendedor atual (se aplicável)."""
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is None:
            return queryset
        
        # Construir filtro Q
        filters = Q(**{self.vendedor_filter_field: vendedor_id})
        for related_field in self.vendedor_filter_related:
            filters |= Q(**{related_field: vendedor_id})
        
        return queryset.filter(filters).distinct()
    
    def get_queryset(self):
        qs = super().get_queryset()
        return self.filter_by_vendedor(qs)
```

**Uso:**
```python
class LeadViewSet(VendedorFilterMixin, BaseModelViewSet):
    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = ['oportunidades__vendedor_id']
    # get_queryset() é herdado do mixin
```

**Redução:** 50 linhas → 10 linhas (40 linhas economizadas)

---

### Fase 4: Criar Decorator de Cache (MÉDIO)

#### 4.1. Criar `@cache_list_response`

**Arquivo:** `backend/crm_vendas/decorators.py` (NOVO)

```python
"""Decorators reutilizáveis para CRM Vendas."""
from functools import wraps
from rest_framework.response import Response
from .cache import CRMCacheManager
from .utils import get_current_vendedor_id
from tenants.middleware import get_current_loja_id


def cache_list_response(cache_prefix, ttl=120, extra_keys=None):
    """
    Decorator para cachear resposta de list().
    
    Args:
        cache_prefix: Prefixo do cache (ex: 'crm_contas_list')
        ttl: Tempo de vida do cache em segundos
        extra_keys: Lista de query params para incluir na chave
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            loja_id = get_current_loja_id()
            vendedor_id = get_current_vendedor_id(request)
            
            # Construir chave de cache
            cache_kwargs = {}
            if extra_keys:
                for key in extra_keys:
                    value = request.query_params.get(key)
                    if value:
                        cache_kwargs[key] = value
            
            cache_key = CRMCacheManager.get_cache_key(
                cache_prefix,
                loja_id,
                vendedor_id,
                **cache_kwargs
            )
            
            # Tentar obter do cache
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)
            
            # Executar função original
            response = func(self, request, *args, **kwargs)
            
            # Cachear se sucesso
            if response.status_code == 200:
                cache.set(cache_key, response.data, ttl)
            
            return response
        return wrapper
    return decorator
```

**Uso:**
```python
from .decorators import cache_list_response

class ContaViewSet(BaseModelViewSet):
    @cache_list_response('crm_contas_list', ttl=120)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

**Redução:** 30 linhas → 2 linhas (28 linhas economizadas)

---

## 📈 RESULTADOS ESPERADOS

### Redução de Código

```
ANTES:
- views.py: 774 linhas
- utils.py: 32 linhas
- signals.py: 58 linhas
TOTAL: 864 linhas

DEPOIS:
- views.py: 600 linhas (-174 linhas, -22%)
- utils.py: 80 linhas (+48 linhas, funções reutilizáveis)
- signals.py: 30 linhas (-28 linhas, -48%)
- mixins.py: 60 linhas (NOVO)
- cache.py: 80 linhas (NOVO)
- decorators.py: 40 linhas (NOVO)
TOTAL: 890 linhas (+26 linhas, +3%)

REDUÇÃO EFETIVA: 185 linhas de código duplicado eliminadas
CÓDIGO REUTILIZÁVEL: 180 linhas de mixins/utils/decorators
```

### Benefícios

1. **Manutenibilidade:** Correções em 1 lugar (não 3-5)
2. **Consistência:** Comportamento idêntico em todos os ViewSets
3. **Testabilidade:** Testar mixins/utils isoladamente
4. **Escalabilidade:** Fácil adicionar novos ViewSets
5. **Performance:** Cache centralizado e otimizado

---

## 🚀 IMPLEMENTAÇÃO

### Ordem de Execução

1. ✅ **Fase 1:** Criar mixins e utilitários (1-2 horas)
   - Criar `mixins.py` com `CRMPermissionMixin`
   - Mover `_get_loja` para `utils.py`
   - Atualizar views para usar mixins

2. ✅ **Fase 2:** Criar gerenciador de cache (1 hora)
   - Criar `cache.py` com `CRMCacheManager`
   - Atualizar signals para usar manager
   - Atualizar views para usar manager

3. ✅ **Fase 3:** Criar mixins de filtro (1 hora)
   - Adicionar `VendedorFilterMixin` em `mixins.py`
   - Atualizar ViewSets para usar mixin

4. ✅ **Fase 4:** Criar decorators (1 hora)
   - Criar `decorators.py` com `@cache_list_response`
   - Atualizar ViewSets para usar decorator

5. ✅ **Testes:** Validar refatoração (1 hora)
   - Testar todos os endpoints
   - Verificar cache funcionando
   - Validar permissões de vendedor

**Tempo total estimado:** 5-6 horas

---

## 🎓 LIÇÕES APRENDIDAS

### O que está BEM

1. ✅ Models bem estruturados com `LojaIsolationMixin`
2. ✅ Uso de `BaseModelViewSet` para DRY
3. ✅ Cache implementado (pode ser melhorado)
4. ✅ Signals para invalidação de cache
5. ✅ Separação de serializers (list vs detail)

### O que pode MELHORAR

1. ❌ Código duplicado em views (185 linhas)
2. ❌ Lógica de permissão repetida (3x)
3. ❌ Lógica de cache repetida (4x)
4. ❌ Filtros de vendedor repetidos (5x)
5. ⚠️ Falta de testes unitários

---

## 💡 RECOMENDAÇÕES ADICIONAIS

### 1. Adicionar Testes Unitários

```python
# tests/test_mixins.py
class TestCRMPermissionMixin(TestCase):
    def test_bloquear_vendedor_retorna_403(self):
        # ...
    
    def test_proprietario_nao_bloqueado(self):
        # ...
```

### 2. Documentar Mixins

```python
class CRMPermissionMixin:
    """
    Mixin para controle de acesso de vendedores.
    
    Usage:
        class MyViewSet(CRMPermissionMixin, BaseModelViewSet):
            def list(self, request):
                bloqueio = self.bloquear_vendedor(request)
                if bloqueio:
                    return bloqueio
                # ...
    """
```

### 3. Adicionar Type Hints

```python
from typing import Optional
from rest_framework.request import Request
from rest_framework.response import Response

def bloquear_vendedor(self, request: Request, mensagem: Optional[str] = None) -> Optional[Response]:
    """Bloqueia acesso de vendedores."""
    # ...
```

### 4. Criar Constantes

```python
# constants.py
VENDEDOR_PERMISSION_DENIED = 'Vendedores não têm permissão para acessar configurações.'
CACHE_TTL_DEFAULT = 120
CACHE_TTL_DASHBOARD = 120
```

---

## 📞 CONCLUSÃO

O app CRM Vendas está bem estruturado, mas tem **185 linhas de código duplicado** que podem ser eliminadas através de refatoração. A implementação de mixins, utilitários e decorators vai:

- ✅ Reduzir código duplicado em 22%
- ✅ Melhorar manutenibilidade
- ✅ Facilitar testes
- ✅ Padronizar comportamento
- ✅ Facilitar adição de novos recursos

**Prioridade:** 🟡 MÉDIA (não é crítico, mas traz benefícios significativos)

**Recomendação:** Implementar em sprint dedicado de refatoração

---

**Desenvolvido com ❤️ seguindo boas práticas de engenharia de software**
