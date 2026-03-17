# Correção: Arquivos Corrompidos (v997)

**Data**: 17/03/2026  
**Status**: ✅ CORRIGIDO

---

## 🎯 PROBLEMA

Ao tentar criar nova loja, o sistema falhou com erro:

```
ModuleNotFoundError: No module named 'core.db_backends.postgresql_schema.base'
'core.db_backends.postgresql_schema' is not a package

django.core.exceptions.ImproperlyConfigured: 'core.db_backends.postgresql_schema' 
isn't an available database backend
```

---

## 🔍 CAUSA RAIZ

Os arquivos `backend/core/db_backends/postgresql_schema.py` e `backend/core/db_config.py` foram corrompidos durante a análise anterior (v994-v996).

**Corrupção**: Tags XML `</content></file>` foram inseridas no meio das regex:

```python
# CORROMPIDO
if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*</content>
</file>, schema_name):

# CORRETO
if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
```

---

## 🔧 CORREÇÃO APLICADA

### Arquivos Corrigidos

1. **backend/core/db_backends/postgresql_schema.py**
   - Linha 30: Regex corrigida
   
2. **backend/core/db_config.py**
   - Linha 45: Regex corrigida

### Correção

Ambos os arquivos foram reescritos completamente com o código correto.

---

## ✅ VERIFICAÇÃO

```bash
heroku run cat backend/core/db_backends/postgresql_schema.py --app lwksistemas | head -40
# ✅ Arquivo correto no Heroku
```

---

## 📝 NOTA IMPORTANTE

Este é o MESMO problema que foi corrigido na v993. Os arquivos foram corrompidos novamente durante a análise de código nas versões v994-v996.

**Prevenção**: Evitar usar ferramentas que possam inserir tags XML no meio do código Python.

---

## 🎯 PRÓXIMO PASSO

Testar criação de nova loja para confirmar que o sistema está funcionando.
