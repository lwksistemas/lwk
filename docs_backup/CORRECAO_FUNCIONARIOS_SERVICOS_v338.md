# Correção: Admin Aparece em Funcionários - Dashboard Serviços v338

## 🎯 Problema
O administrador da loja não aparecia automaticamente na lista de funcionários do dashboard de serviços (servico-5889).

## 🔍 Causa Raiz
O modelo `Funcionario` em `backend/servicos/models.py` não tinha o `LojaIsolationManager` configurado, causando erro ao tentar usar o método `all_without_filter()` na função `ensure_owner_as_funcionario()`.

**Erro no log:**
```
AttributeError: 'Manager' object has no attribute 'all_without_filter'
```

## ✅ Solução Implementada

### 1. Adicionado LojaIsolationManager ao modelo Funcionario
**Arquivo:** `backend/servicos/models.py`

```python
from core.mixins import LojaIsolationMixin, LojaIsolationManager

class Funcionario(LojaIsolationMixin, BaseFuncionario):
    """Funcionários"""
    
    objects = LojaIsolationManager()  # ✅ ADICIONADO

    class Meta:
        db_table = 'servicos_funcionarios'
        ordering = ['nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
```

### 2. Melhorada função ensure_owner_as_funcionario
**Arquivo:** `backend/core/utils.py`

Agora a função detecta automaticamente se o manager tem `all_without_filter()` e se adapta:

```python
def ensure_owner_as_funcionario(funcionario_model, cargo_padrao='Administrador'):
    # ...
    
    # Verificar se o manager tem all_without_filter (LojaIsolationManager)
    manager = funcionario_model.objects
    if hasattr(manager, 'all_without_filter'):
        # Manager customizado com bypass de isolamento
        base_queryset = manager.all_without_filter()
    else:
        # Manager padrão do Django - usar filter direto
        base_queryset = manager.all()
    
    # Verificar se já existe
    exists = base_queryset.filter(
        loja_id=loja_id, 
        email=owner.email
    ).exists()
    
    if not exists:
        base_queryset.create(
            nome=owner.get_full_name() or owner.username or owner.email.split('@')[0],
            email=owner.email,
            telefone=getattr(owner, 'telefone', '') or '',
            cargo=cargo_padrao,
            is_admin=True,
            loja_id=loja_id,
        )
    # ...
```

## 📦 Deploy

### Backend v338
```bash
git add backend/core/utils.py backend/servicos/models.py
git commit -m "fix: adiciona LojaIsolationManager ao Funcionario de servicos e melhora ensure_owner_as_funcionario"
git push heroku master
```

**Status:** ✅ Deploy concluído com sucesso

## 🧪 Como Testar

1. Acesse: https://lwksistemas.com.br/loja/servico-5889/dashboard
2. Faça login com o usuário admin da loja (servico@teste.com)
3. Clique no botão "👥 Gerenciar Funcionários"
4. **Resultado esperado:** O admin da loja deve aparecer automaticamente na lista

## 📊 Consistência entre Apps

Agora todos os apps têm o `LojaIsolationManager` configurado:

- ✅ `clinica_estetica/models.py` - Funcionario (já tinha)
- ✅ `restaurante/models.py` - Funcionario (já tinha)
- ✅ `servicos/models.py` - Funcionario (CORRIGIDO)

## 🔒 Segurança

A função `ensure_owner_as_funcionario()` agora é mais robusta e funciona com qualquer tipo de manager (customizado ou padrão do Django), mantendo a segurança do isolamento de dados por loja.

## 📝 Arquivos Modificados

1. `backend/servicos/models.py` - Adicionado `LojaIsolationManager`
2. `backend/core/utils.py` - Melhorada detecção de manager

## 🎉 Resultado

O administrador da loja agora aparece automaticamente na lista de funcionários do dashboard de serviços, igual ao comportamento da clínica estética.
