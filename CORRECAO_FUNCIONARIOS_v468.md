# Correção - Sistema de Funcionários - v468

## 🐛 Problemas Identificados

1. **Admin não aparecia** na lista de funcionários da Clínica Harmonis
2. **Formulário incorreto** - tinha opção "Profissional/Esteticista" (redundante)
3. **Campo "Especialidade"** no formulário de funcionários (redundante - só profissionais têm)

## ✅ Correções Implementadas

### 1. Admin Criado Manualmente
Como a loja já existia antes do signal ser implementado, o admin não foi criado automaticamente.

**Solução**: Script Python para criar admin manualmente
```python
# backend/criar_admin_clinica.py
admin = Funcionario.objects.create(
    nome=loja.owner.get_full_name() or loja.owner.username,
    email=loja.owner.email,
    telefone='',
    cargo='Administrador',
    is_admin=True,
    is_active=True,
    loja_id=loja.id
)
```

**Resultado**:
```
✅ Admin criado com sucesso!
   Nome: Nayara Souza
   Email: pjluiz25@hotmail.com
   Cargo: Administrador
   is_admin: True
```

### 2. Formulário Corrigido

**Antes** (❌ Incorreto):
```typescript
<select name="funcao">
  <option value="administrador">Administrador</option>
  <option value="gerente">Gerente</option>
  <option value="profissional">Profissional/Esteticista</option>  ❌ ERRADO
  <option value="atendente">Atendente/Recepcionista</option>
  <option value="caixa">Caixa</option>
  <option value="visualizador">Visualizador</option>
</select>
```

**Depois** (✅ Correto):
```typescript
<select name="funcao">
  <option value="administrador">Administrador</option>
  <option value="gerente">Gerente</option>
  <option value="atendente">Atendente/Recepcionista</option>
  <option value="caixa">Caixa</option>
  <option value="visualizador">Visualizador</option>
</select>
<p className="text-xs text-gray-500 mt-1">
  💡 Para cadastrar profissionais (esteticistas), use o botão "Profissional"
</p>
```

### 3. Campo "Especialidade" Removido

**Antes** (❌ Redundante):
```typescript
<div>
  <label>Especialidade</label>
  <input
    type="text"
    value={formData.especialidade}
    placeholder="Ex: Limpeza de Pele, Massagem... (para profissionais)"
  />
</div>
```

**Depois** (✅ Removido):
- Campo removido do formulário
- Campo removido do estado `formData`
- Campo removido do payload da API
- Campo removido da exibição na lista

**Motivo**: Especialidade é exclusiva de **Profissionais**, não de Funcionários.

### 4. Placeholder do Campo "Cargo" Atualizado

**Antes**:
```typescript
placeholder="Ex: Esteticista, Recepcionista..."  ❌
```

**Depois**:
```typescript
placeholder="Ex: Gerente, Recepcionista, Caixa..."  ✅
<p className="text-xs text-gray-500 mt-1">
  ⚠️ Não cadastre profissionais aqui (use o botão "Profissional")
</p>
```

## 📊 Estrutura Correta

### Modelo Funcionario (Clínica)
```python
class Funcionario(LojaIsolationMixin, models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cargo = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)  # Admin da loja
    is_active = models.BooleanField(default=True)
```

**Campos**:
- ✅ `nome`, `email`, `telefone`, `cargo`
- ✅ `is_admin` (marca admin da loja)
- ✅ `is_active` (ativo/inativo)
- ❌ **NÃO tem** `funcao` (diferente de outros apps)
- ❌ **NÃO tem** `especialidade` (só profissionais têm)

### Modelo Profissional (Clínica)
```python
class Profissional(LojaIsolationMixin, models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    especialidade = models.CharField(max_length=100)  # ✅ Só profissionais
    registro_profissional = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
```

## 🚀 Deploys Realizados

### Deploy v468 - Frontend
- Arquivo: `frontend/components/clinica/modals/ModalFuncionarios.tsx`
- Removido opção "Profissional/Esteticista"
- Removido campo "Especialidade"
- Adicionadas mensagens de orientação
- Status: ✅ Produção

### Deploy v460 - Backend
- Arquivo: `backend/criar_admin_clinica.py`
- Script para criar admin manualmente
- Status: ✅ Executado com sucesso

## 🧪 Como Testar

1. Acessar: https://lwksistemas.com.br/loja/clinica-harmonis-5898/dashboard
2. Clicar no botão "👥 Funcionários"
3. Verificar:
   - ✅ Admin "Nayara Souza" aparece na lista
   - ✅ Badge "Admin" azul visível
   - ✅ Botões "Editar" e "Excluir" desabilitados para admin
4. Clicar em "+ Novo Funcionário"
5. Verificar formulário:
   - ✅ Sem opção "Profissional/Esteticista"
   - ✅ Sem campo "Especialidade"
   - ✅ Mensagens de orientação presentes

## 📝 Arquivos Modificados

```
frontend/components/clinica/modals/ModalFuncionarios.tsx
backend/criar_admin_clinica.py (novo)
criar_admin_producao.sh (novo)
```

## ✨ Resultado Final

Sistema de Funcionários agora está **100% correto**:
- ✅ Admin criado e visível
- ✅ Formulário sem opções redundantes
- ✅ Separação clara: Funcionários ≠ Profissionais
- ✅ Proteções para admin (não pode editar/excluir)
- ✅ Mensagens de orientação para usuário

---

**Data**: 08/02/2026
**Versão**: v468
**Status**: ✅ Concluído e em Produção
