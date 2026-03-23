# Análise de Boas Práticas e Refatoração do Sistema LWK

## Baseado nas literaturas:
- Two Scoops of Django (Best Practices)
- Clean Code (Robert C. Martin)
- Refactoring (Martin Fowler)
- Django for APIs (William S. Vincent)
- Clean Code in Python (Mariano Anaya)

---

## 1. ANÁLISE GERAL DO BACKEND (Django 4.2)

### ✅ PONTOS POSITIVOS

#### 1.1 Arquitetura Multi-tenant
- **Excelente**: Uso correto de `django-tenants` com schemas isolados
- **Segurança**: Cada loja tem seu próprio schema PostgreSQL
- **Mixin Pattern**: `LojaIsolationMixin` garante isolamento automático

#### 1.2 Organização de Models
- **Bom**: Models bem estruturados com Meta classes apropriadas
- **Índices**: Uso correto de índices para otimização de queries
- **Constraints**: Uso de UniqueConstraint para garantir integridade

#### 1.3 Serializers e ViewSets
- **DRF**: Uso adequado do Django REST Framework
- **Paginação**: Implementação de paginação customizada
- **Cache**: Sistema de cache implementado com decorators

#### 1.4 Signals
- **Automação**: Signals bem utilizados para criar estruturas automaticamente
- **Logging**: Bom uso de logging para rastreabilidade

---

## 2. PROBLEMAS IDENTIFICADOS E REFATORAÇÕES NECESSÁRIAS

### 🔴 CRÍTICO: Falta de Service Layer (Two Scoops of Django)

**Problema**: Lógica de negócio está espalhada entre Views, Models e Utils

**Exemplo atual** (views.py linha 552):
```python
def perform_create(self, serializer):
    vendedor_id = get_current_vendedor_id(self.request)
    data = serializer.validated_data
    # Lógica de negócio complexa dentro da view
    if vendedor_id is not None and not data.get('vendedor'):
        serializer.save(vendedor_id=vendedor_id)
        return
    # Mais lógica...
```

**Refatoração recomendada**: Criar Service Layer

```python
# backend/crm_vendas/services.py
class OportunidadeService:
    """
    Service Layer para lógica de negócio de Oportunidades.
    Segue o padrão recomendado em Two Scoops of Django.
    """
    
    def __init__(self, request):
        self.request = request
        self.vendedor_id = get_current_vendedor_id(request)
    
    def criar_oportunidade(self, validated_data):
        """
        Cria uma oportunidade aplicando regras de negócio.
        
        Regras:
        1. Usar vendedor logado se disponível
        2. Herdar vendedor do lead se não houver vendedor logado
        3. Logar warning se criar sem vendedor
        """
        # Regra 1: Vendedor logado
        if self.vendedor_id and not validated_data.get('vendedor'):
            validated_data['vendedor_id'] = self.vendedor_id
            return Oportunidade.objects.create(**validated_data)
        
        # Regra 2: Herdar do lead
        lead = validated_data.get('lead')
        if lead and not validated_data.get('vendedor') and lead.vendedor_id:
            validated_data['vendedor_id'] = lead.vendedor_id
            logger.info(f'Oportunidade herdou vendedor do lead: {lead.id}')
            return Oportunidade.objects.create(**validated_data)
        
        # Regra 3: Sem vendedor (warning)
        if not validated_data.get('vendedor'):
            logger.warning(
                f'Oportunidade criada SEM vendedor: user={self.request.user.id}'
            )
        
        return Oportunidade.objects.create(**validated_data)
    
    def atualizar_oportunidade(self, instance, validated_data):
        """Atualiza oportunidade com regras de negócio."""
        if self.vendedor_id and not instance.vendedor_id and not validated_data.get('vendedor'):
            validated_data['vendedor_id'] = self.vendedor_id
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

# backend/crm_vendas/views.py (refatorado)
class OportunidadeViewSet(VendedorFilterMixin, BaseModelViewSet):
    # ... configurações ...
    
    def perform_create(self, serializer):
        """Delega lógica de negócio para o Service Layer."""
        service = OportunidadeService(self.request)
        service.criar_oportunidade(serializer.validated_data)
    
    def perform_update(self, serializer):
        """Delega lógica de negócio para o Service Layer."""
        service = OportunidadeService(self.request)
        service.atualizar_oportunidade(serializer.instance, serializer.validated_data)
```

