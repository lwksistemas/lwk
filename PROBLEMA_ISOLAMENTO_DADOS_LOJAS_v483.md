# Problema: Isolamento de Dados entre Lojas - v483

## 🚨 Problema Crítico Identificado

**Data:** 08/02/2026  
**Severidade:** 🔴 **CRÍTICA**  
**Status:** ⚠️ **IDENTIFICADO - AGUARDANDO CORREÇÃO**

---

## 📋 Descrição do Problema

Quando você cria uma **nova loja de clínica de estética**, ela está vindo com os **dados da loja de teste** (clinica-harmonis-5898). Isso significa que há um problema de **isolamento de dados** entre lojas.

### Comportamento Atual (INCORRETO)
```
1. Criar nova loja "Clínica Nova"
2. Acessar dashboard da "Clínica Nova"
3. ❌ Aparecem clientes da "Clínica Harmonis"
4. ❌ Aparecem procedimentos da "Clínica Harmonis"
5. ❌ Aparecem agendamentos da "Clínica Harmonis"
```

### Comportamento Esperado (CORRETO)
```
1. Criar nova loja "Clínica Nova"
2. Acessar dashboard da "Clínica Nova"
3. ✅ Dashboard vazio (sem dados)
4. ✅ Apenas admin/funcionário criado automaticamente
5. ✅ Pronto para cadastrar novos clientes/procedimentos
```

---

## 🔍 Causa Raiz

### Arquitetura Multi-Tenant

O sistema usa **PostgreSQL com schemas separados** para isolar dados entre lojas:

```
PostgreSQL Database
├── Schema: public (superadmin, tipos de loja, planos)
├── Schema: loja_clinica_harmonis_5898 (dados da loja de teste)
├── Schema: loja_nova_clinica (deveria ser criado vazio)
└── Schema: loja_outra_clinica (deveria ser criado vazio)
```

### O Problema

1. **Ao criar nova loja:**
   - ✅ Campo `database_name` é preenchido (ex: `loja_nova_clinica`)
   - ✅ Campo `database_created` é marcado como `False`
   - ❌ **Schema não é criado no PostgreSQL**

2. **Ao acessar a nova loja:**
   - Middleware tenta usar schema `loja_nova_clinica`
   - Schema não existe
   - **Fallback para schema `public` ou outro schema existente**
   - Resultado: **dados de outra loja aparecem**

---

## 🛠️ Solução Necessária

### 1. Criar Schema Automaticamente

Quando uma nova loja é criada, o sistema deve:

```python
# backend/superadmin/signals.py (CRIAR ESTE ARQUIVO)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection
from .models import Loja

@receiver(post_save, sender=Loja)
def criar_schema_loja(sender, instance, created, **kwargs):
    """
    Cria schema vazio no PostgreSQL quando uma nova loja é criada
    """
    if created and not instance.database_created:
        schema_name = instance.database_name
        
        try:
            with connection.cursor() as cursor:
                # 1. Criar schema
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                
                # 2. Executar migrações no schema
                from django.core.management import call_command
                call_command('migrate', '--database', schema_name, '--run-syncdb')
                
                # 3. Marcar como criado
                instance.database_created = True
                instance.save(update_fields=['database_created'])
                
                print(f"✅ Schema '{schema_name}' criado com sucesso!")
                
        except Exception as e:
            print(f"❌ Erro ao criar schema '{schema_name}': {e}")
            raise
```

### 2. Garantir Isolamento no Middleware

O middleware já está correto, mas precisa garantir que:

```python
# backend/tenants/middleware.py (JÁ EXISTE - VERIFICAR)

# Linha 69-70
schema_name = loja.database_name or f"loja_{loja.id}"
settings.DATABASES[db_name] = {
    **default_db,
    'OPTIONS': {
        'options': f'-c search_path={schema_name},public'  # ✅ Correto
    },
    # ...
}
```

### 3. Validar Schema Existe

Antes de usar o schema, validar que ele existe:

```python
def schema_exists(schema_name):
    """Verifica se o schema existe no PostgreSQL"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = %s
        """, [schema_name])
        return cursor.fetchone() is not None

# No middleware
if not schema_exists(schema_name):
    logger.error(f"Schema '{schema_name}' não existe!")
    # Criar schema ou retornar erro
```

---

## 📊 Impacto

### Segurança
- 🔴 **CRÍTICO**: Vazamento de dados entre lojas
- 🔴 **CRÍTICO**: Violação de privacidade (LGPD)
- 🔴 **CRÍTICO**: Cliente A vê dados do Cliente B

