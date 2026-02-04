# 🏗️ Arquitetura Limpa - Criação de Funcionários

## Visão Geral
Sistema consolidado e sem duplicações para criação automática de funcionários quando uma loja é criada.

## Componentes Principais

### 1. Modelo Base (ÚNICO)
**Arquivo**: `backend/core/models.py`

```python
class BaseFuncionario(BaseModel):
    """
    Modelo base abstrato para funcionários
    Usado em: clinica_estetica, servicos, restaurante, crm_vendas
    """
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    cargo = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)  # ✅ Identifica o admin da loja
```

**Características**:
- ✅ Modelo abstrato (não cria tabela própria)
- ✅ Reutilizado por todos os tipos de loja
- ✅ Campo `is_admin` para identificar o administrador
- ✅ Sem campo `user` (removido para evitar conflitos UNIQUE)

### 2. Signal de Criação Automática (ÚNICO)
**Arquivo**: `backend/superadmin/signals.py`

```python
@receiver(post_save, sender='superadmin.Loja')
def create_funcionario_for_loja_owner(sender, instance, created, **kwargs):
    """
    Cria automaticamente um funcionário para o administrador quando uma loja é criada.
    
    Executado APENAS na criação de novas lojas (created=True).
    """
```

**Características**:
- ✅ Executado automaticamente quando uma loja é criada
- ✅ Cria funcionário para o owner da loja
- ✅ Marca como `is_admin=True`
- ✅ Adiciona `loja_id` para isolamento de dados
- ✅ Verifica se já existe antes de criar (evita duplicações)
- ✅ Trata cada tipo de loja (Clínica, CRM, Restaurante, Serviços)

**Tipos de Loja Suportados**:
1. **Clínica de Estética** → `clinica_estetica.models.Funcionario`
2. **Serviços** → `servicos.models.Funcionario`
3. **Restaurante** → `restaurante.models.Funcionario`
4. **CRM Vendas** → `crm_vendas.models.Vendedor`
5. **E-commerce** → Não tem funcionários

### 3. Comando de Correção (APENAS PARA DADOS ANTIGOS)
**Arquivo**: `backend/superadmin/management/commands/criar_funcionarios_admins.py`

**⚠️ IMPORTANTE**: Este comando é apenas para correção de dados antigos!

**Quando usar**:
- Lojas criadas antes do signal ser implementado
- Erro na criação automática que precisa ser corrigido

**Quando NÃO usar**:
- Lojas novas (já têm funcionário criado automaticamente)
- Operação normal do sistema

```bash
# Uso (apenas se necessário)
python manage.py criar_funcionarios_admins
```

## Fluxo de Criação

### Loja Nova (Automático)
```
1. Superadmin cria nova loja
   ↓
2. Signal post_save é disparado
   ↓
3. Verifica se já existe funcionário
   ↓
4. Cria funcionário com is_admin=True
   ↓
5. Funcionário aparece no dashboard
```

### Loja Antiga (Manual - Apenas se necessário)
```
1. Identificar lojas sem funcionário
   ↓
2. Executar comando: criar_funcionarios_admins
   ↓
3. Comando cria funcionários faltantes
   ↓
4. Funcionários aparecem nos dashboards
```

## Isolamento de Dados

### LojaIsolationMixin
Todos os funcionários herdam de `LojaIsolationMixin` que garante:

```python
class Funcionario(LojaIsolationMixin, BaseFuncionario):
    loja_id = models.IntegerField(db_index=True)  # ✅ Obrigatório
    objects = LojaIsolationManager()  # ✅ Filtra automaticamente
```

**Benefícios**:
- ✅ Cada loja só vê seus próprios funcionários
- ✅ Impossível acessar funcionários de outra loja
- ✅ Segurança automática no nível do banco de dados

## Identificação do Administrador

### Campo is_admin
```python
is_admin = models.BooleanField(default=False)
```

**Características**:
- ✅ `True` para o owner da loja
- ✅ `False` para funcionários adicionados manualmente
- ✅ Administrador não pode ser excluído
- ✅ Badge especial no frontend: "👤 Administrador"

## Frontend

### Modal de Funcionários
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/clinica-estetica.tsx`

**Características**:
- ✅ Lista todos os funcionários da loja
- ✅ Badge especial para administrador
- ✅ Botão "Excluir" desabilitado para admin
- ✅ CRUD completo (Criar, Listar, Editar, Excluir)

### API Client
**Arquivo**: `frontend/lib/api-client.ts`

```typescript
// Interceptor adiciona X-Loja-ID automaticamente
clinicaApiClient.interceptors.request.use((config) => {
  const lojaId = localStorage.getItem('current_loja_id');
  if (lojaId) {
    config.headers['X-Loja-ID'] = lojaId;  // ✅ ID único da loja
  }
  return config;
});
```

**Benefícios**:
- ✅ Usa ID único da loja (não slug)
- ✅ Evita conflitos se duas lojas tiverem mesmo nome
- ✅ Mais seguro e confiável

## Checklist de Limpeza

### ✅ Código Consolidado
- [x] Modelo base único em `core/models.py`
- [x] Signal único em `superadmin/signals.py`
- [x] Comando de correção documentado
- [x] Sem duplicações de lógica

### ✅ Documentação
- [x] Comentários claros no código
- [x] Docstrings em todas as funções
- [x] Arquivo de arquitetura (este documento)

### ✅ Segurança
- [x] Isolamento de dados por loja
- [x] Validação de loja_id obrigatório
- [x] Administrador não pode ser excluído

### ✅ Frontend
- [x] Header X-Loja-ID com ID único
- [x] Badge de administrador
- [x] Proteção contra exclusão do admin

## Manutenção Futura

### Adicionar Novo Tipo de Loja
1. Criar modelo herdando de `BaseFuncionario`
2. Adicionar caso no signal `create_funcionario_for_loja_owner`
3. Adicionar caso no comando `criar_funcionarios_admins` (se necessário)
4. Criar dashboard com modal de funcionários

### Modificar Campos de Funcionário
1. Atualizar `BaseFuncionario` em `core/models.py`
2. Criar migração
3. Atualizar serializers
4. Atualizar frontend

## Arquivos Importantes

### Backend
- `backend/core/models.py` - Modelo base
- `backend/superadmin/signals.py` - Criação automática
- `backend/superadmin/management/commands/criar_funcionarios_admins.py` - Correção
- `backend/clinica_estetica/models.py` - Modelo específico
- `backend/crm_vendas/models.py` - Modelo específico
- `backend/servicos/models.py` - Modelo específico
- `backend/restaurante/models.py` - Modelo específico

### Frontend
- `frontend/lib/api-client.ts` - Interceptor com X-Loja-ID
- `frontend/app/(dashboard)/loja/[slug]/dashboard/page.tsx` - Salva loja_id
- `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/clinica-estetica.tsx` - Modal

## Conclusão

Sistema limpo, consolidado e sem duplicações. Toda a lógica de criação de funcionários está centralizada no signal, facilitando manutenção e evitando bugs.