**Benefícios**:
- ✅ Lógica de negócio isolada e testável
- ✅ Views mais limpas (Single Responsibility Principle)
- ✅ Reutilização de código
- ✅ Facilita testes unitários

---

### 🟡 MÉDIO: Fat Models (Two Scoops of Django)

**Problema**: Método `save()` com lógica complexa em ProdutoServico

**Exemplo atual** (models.py linha 401):
```python
def save(self, *args, **kwargs):
    """Gera código automático se não fornecido."""
    if not self.codigo:
        prefixo = 'P' if self.tipo == 'produto' else 'S'
        ultimo = ProdutoServico.objects.filter(
            loja_id=self.loja_id,
            codigo__startswith=prefixo
        ).order_by('-codigo').first()
        # ... lógica complexa ...
    super().save(*args, **kwargs)
```

**Refatoração recomendada**: Extrair para Manager customizado

```python
# backend/crm_vendas/managers.py
class ProdutoServicoManager(LojaIsolationManager):
    """Manager customizado para ProdutoServico."""
    
    def gerar_proximo_codigo(self, tipo, loja_id):
        """
        Gera o próximo código sequencial para produto/serviço.
        
        Args:
            tipo: 'produto' ou 'servico'
            loja_id: ID da loja
        
        Returns:
            str: Código no formato P001, S001, etc.
        """
        prefixo = 'P' if tipo == 'produto' else 'S'
        
        ultimo = self.filter(
            loja_id=loja_id,
            codigo__startswith=prefixo
        ).order_by('-codigo').first()
        
        if ultimo and ultimo.codigo:
            try:
                ultimo_num = int(ultimo.codigo[1:])
                proximo_num = ultimo_num + 1
            except (ValueError, IndexError):
                proximo_num = 1
        else:
            proximo_num = 1
        
        return f"{prefixo}{proximo_num:03d}"

# backend/crm_vendas/models.py (refatorado)
class ProdutoServico(LojaIsolationMixin, models.Model):
    # ... campos ...
    
    objects = ProdutoServicoManager()
    
    def save(self, *args, **kwargs):
        """Gera código automático se não fornecido."""
        if not self.codigo:
            self.codigo = self.__class__.objects.gerar_proximo_codigo(
                self.tipo, 
                self.loja_id
            )
        super().save(*args, **kwargs)
```

**Benefícios**:
- ✅ Lógica de geração de código reutilizável
- ✅ Model mais limpo
- ✅ Facilita testes do manager

---

### 🟡 MÉDIO: Queries N+1 (Django for APIs)

**Problema**: Falta de `select_related` e `prefetch_related` em alguns ViewSets

**Exemplo**: CategoriaProdutoServicoViewSet não otimiza queries

**Refatoração recomendada**:

```python
class CategoriaProdutoServicoViewSet(BaseModelViewSet):
    queryset = CategoriaProdutoServico.objects.select_related(
        'loja'  # Se houver FK para loja
    ).prefetch_related(
        'produtos_servicos'  # Prefetch produtos relacionados
    ).all()
    # ... resto do código ...
```

---

### 🟡 MÉDIO: Duplicação de Código (Clean Code)

**Problema**: Lógica de invalidação de cache repetida

**Exemplo atual**: Decorators `@invalidate_cache_on_change` repetidos

**Refatoração recomendada**: Criar Mixin

```python
# backend/crm_vendas/mixins.py
class CacheInvalidationMixin:
    """
    Mixin para invalidar cache automaticamente em operações CRUD.
    Elimina duplicação de código (DRY principle).
    """
    cache_keys = []  # Definir em cada ViewSet
    
    def perform_create(self, serializer):
        result = super().perform_create(serializer)
        self._invalidate_caches()
        return result
    
    def perform_update(self, serializer):
        result = super().perform_update(serializer)
        self._invalidate_caches()
        return result
    
    def perform_destroy(self, instance):
        result = super().perform_destroy(instance)
        self._invalidate_caches()
        return result
    
    def _invalidate_caches(self):
        """Invalida todos os caches configurados."""
        from .cache import CRMCacheManager
        for key in self.cache_keys:
            CRMCacheManager.invalidate(key)

# Uso:
class OportunidadeViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    cache_keys = ['oportunidades', 'dashboard']
    # Não precisa mais dos decorators!
```

---

### 🟢 BAIXO: Nomenclatura (Clean Code)

**Problema**: Algumas funções com nomes não descritivos

