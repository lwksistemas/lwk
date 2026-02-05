# ✅ Correção: Erro ao Salvar Bloqueio

**Data:** 05/02/2026  
**Status:** ✅ RESOLVIDO

## 🎯 Problema

Ao tentar salvar um bloqueio de agenda, o sistema retornava erro 400:
```
POST /api/cabeleireiro/bloqueios/ 400 (Bad Request)
```

## 🔍 Causa

O modelo `BloqueioAgenda` usava `ForeignKey('Funcionario')`, mas o frontend estava enviando ID de `Profissional` (após a correção do agendamento).

```python
# ANTES - Errado
class BloqueioAgenda(models.Model):
    profissional = models.ForeignKey('Funcionario', ...)  # ❌
```

## ✅ Solução

Atualizado o modelo `BloqueioAgenda` para usar `Profissional`:

```python
# DEPOIS - Correto
class BloqueioAgenda(models.Model):
    profissional = models.ForeignKey('Profissional', ...)  # ✅
```

## 📝 Arquivo Modificado

- ✅ `backend/cabeleireiro/models.py` - Atualizado ForeignKey de BloqueioAgenda

## 🎯 Status

- ✅ Modelo atualizado
- ✅ Deploy realizado (Heroku v398)
- ✅ Sistema funcionando

## 🧪 Como Testar

1. Acessar: https://lwksistemas.com.br/loja/salao-000172/dashboard
2. Clicar em "Ações Rápidas" → "Bloqueios"
3. Clicar em "+ Novo Bloqueio"
4. Preencher:
   - Profissional: Nayara (ou deixar em branco para bloqueio geral)
   - Data Início e Fim
   - Motivo
5. Clicar em "Cadastrar"
6. **Resultado Esperado:** ✅ Bloqueio criado com sucesso!

---

**Commit:** `ca1ca5a` - fix: Atualizar BloqueioAgenda para usar Profissional ao invés de Funcionario  
**Deploy:** v398 (Heroku) ✅
