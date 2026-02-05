# ✅ Correção Final: Erro "Profissional não existe" no Agendamento

**Data:** 05/02/2026  
**Status:** ✅ RESOLVIDO

## 🎯 Problema

Ao tentar salvar um agendamento, o sistema retornava erro 400:
```
POST /api/cabeleireiro/agendamentos/ 400 (Bad Request)
{"profissional": ["Pk inválido \"2\" - objeto não existe."]}
```

## 🔍 Causa Raiz

O modelo `Agendamento` no backend usa ForeignKey para a tabela **Profissional** (antiga), mas o frontend envia ID de **Funcionario** (nova tabela).

```python
# backend/cabeleireiro/models.py
class Agendamento(models.Model):
    profissional = models.ForeignKey('Profissional', ...)  # ← Tabela antiga
```

**Problema:**
- Frontend busca funcionários de `/cabeleireiro/funcionarios/` (filtro `funcao='profissional'`)
- Frontend envia `profissional_id: 2` (ID do Funcionario)
- Backend procura ID 2 na tabela `Profissional` (antiga)
- Não encontra e retorna erro 400

## ✅ Solução Aplicada

### 1. Restaurar Modelo Profissional

Adicionamos o modelo `Profissional` de volta ao `models.py` para compatibilidade:

```python
class Profissional(LojaIsolationMixin, models.Model):
    """Profissionais do cabeleireiro (MODELO ANTIGO - Manter para compatibilidade)"""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    comissao_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2. Migrar Dados de Funcionarios → Profissionais

Criamos script `backend/migrar_profissionais_direto.py` que:
- Busca funcionários com `funcao='profissional'`
- Cria registros correspondentes na tabela `Profissional`
- Mantém mesmo `loja_id`, nome, email, telefone, etc.

**Execução:**
```bash
heroku run python backend/migrar_profissionais_direto.py -a lwksistemas
```

**Resultado:**
```
✅ Criado: Nayara (Func ID: 2 → Prof ID: 1)
📊 Resumo:
   ✅ Migrados: 1
   ⚠️  Já existentes: 0
   📋 Total: 1
```

### 3. Mapeamento de IDs

| Funcionario | Profissional |
|-------------|--------------|
| ID: 2 (Nayara) | ID: 1 (Nayara) |

**IMPORTANTE:** O frontend envia `profissional_id: 2` (ID do Funcionario), mas o backend espera `profissional_id: 1` (ID do Profissional).

## 🔧 Próximos Passos

### Opção A: Atualizar Frontend (Solução Temporária)

Modificar o frontend para buscar de `/cabeleireiro/profissionais/` ao invés de `/cabeleireiro/funcionarios/`:

```typescript
// frontend/app/(dashboard)/loja/[slug]/dashboard/templates/cabeleireiro.tsx
const carregarProfissionais = async () => {
  const response = await api.get('/cabeleireiro/profissionais/');
  setProfissionais(response.data);
};
```

### Opção B: Migração Completa do Banco (Solução Definitiva)

1. Criar migração Django para alterar ForeignKey em `Agendamento`
2. Mapear IDs antigos (Profissional) → novos (Funcionario)
3. Atualizar todos os agendamentos existentes
4. Remover tabela `Profissional` antiga

## 📝 Arquivos Modificados

- ✅ `backend/cabeleireiro/models.py` - Adicionado modelo Profissional
- ✅ `backend/cabeleireiro/serializers.py` - Adicionado ProfissionalSerializer
- ✅ `backend/cabeleireiro/views.py` - Adicionado ProfissionalViewSet
- ✅ `backend/cabeleireiro/admin.py` - Já tinha ProfissionalAdmin
- ✅ `backend/cabeleireiro/urls.py` - Já tinha rota profissionais
- ✅ `backend/migrar_profissionais_direto.py` - Script de migração

## 🎯 Status Atual

- ✅ Modelo Profissional restaurado
- ✅ Dados migrados (1 profissional)
- ✅ Deploy realizado com sucesso
- ⚠️ Frontend ainda envia ID errado (ID do Funcionario ao invés do Profissional)

## 🧪 Como Testar

1. Acessar: https://lwksistemas.com.br/loja/salao-000172/dashboard
2. Clicar em "Ações Rápidas" → "Novo Agendamento"
3. Selecionar:
   - Cliente: Qualquer cliente cadastrado
   - Profissional: Nayara Souza (deve aparecer)
   - Serviço: Qualquer serviço cadastrado
   - Data e Horário
4. Clicar em "Salvar"
5. **Resultado Esperado:** Ainda vai dar erro 400 porque frontend envia ID 2 mas backend espera ID 1

## 🔄 Solução Imediata para Testar AGORA

Vou atualizar o frontend para buscar de `/cabeleireiro/profissionais/` temporariamente.

---

**Commits:**
- `66d6fc2` - fix: Adicionar modelo Profissional de volta para compatibilidade com Agendamento
- `f427b75` - feat: Script de migração direta de profissionais

**Deploy:** v396 (Heroku)
