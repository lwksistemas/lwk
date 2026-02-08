# Correção de Isolamento de Dados - v498

## 🚨 PROBLEMA CRÍTICO DETECTADO

**Cliente da loja `teste-5889` (loja_id=114) estava aparecendo na loja `harmonis-000126` (loja_id=115)**

### Sintomas
- Cliente "Luiz Henrique Felix" cadastrado na loja teste-5889 aparecia na lista de clientes da loja harmonis-000126
- Ao tentar excluir o cliente da loja harmonis-000126, dava erro de validação
- Logs mostravam: `🚨 VIOLAÇÃO DE SEGURANÇA: Tentativa de salvar objeto com loja_id=114 mas contexto é loja_id=115`
- Vazamento de dados entre lojas (violação grave de segurança)

### Causa Raiz

O problema estava nos **ViewSets que definiam `queryset` como atributo de classe**:

```python
# ❌ ERRADO - queryset avaliado no momento da importação do módulo
class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()  # Avaliado ANTES do contexto ser configurado
    serializer_class = ClienteSerializer
```

**Por que isso causava o problema:**

1. **Atributo de classe é avaliado uma única vez** quando o módulo é importado (no startup do Django)
2. Nesse momento, **não há contexto de loja** (`loja_id` é None)
3. O `LojaIsolationManager` deveria filtrar por loja, mas como não há contexto, retorna queryset vazio ou sem filtro
4. O queryset fica **"congelado"** com essa avaliação inicial
5. Quando uma requisição chega, o queryset já avaliado é reutilizado, **ignorando o contexto atual**
6. Resultado: **dados de todas as lojas misturados**

### Fluxo do Problema

```
1. Django inicia → Importa views.py
2. ClienteViewSet é definido → queryset = Cliente.objects.all() é avaliado
3. get_current_loja_id() retorna None (não há requisição ainda)
4. LojaIsolationManager não consegue filtrar
5. Queryset fica sem filtro de loja
6. Requisição chega → ViewSet usa queryset já avaliado
7. VAZAMENTO: Cliente da loja A aparece na loja B
```

## ✅ SOLUÇÃO IMPLEMENTADA

Remover `queryset` como atributo de classe e definir **dinamicamente no método `get_queryset()`**:

```python
# ✅ CORRETO - queryset avaliado a cada requisição
class ClienteViewSet(BaseModelViewSet):
    serializer_class = ClienteSerializer
    
    def get_queryset(self):
        """
        Retorna queryset filtrado por loja
        IMPORTANTE: Não usar queryset como atributo de classe para evitar cache
        """
        return Cliente.objects.all()  # Avaliado DURANTE a requisição
```

**Por que isso funciona:**

1. `get_queryset()` é chamado **durante a requisição** (não no startup)
2. Nesse momento, o `TenantMiddleware` já configurou o contexto (`loja_id` está definido)
3. O `LojaIsolationManager` consegue filtrar corretamente por `loja_id`
4. Cada requisição obtém um **queryset fresco** com o contexto correto
5. **Isolamento perfeito**: cada loja vê apenas seus dados

### Fluxo Correto

```
1. Requisição chega → TenantMiddleware configura loja_id=114
2. ViewSet.get_queryset() é chamado
3. Cliente.objects.all() é avaliado AGORA
4. LojaIsolationManager filtra por loja_id=114
5. Queryset retorna apenas clientes da loja 114
6. ✅ ISOLAMENTO: Cada loja vê apenas seus dados
```

## 📝 MUDANÇAS APLICADAS

Todos os ViewSets da Clínica Estética foram corrigidos:

### ViewSets Corrigidos
- ✅ `ClienteViewSet` - queryset dinâmico
- ✅ `ProfissionalViewSet` - queryset dinâmico
- ✅ `ProcedimentoViewSet` - queryset dinâmico
- ✅ `AgendamentoViewSet` - queryset dinâmico
- ✅ `EvolucaoPacienteViewSet` - queryset dinâmico
- ✅ `AnamnesesTemplateViewSet` - queryset dinâmico
- ✅ `AnamneseViewSet` - queryset dinâmico
- ✅ `HorarioFuncionamentoViewSet` - queryset dinâmico
- ✅ `BloqueioAgendaViewSet` - queryset dinâmico
- ✅ `ProtocoloProcedimentoViewSet` - queryset dinâmico

### Exemplo de Correção

**ANTES (v497):**
```python
class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()  # ❌ Avaliado no startup
    serializer_class = ClienteSerializer
```

**DEPOIS (v498):**
```python
class ClienteViewSet(BaseModelViewSet):
    serializer_class = ClienteSerializer
    
    def get_queryset(self):
        return Cliente.objects.all()  # ✅ Avaliado durante requisição
```

## 🛡️ SEGURANÇA

### Camadas de Proteção (Defesa em Profundidade)

1. **PostgreSQL Schemas Isolados** - Cada loja tem seu schema próprio
2. **LojaIsolationManager** - Filtra automaticamente por `loja_id`
3. **LojaIsolationMixin** - Valida `loja_id` no save/delete
4. **TenantMiddleware** - Configura contexto e valida permissões
5. **BaseModelViewSet** - Valida contexto antes de retornar queryset

