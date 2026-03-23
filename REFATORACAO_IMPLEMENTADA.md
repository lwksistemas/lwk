# Refatoração Implementada - Fase 1 (Backend)

## Data: 23/03/2026

---

## ✅ O QUE FOI IMPLEMENTADO

### 1. Service Layer (Two Scoops of Django) - CRÍTICO

Criado arquivo `backend/crm_vendas/services.py` com 4 services:

#### OportunidadeService
- `criar_oportunidade()`: Aplica regras de negócio para criação
- `atualizar_oportunidade()`: Aplica regras de negócio para atualização
- Regras implementadas:
  1. Usar vendedor logado (prioridade)
  2. Herdar vendedor do lead
  3. Criar sem vendedor (com warning)

#### PropostaService
- `gerar_proposta_de_template()`: Gera proposta a partir de template
- `enviar_para_cliente()`: Envia proposta com validações

#### ContratoService
- `gerar_contrato_de_proposta()`: Gera contrato de proposta aprovada
- `enviar_para_assinatura()`: Envia contrato para assinatura digital

#### ProdutoServicoService
- `calcular_valor_total_itens()`: Calcula valor total de itens
- `validar_disponibilidade()`: Valida disponibilidade de produto/serviço

**Benefícios**:
- ✅ Lógica de negócio isolada e testável
- ✅ Views mais limpas (Single Responsibility Principle)
- ✅ Reutilização de código
- ✅ Facilita testes unitários

---

### 2. Custom Managers (Two Scoops of Django) - MÉDIO

Criado arquivo `backend/crm_vendas/managers.py` com 5 managers:

#### ProdutoServicoManager
- `gerar_proximo_codigo()`: Gera códigos sequenciais (P001, S001)
- `ativos()`: Filtra produtos/serviços ativos
- `por_tipo()`: Filtra por tipo (produto/serviço)
- `por_categoria()`: Filtra por categoria
- `com_categoria()`: Query otimizada com select_related

#### OportunidadeManager
- `com_relacionamentos()`: Query otimizada (evita N+1)
- `por_etapa()`: Filtra por etapa do funil
- `abertas()`, `ganhas()`, `perdidas()`: Filtros de status
- `por_vendedor()`: Filtra por vendedor

#### PropostaManager
- `com_relacionamentos()`: Query otimizada
- `por_status()`: Filtra por status
- `rascunhos()`, `enviadas()`, `aprovadas()`, `rejeitadas()`: Filtros

#### ContratoManager
- `com_relacionamentos()`: Query otimizada
- `por_status()`: Filtra por status
- `aguardando_assinatura()`, `assinados()`, `ativos()`: Filtros

#### LeadManager
- `com_relacionamentos()`: Query otimizada
- `por_status()`: Filtra por status
- `novos()`, `qualificados()`, `convertidos()`: Filtros
- `por_origem()`: Filtra por origem

**Benefícios**:
- ✅ Queries complexas encapsuladas
- ✅ Models mais limpos (Thin Models)
- ✅ Reutilização de queries
- ✅ Melhor performance com select_related/prefetch_related

---

### 3. Refatoração de Models

**Alterações**:
- Importado managers customizados
- Substituído `objects = LojaIsolationManager()` por managers específicos:
  - `Lead.objects = LeadManager()`
  - `Oportunidade.objects = OportunidadeManager()`
  - `ProdutoServico.objects = ProdutoServicoManager()`
  - `Proposta.objects = PropostaManager()`
  - `Contrato.objects = ContratoManager()`

- Refatorado `ProdutoServico.save()`:
  ```python
  # Antes: 25 linhas de lógica complexa
  # Depois: 5 linhas delegando para o Manager
  def save(self, *args, **kwargs):
      if not self.codigo:
          self.codigo = self.__class__.objects.gerar_proximo_codigo(
              self.tipo,
              self.loja_id
          )
      super().save(*args, **kwargs)
  ```

**Benefícios**:
- ✅ Models mais limpos e focados
- ✅ Lógica de geração de código reutilizável
- ✅ Facilita testes do manager

---

### 4. Refatoração de Views

**Alterações em OportunidadeViewSet**:

```python
# Antes: 35 linhas de lógica de negócio
@invalidate_cache_on_change('oportunidades', 'dashboard')
def perform_create(self, serializer):
    vendedor_id = get_current_vendedor_id(self.request)
    data = serializer.validated_data
    # ... 30+ linhas de lógica ...
    serializer.save()

# Depois: 5 linhas delegando para Service Layer
@invalidate_cache_on_change('oportunidades', 'dashboard')
def perform_create(self, serializer):
    """Cria oportunidade usando Service Layer."""
    service = OportunidadeService(self.request)
    service.criar_oportunidade(serializer.validated_data)
```

**Benefícios**:
- ✅ Views 85% mais limpas
- ✅ Lógica de negócio testável independentemente
- ✅ Facilita manutenção e debugging

---

## 📊 MÉTRICAS DE MELHORIA

### Antes da Refatoração
- `OportunidadeViewSet.perform_create`: 35 linhas
- `ProdutoServico.save()`: 25 linhas
- Lógica de negócio: Espalhada em Views e Models
- Testabilidade: Difícil (precisa mockar request, serializer, etc)

### Depois da Refatoração
- `OportunidadeViewSet.perform_create`: 5 linhas (-86%)
- `ProdutoServico.save()`: 5 linhas (-80%)
- Lógica de negócio: Centralizada em Services
- Testabilidade: Fácil (testes unitários diretos nos Services)

---

## 🎯 PRÓXIMOS PASSOS

### Fase 2: Testes Unitários (1 semana)
- [ ] Criar testes para OportunidadeService
- [ ] Criar testes para PropostaService
- [ ] Criar testes para ContratoService
- [ ] Criar testes para Managers customizados
- [ ] Meta: >80% de cobertura

### Fase 3: Frontend (2 semanas)
- [ ] Separar componente `produtos-servicos/page.tsx` (500+ linhas)
- [ ] Criar custom hooks para lógica de API
- [ ] Implementar Error Boundary
- [ ] Criar componentes reutilizáveis

### Fase 4: Otimizações (1 semana)
- [ ] Adicionar select_related/prefetch_related em todos os ViewSets
- [ ] Criar índices adicionais no banco
- [ ] Implementar cache em queries pesadas
- [ ] Otimizar serializers

---

## 📚 REFERÊNCIAS APLICADAS

1. **Two Scoops of Django 3.x**
   - ✅ Service Layer implementado
   - ✅ Custom Managers implementados
   - ✅ Thin Models aplicado

2. **Clean Code (Robert C. Martin)**
   - ✅ Single Responsibility Principle
   - ✅ Funções pequenas e focadas
   - ✅ Nomes descritivos

3. **Refactoring (Martin Fowler)**
   - ✅ Extract Method aplicado
   - ✅ Move Method aplicado
   - ✅ Código duplicado eliminado

---

## 🔧 COMO USAR OS NOVOS SERVICES

### Exemplo 1: Criar Oportunidade
```python
from crm_vendas.services import OportunidadeService

# Na view
service = OportunidadeService(request)
oportunidade = service.criar_oportunidade(validated_data)
```

### Exemplo 2: Gerar Proposta de Template
```python
from crm_vendas.services import PropostaService

service = PropostaService(request)
proposta = service.gerar_proposta_de_template(
    oportunidade=oportunidade,
    template_id=1,
    customizacoes={'titulo': 'Proposta Customizada'}
)
```

### Exemplo 3: Usar Manager Customizado
```python
from crm_vendas.models import Oportunidade

# Query otimizada com relacionamentos
oportunidades = Oportunidade.objects.com_relacionamentos().abertas()

# Filtrar por vendedor
minhas_oportunidades = Oportunidade.objects.por_vendedor(vendedor_id)

# Gerar código de produto
codigo = ProdutoServico.objects.gerar_proximo_codigo('produto', loja_id)
```

---

## ✅ CONCLUSÃO

A Fase 1 da refatoração foi concluída com sucesso! O código agora segue as melhores práticas recomendadas pelos livros:

- **Two Scoops of Django**: Service Layer e Custom Managers
- **Clean Code**: Single Responsibility e funções pequenas
- **Refactoring**: Eliminação de código duplicado

O sistema está mais:
- ✅ Manutenível
- ✅ Testável
- ✅ Escalável
- ✅ Legível

**Próximo passo**: Implementar testes unitários para garantir que as refatorações não quebraram funcionalidades existentes.

---

**Commit**: `4d2162cd` - refactor: implementar Service Layer e Custom Managers
**Data**: 23/03/2026
**Responsável**: Equipe de Desenvolvimento LWK