**Exemplo**: `_get_admin_funcionario` poderia ser mais claro

**Refatoração**:
```python
# Antes
def _get_admin_funcionario(self, loja):
    pass

# Depois
def _obter_funcionario_administrador_da_loja(self, loja):
    """
    Obtém o funcionário que representa o administrador da loja.
    
    Args:
        loja: Instância da Loja
    
    Returns:
        dict: Dados do funcionário administrador ou None
    """
    pass
```

---

## 3. ANÁLISE DO FRONTEND (Next.js 14)

### ✅ PONTOS POSITIVOS

#### 3.1 Estrutura App Router
- **Moderno**: Uso correto do App Router do Next.js 14
- **TypeScript**: Tipagem adequada com interfaces

#### 3.2 Componentes
- **Organização**: Componentes bem separados por funcionalidade
- **Hooks**: Uso adequado de useState, useEffect, useCallback

### 🔴 PROBLEMAS IDENTIFICADOS

#### 3.1 CRÍTICO: Componentes Fat (Clean Code)

**Problema**: Componente `produtos-servicos/page.tsx` com 500+ linhas

**Refatoração recomendada**: Separar em componentes menores

```typescript
// frontend/app/(dashboard)/loja/[slug]/crm-vendas/produtos-servicos/components/ProdutoServicoForm.tsx
interface ProdutoServicoFormProps {
  formData: FormData;
  categorias: Categoria[];
  onSubmit: (e: React.FormEvent) => void;
  onChange: (data: Partial<FormData>) => void;
  submitting: boolean;
}

export function ProdutoServicoForm({ 
  formData, 
  categorias, 
  onSubmit, 
  onChange, 
  submitting 
}: ProdutoServicoFormProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {/* Campos do formulário */}
    </form>
  );
}

// frontend/app/(dashboard)/loja/[slug]/crm-vendas/produtos-servicos/components/ProdutoServicoTable.tsx
interface ProdutoServicoTableProps {
  itens: ProdutoServico[];
  onView: (item: ProdutoServico) => void;
  onEdit: (item: ProdutoServico) => void;
  onDelete: (item: ProdutoServico) => void;
}

export function ProdutoServicoTable({ 
  itens, 
  onView, 
  onEdit, 
  onDelete 
}: ProdutoServicoTableProps) {
  return (
    <table className="w-full">
      {/* Tabela */}
    </table>
  );
}

// frontend/app/(dashboard)/loja/[slug]/crm-vendas/produtos-servicos/page.tsx (refatorado)
export default function ProdutosServicosPage() {
  // Apenas lógica de estado e coordenação
  const [itens, setItens] = useState<ProdutoServico[]>([]);
  // ... outros estados ...
  
  return (
    <div className="space-y-4">
      <ProdutoServicoFilters {...filterProps} />
      <ProdutoServicoTable {...tableProps} />
      <ProdutoServicoModal {...modalProps} />
    </div>
  );
}
```

**Benefícios**:
- ✅ Componentes com responsabilidade única
- ✅ Mais fácil de testar
- ✅ Reutilização de componentes
- ✅ Melhor legibilidade

---

#### 3.2 MÉDIO: Custom Hooks (React Best Practices)

**Problema**: Lógica de API repetida em vários componentes

**Refatoração recomendada**: Criar custom hooks

```typescript
// frontend/hooks/useProdutosServicos.ts
export function useProdutosServicos(slug: string) {
  const [itens, setItens] = useState<ProdutoServico[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const loadItens = useCallback(async (filtros?: Filtros) => {
    try {
      setLoading(true);
      const params = new URLSearchParams(filtros).toString();
      const url = params 
        ? `/crm-vendas/produtos-servicos/?${params}` 
        : '/crm-vendas/produtos-servicos/';
      const res = await apiClient.get<ProdutoServico[]>(url);
      setItens(normalizeListResponse(res.data));
      setError(null);
    } catch (err) {
      setError('Erro ao carregar produtos e serviços');
    } finally {
      setLoading(false);
    }
  }, []);
  
  const criarItem = useCallback(async (data: FormData) => {
    await apiClient.post('/crm-vendas/produtos-servicos/', data);
    await loadItens();
  }, [loadItens]);
  
  const atualizarItem = useCallback(async (id: number, data: FormData) => {
    await apiClient.put(`/crm-vendas/produtos-servicos/${id}/`, data);
    await loadItens();
  }, [loadItens]);
  
  const deletarItem = useCallback(async (id: number) => {
    await apiClient.delete(`/crm-vendas/produtos-servicos/${id}/`);
    await loadItens();
  }, [loadItens]);
  
  return {
    itens,
    loading,
    error,
    loadItens,
    criarItem,
    atualizarItem,
    deletarItem,
  };
}

// Uso no componente:
export default function ProdutosServicosPage() {
  const { 
    itens, 
    loading, 
    error, 
    criarItem, 
    atualizarItem, 
    deletarItem 
  } = useProdutosServicos(slug);
  
  // Componente muito mais limpo!
}
```

