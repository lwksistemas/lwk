# 🔄 Refatoração - Profissionais → Funcionários

**Data:** 05/02/2026  
**Commit:** `210f2fd`  
**Status:** ✅ FRONTEND DEPLOYADO | ⏳ BACKEND PENDENTE

## 🎯 Objetivo

Remover duplicação de código mantendo apenas o modelo `Funcionario` (mais completo) ao invés de ter dois modelos separados (`Profissional` e `Funcionario`).

## ❌ Problema Identificado

O sistema tinha DOIS modelos para representar profissionais:

### 1. Modelo Profissional (Antigo - Simples)
```python
class Profissional(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    especialidade = models.CharField(max_length=100)
    comissao_percentual = models.DecimalField()
    is_active = models.BooleanField()
```

### 2. Modelo Funcionario (Novo - Completo)
```python
class Funcionario(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cargo = models.CharField(max_length=100)
    funcao = models.CharField(choices=FUNCAO_CHOICES)  # ✅ Inclui 'profissional'
    especialidade = models.CharField()  # Para profissionais
    comissao_percentual = models.DecimalField()  # Para profissionais
    salario = models.DecimalField()
    data_admissao = models.DateField()
    is_active = models.BooleanField()
```

**Problema:** Funcionários cadastrados como `funcao='profissional'` não apareciam no agendamento porque o sistema buscava da tabela `Profissional`.

## ✅ Solução Aplicada

### Frontend (✅ Deployado)

**Modal de Agendamento:**
```typescript
// ❌ Antes - Buscava de /profissionais/
const [profissionaisRes] = await Promise.all([
  apiClient.get('/cabeleireiro/profissionais/'),
]);
setProfissionais(ensureArray(profissionaisRes.data));

// ✅ Depois - Busca de /funcionarios/ e filtra
const [funcionariosRes] = await Promise.all([
  apiClient.get('/cabeleireiro/funcionarios/'),
]);
const todosFuncionarios = ensureArray(funcionariosRes.data);
const profissionaisAtivos = todosFuncionarios.filter((f: any) => 
  f.funcao === 'profissional' && f.is_active
);
setProfissionais(profissionaisAtivos);
```

### Backend (⏳ Pendente - Requer Migração)

**Mudanças Preparadas:**

1. **models.py:**
   - ❌ Remover modelo `Profissional`
   - ✅ Atualizar `Agendamento.profissional` para apontar para `Funcionario`
   - ✅ Atualizar `BloqueioAgenda.profissional` para apontar para `Funcionario`

2. **serializers.py:**
   - ❌ Remover `ProfissionalSerializer`
   - ✅ Usar `FuncionarioSerializer` filtrado

3. **views.py:**
   - ❌ Remover `ProfissionalViewSet`
   - ✅ Usar `FuncionarioViewSet` com filtro `funcao='profissional'`

4. **urls.py:**
   - ❌ Remover rota `/profissionais/`
   - ✅ Usar `/funcionarios/` com query param `?funcao=profissional`

## 📁 Arquivos Modificados

### Frontend (✅ Deployado):
- `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/cabeleireiro.tsx`
  - ModalAgendamento: Busca funcionários e filtra por `funcao='profissional'`

### Backend (⏳ Preparado, aguardando migração):
- `backend/cabeleireiro/models.py`
  - Modelo Profissional removido
  - ForeignKeys atualizadas para Funcionario
  
- `backend/cabeleireiro/serializers.py`
  - ProfissionalSerializer removido
  
- `backend/cabeleireiro/views.py`
  - ProfissionalViewSet removido

## 🚀 Deploy Status

### Frontend:
```
✅ Build passou
✅ Deploy no Vercel concluído
✅ Em produção: https://lwksistemas.com.br
```

### Backend:
```
⏳ Mudanças preparadas
⏳ Aguardando migração do banco de dados
⏳ Não deployado ainda
```

## 🧪 Como Testar (Frontend)

1. Acessar: https://lwksistemas.com.br/loja/salao-000172/dashboard
2. Login: `andre` / (sua senha)
3. Cadastrar um funcionário:
   - "Ações Rápidas" → "Funcionários"
   - Nome: "Nayara Souza"
   - Função: "Profissional/Cabeleireiro"
   - Especialidade: "Corte"
   - Salvar
4. Criar agendamento:
   - "Ações Rápidas" → "Agendamentos"
   - Verificar se "Nayara Souza" aparece no select de profissionais ✅

## ⚠️ Próximos Passos (Backend)

Para completar a refatoração no backend, é necessário:

### 1. Criar Migração de Dados
```python
# Migrar dados de Profissional para Funcionario
# Atualizar ForeignKeys em Agendamento e BloqueioAgenda
```

### 2. Aplicar Migração
```bash
cd backend
python manage.py makemigrations cabeleireiro
python manage.py migrate cabeleireiro
```

### 3. Remover Endpoint Antigo
```python
# urls.py
# Remover: router.register(r'profissionais', ProfissionalViewSet)
```

### 4. Deploy Backend
```bash
git push heroku master
```

## 📊 Benefícios

### Antes:
```
❌ Dois modelos duplicados (Profissional e Funcionario)
❌ Dados espalhados em duas tabelas
❌ Confusão sobre qual usar
❌ Funcionários não apareciam no agendamento
```

### Depois:
```
✅ Um único modelo (Funcionario)
✅ Dados centralizados
✅ Código mais limpo e manutenível
✅ Funcionários aparecem corretamente no agendamento
✅ Campo 'funcao' define o tipo (profissional, atendente, etc)
```

## 🎓 Boas Práticas Aplicadas

1. **DRY (Don't Repeat Yourself):**
   - Eliminar duplicação de modelos
   - Usar um modelo completo ao invés de vários simples

2. **Single Source of Truth:**
   - Funcionários em um único lugar
   - Função define o tipo de acesso

3. **Backward Compatibility:**
   - Frontend funciona imediatamente
   - Backend pode ser migrado gradualmente

4. **Filtros Inteligentes:**
   - Usar `funcao='profissional'` para filtrar
   - Manter flexibilidade para outros tipos

## ✨ Conclusão

**Frontend:** ✅ Funcionários cadastrados como "Profissional" agora aparecem no agendamento!

**Backend:** ⏳ Código preparado, aguardando migração do banco de dados para remover completamente o modelo antigo.

---

**Status:** ✅ FRONTEND COMPLETO | ⏳ BACKEND PENDENTE  
**Testado:** 🧪 PRONTO PARA TESTE  
**URL:** https://lwksistemas.com.br/loja/salao-000172/dashboard