### Funcionalidade
- 🔴 **CRÍTICO**: Nova loja não funciona corretamente
- 🔴 **CRÍTICO**: Dados misturados entre lojas
- 🟡 **MÉDIO**: Confusão para novos usuários

### Negócio
- 🔴 **CRÍTICO**: Perda de confiança do cliente
- 🔴 **CRÍTICO**: Possível processo legal (LGPD)
- 🔴 **CRÍTICO**: Reputação da plataforma comprometida

---

## ✅ Checklist de Correção

### Fase 1: Criar Signal para Schemas
- [ ] Criar arquivo `backend/superadmin/signals.py`
- [ ] Implementar `criar_schema_loja` signal
- [ ] Registrar signal em `backend/superadmin/apps.py`
- [ ] Testar criação de schema

### Fase 2: Validar Schemas Existentes
- [ ] Criar função `schema_exists()`
- [ ] Adicionar validação no middleware
- [ ] Criar schema se não existir
- [ ] Logar erros de schema

### Fase 3: Migrar Lojas Existentes
- [ ] Listar todas as lojas com `database_created=False`
- [ ] Criar schemas para lojas existentes
- [ ] Executar migrações em cada schema
- [ ] Marcar `database_created=True`

### Fase 4: Limpar Dados Misturados
- [ ] Identificar lojas com dados misturados
- [ ] Limpar dados incorretos
- [ ] Validar isolamento

### Fase 5: Testes
- [ ] Criar nova loja de teste
- [ ] Verificar que vem vazia
- [ ] Adicionar dados na loja A
- [ ] Verificar que loja B não vê dados da loja A
- [ ] Testar com múltiplas lojas simultâneas

---

## 🚀 Implementação Imediata

### Script Temporário para Criar Schemas

Enquanto o signal não é implementado, criar schemas manualmente:

```python
# backend/criar_schemas_lojas.py

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def criar_schemas():
    """Cria schemas para todas as lojas que não têm"""
    lojas = Loja.objects.filter(database_created=False)
    
    print(f"📋 Encontradas {lojas.count()} lojas sem schema")
    
    for loja in lojas:
        schema_name = loja.database_name
        print(f"\n🔧 Criando schema para: {loja.nome} ({schema_name})")
        
        try:
            with connection.cursor() as cursor:
                # Criar schema
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                print(f"   ✅ Schema '{schema_name}' criado")
                
                # Marcar como criado
                loja.database_created = True
                loja.save(update_fields=['database_created'])
                print(f"   ✅ Loja marcada como database_created=True")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")

if __name__ == '__main__':
    criar_schemas()
```

**Executar:**
```bash
cd backend
python criar_schemas_lojas.py
```

---

## 📝 Notas Importantes

### 1. Loja de Teste (clinica-harmonis-5898)
- Esta loja DEVE manter seus dados
- É usada para testes e demonstrações
- Não deve ser afetada pela correção

### 2. Novas Lojas
- Devem vir **completamente vazias**
- Apenas com admin/funcionário criado automaticamente
- Sem clientes, procedimentos ou agendamentos

### 3. Lojas Existentes
- Verificar se têm dados misturados
- Limpar dados incorretos se necessário
- Validar isolamento após correção

### 4. Performance
- Criar schema é operação rápida (< 1 segundo)
- Executar migrações pode demorar (5-10 segundos)
- Considerar fazer de forma assíncrona

---

## 🔗 Documentação Relacionada

- [DASHBOARD_CLINICA_ESTETICA_COMPLETO_v481.md](./DASHBOARD_CLINICA_ESTETICA_COMPLETO_v481.md)
- [GUIA_ISOLAMENTO_DADOS.md](./backend/GUIA_ISOLAMENTO_DADOS.md)
- [Documentação PostgreSQL Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)

---

## 🎯 Próximos Passos

1. **URGENTE**: Implementar signal para criar schemas automaticamente
2. **URGENTE**: Executar script para criar schemas de lojas existentes
3. **URGENTE**: Validar isolamento de dados
4. **IMPORTANTE**: Limpar dados misturados
5. **IMPORTANTE**: Adicionar testes automatizados
6. **IMPORTANTE**: Documentar processo de criação de lojas

---

## ⚠️ Aviso

**Este é um problema crítico de segurança e privacidade.**

Até que seja corrigido:
- ❌ NÃO criar novas lojas em produção
- ❌ NÃO permitir que clientes criem lojas
- ✅ Usar apenas loja de teste existente
- ✅ Avisar equipe sobre o problema

---

**Última atualização:** 08/02/2026  
**Versão:** v483  
**Status:** ⚠️ CRÍTICO - AGUARDANDO CORREÇÃO