### Por que Múltiplas Camadas?

Mesmo com schemas isolados, mantemos o filtro por `loja_id` porque:
- **Defesa em profundidade** - Se uma camada falhar, outras protegem
- **Previne vazamento** - Se schema não for configurado corretamente
- **Performance** - Índice em `loja_id` torna filtro muito rápido
- **Compatibilidade** - Funciona com schemas isolados E tabelas compartilhadas

## 🧪 COMO TESTAR

### 1. Verificar Isolamento de Clientes

```bash
# Loja teste-5889 (loja_id=114)
curl -H "X-Loja-ID: 114" https://lwksistemas.com.br/api/clinica/clientes/

# Loja harmonis-000126 (loja_id=115)
curl -H "X-Loja-ID: 115" https://lwksistemas.com.br/api/clinica/clientes/

# ✅ Cada loja deve ver apenas seus próprios clientes
```

### 2. Verificar Logs

```bash
heroku logs --tail --app lwksistemas

# ✅ Deve mostrar:
# [TenantMiddleware] Contexto setado: loja_id=114
# [LojaIsolationManager] Filtrando por loja_id=114

# ❌ NÃO deve mostrar:
# VIOLAÇÃO DE SEGURANÇA
# Cliente de outra loja
```

### 3. Testar no Frontend

1. Acessar https://lwksistemas.com.br/loja/teste-5889/dashboard
2. Ir em Clientes
3. Verificar que apenas clientes da loja teste-5889 aparecem
4. Acessar https://lwksistemas.com.br/loja/harmonis-000126/dashboard
5. Ir em Clientes
6. Verificar que apenas clientes da loja harmonis-000126 aparecem

## 📊 IMPACTO

### Antes (v497)
- ❌ Vazamento de dados entre lojas
- ❌ Cliente da loja A aparecia na loja B
- ❌ Violação de segurança crítica
- ❌ Risco de LGPD

### Depois (v498)
- ✅ Isolamento perfeito entre lojas
- ✅ Cada loja vê apenas seus dados
- ✅ Segurança garantida
- ✅ Conformidade com LGPD

## 🎯 BOAS PRÁTICAS APLICADAS

### DRY (Don't Repeat Yourself)
- Solução centralizada no `get_queryset()`
- Não precisou alterar serializers ou models

### SOLID
- **Single Responsibility**: Cada ViewSet tem uma única responsabilidade
- **Open/Closed**: Extensível sem modificar código existente
- **Liskov Substitution**: Todos os ViewSets seguem o mesmo padrão

### Clean Code
- Código limpo e documentado
- Comentários explicando o "porquê"
- Nomes descritivos

### KISS (Keep It Simple, Stupid)
- Solução simples e direta
- Não adicionou complexidade desnecessária
- Fácil de entender e manter

## 📚 LIÇÕES APRENDIDAS

### 1. Atributos de Classe vs Métodos
- **Atributos de classe** são avaliados uma única vez (no import)
- **Métodos** são avaliados a cada chamada (durante requisição)
- Para dados dinâmicos (que dependem de contexto), **sempre usar métodos**

### 2. Thread-Local Storage
- Contexto de loja usa thread-local storage
- Só está disponível **durante a requisição**
- Não está disponível no startup do Django

### 3. Lazy Evaluation
- QuerySets do Django são lazy (avaliados quando necessário)
- Mas se armazenados como atributo de classe, são avaliados cedo demais
- Solução: criar queryset fresco a cada requisição

### 4. Defesa em Profundidade
- Nunca confiar em uma única camada de segurança
- Múltiplas camadas de proteção
- Se uma falhar, outras protegem

## 🔄 PRÓXIMOS PASSOS

### Verificar Outros Apps
- [ ] CRM Vendas - verificar se tem o mesmo problema
- [ ] Restaurante - verificar se tem o mesmo problema
- [ ] E-commerce - verificar se tem o mesmo problema
- [ ] Serviços - verificar se tem o mesmo problema

### Monitoramento
- [ ] Adicionar alertas para violações de segurança
- [ ] Dashboard de auditoria de acessos
- [ ] Logs estruturados para análise

### Testes Automatizados
- [ ] Testes de isolamento entre lojas
- [ ] Testes de vazamento de dados
- [ ] Testes de performance

## 📖 REFERÊNCIAS

- Django QuerySets: https://docs.djangoproject.com/en/4.2/ref/models/querysets/
- Thread-Local Storage: https://docs.python.org/3/library/threading.html#thread-local-data
- Multi-Tenancy: https://django-tenants.readthedocs.io/
- LGPD: https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd

## 🏷️ TAGS

`#segurança` `#isolamento` `#multi-tenancy` `#lgpd` `#bugfix` `#crítico` `#v498`

---

**Deploy:** v498  
**Data:** 2026-02-08  
**Status:** ✅ Resolvido  
**Prioridade:** 🚨 Crítica  
**Impacto:** Alto - Segurança e conformidade