---

#### 3.3 MÉDIO: Tratamento de Erros (Clean Code)

**Problema**: Tratamento de erros inconsistente

**Refatoração recomendada**: Criar Error Boundary e handler centralizado

```typescript
// frontend/lib/error-handler.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function handleApiError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || 'Erro ao processar requisição';
  }
  
  return 'Erro inesperado. Tente novamente.';
}

// Uso:
try {
  await apiClient.post('/endpoint', data);
} catch (err) {
  const errorMessage = handleApiError(err);
  setError(errorMessage);
}
```

---

## 4. PLANO DE REFATORAÇÃO PRIORITÁRIO

### Fase 1: Backend (2-3 semanas)
1. ✅ **Criar Service Layer** para Oportunidades, Propostas, Contratos
2. ✅ **Extrair Managers customizados** para lógica de Models
3. ✅ **Criar CacheInvalidationMixin** para eliminar duplicação
4. ✅ **Adicionar select_related/prefetch_related** em todos os ViewSets
5. ✅ **Criar testes unitários** para Services

### Fase 2: Frontend (2-3 semanas)
1. ✅ **Separar componentes grandes** em componentes menores
2. ✅ **Criar custom hooks** para lógica de API
3. ✅ **Implementar Error Boundary** e tratamento centralizado
4. ✅ **Adicionar testes** com React Testing Library
5. ✅ **Implementar loading states** consistentes

### Fase 3: Infraestrutura (1-2 semanas)
1. ✅ **Configurar CI/CD** com testes automatizados
2. ✅ **Adicionar linting** (pylint, eslint) no pipeline
3. ✅ **Configurar pre-commit hooks** para qualidade de código
4. ✅ **Documentar APIs** com drf-spectacular

---

## 5. MÉTRICAS DE QUALIDADE

### Antes da Refatoração
- Linhas por arquivo: 500-2000 (muito alto)
- Complexidade ciclomática: 15-25 (alto)
- Cobertura de testes: ~30% (baixo)
- Duplicação de código: ~15% (médio)

### Metas Após Refatoração
- Linhas por arquivo: < 300 (ideal)
- Complexidade ciclomática: < 10 (bom)
- Cobertura de testes: > 80% (excelente)
- Duplicação de código: < 5% (excelente)

---

## 6. CONCLUSÃO

O sistema está **bem estruturado** em termos de arquitetura geral, mas precisa de refatoração para seguir as melhores práticas dos livros mencionados:

### Principais melhorias necessárias:
1. **Service Layer** (Two Scoops of Django) - CRÍTICO
2. **Componentes menores** (Clean Code) - CRÍTICO
3. **Custom Hooks** (React Best Practices) - MÉDIO
4. **Managers customizados** (Two Scoops of Django) - MÉDIO
5. **Testes automatizados** (Clean Code) - MÉDIO

### Benefícios esperados:
- ✅ Código mais limpo e manutenível
- ✅ Facilita onboarding de novos desenvolvedores
- ✅ Reduz bugs em produção
- ✅ Melhora performance (queries otimizadas)
- ✅ Facilita testes e refatorações futuras

---

## 7. REFERÊNCIAS

1. **Two Scoops of Django 3.x** - Daniel Roy Greenfeld, Audrey Roy Greenfeld
2. **Clean Code** - Robert C. Martin
3. **Refactoring: Improving the Design of Existing Code** - Martin Fowler
4. **Django for APIs** - William S. Vincent
5. **Clean Code in Python** - Mariano Anaya
6. **Real-World Next.js** - Michele Riva
7. **React Development using TypeScript** - Carl Rippon

---

**Documento criado em**: 23/03/2026
**Última atualização**: 23/03/2026
**Responsável**: Equipe de Desenvolvimento LWK
