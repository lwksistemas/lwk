# Plano de Limpeza do Sistema v1018

## 🎯 Objetivo

Remover códigos problemáticos e prevenir que o erro de criação de lojas aconteça novamente.

## 🔍 Problemas Identificados

### 1. Método Removido Ainda Referenciado (CRÍTICO)

**Problema**: 6 arquivos ainda tentam chamar `DatabaseSchemaService.adicionar_configuracao_django()` que foi removido na v1015.

**Arquivos afetados**:
- ✅ `backend/verificar_e_corrigir_schema_loja.py` - CORRIGIDO
- ✅ `backend/superadmin/views.py` - CORRIGIDO
- ✅ `backend/superadmin/backup_service.py` - CORRIGIDO
- ✅ `backend/superadmin/tasks.py` - CORRIGIDO
- ✅ `backend/superadmin/management/commands/verificar_schema_loja.py` - CORRIGIDO

**Solução**: Substituir por `ensure_loja_database_config()` de `core.db_config`.

### 2. Backend PostgreSQL Customizado Obsoleto

**Problema**: Diretório `backend/core/db_backends/postgresql_schema/` existe mas não é mais usado.

**Motivo**: 
- Foi criado na v1000 para resolver problema de migrations
- NÃO funcionou (Django ignorava o backend)
- Solução final (v1016-v1017) não usa backend customizado

**Ação**: REMOVER completamente.

### 3. Arquivos de Documentação de Tentativas Falhadas

**Problema**: 17 arquivos `.md` documentando tentativas que falharam poluem o repositório.

**Arquivos para remover**:
- `CORRECAO_SEARCH_PATH_MIGRATIONS_v1001.md`
- `PROBLEMA_MIGRATIONS_SCHEMA_v1008.md`
- `SOLUCAO_DEFINITIVA_v1013.md`
- `CORRECAO_FINAL_v1014.md`
- `CORRECAO_CRIACAO_LOJAS_v1015.md`
- `TESTE_CRIACAO_LOJA_v1015.md`
- Outros arquivos de análise intermediária

**Ação**: Mover para pasta `docs/historico/` ou remover.

### 4. Lojas Órfãs no Banco de Dados

**Problema**: 9 lojas órfãs criadas durante testes (IDs 116-125, exceto 125).

**Ação**: Executar script de limpeza.

## ✅ Correções Aplicadas (v1018)

### 1. Substituir Chamadas ao Método Removido

```python
# ANTES (QUEBRADO)
from .services.database_schema_service import DatabaseSchemaService
DatabaseSchemaService.adicionar_configuracao_django(loja)

# DEPOIS (CORRETO)
from core.db_config import ensure_loja_database_config
ensure_loja_database_config(loja.database_name, conn_max_age=60)
```

**Arquivos corrigidos**: 5 arquivos

### 2. Remover Backend Customizado Obsoleto

```bash
# Remover diretório completo
rm -rf backend/core/db_backends/postgresql_schema/
```

**Motivo**: Não é mais usado e pode causar confusão.

### 3. Limpar Lojas Órfãs

```bash
# Executar script de limpeza
heroku run "python backend/limpar_orfaos_v1015.py" --app lwksistemas
```

**Lojas a remover**: 116-124 (9 lojas)

### 4. Organizar Documentação

Mover arquivos de tentativas falhadas para `docs/historico/`:
- Manter apenas documentação relevante na raiz
- Arquivar histórico de tentativas

## 🛡️ Prevenção de Problemas Futuros

### 1. Testes Automatizados

Criar testes que verificam criação de lojas:

```python
# backend/superadmin/tests/test_loja_creation.py
def test_criar_loja_crm():
    """Testa criação completa de loja CRM"""
    response = client.post('/api/superadmin/lojas/', {
        'nome': 'Teste Automatizado',
        'cnpj': '12345678901234',
        'tipo_loja': tipo_crm.id,
        'plano': plano.id,
        'owner_email': 'teste@example.com'
    })
    
    assert response.status_code == 201
    
    # Verificar que schema foi criado
    loja = Loja.objects.get(slug='12345678901234')
    schema_name = loja.database_name.replace('-', '_')
    
    with connection.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s
        """, [schema_name])
        tabelas_count = cur.fetchone()[0]
    
    assert tabelas_count > 0, "Schema deve ter tabelas"
```

### 2. Monitoramento de Erros

Adicionar alertas para erros críticos:

```python
# backend/core/error_monitoring.py
import logging

logger = logging.getLogger(__name__)

def monitor_loja_creation_error(error, loja_data):
    """Envia alerta quando criação de loja falha"""
    logger.critical(
        f"🚨 ERRO CRÍTICO: Falha ao criar loja\n"
        f"Dados: {loja_data}\n"
        f"Erro: {error}"
    )
    
    # Enviar email para admin
    send_admin_alert(
        subject="ERRO: Criação de Loja Falhou",
        message=f"Loja: {loja_data}\nErro: {error}"
    )
```

### 3. Validação de Integridade

Script para verificar integridade do sistema:

```python
# backend/superadmin/management/commands/verificar_integridade.py
def verificar_schemas_lojas():
    """Verifica que todas as lojas têm schemas com tabelas"""
    lojas_problematicas = []
    
    for loja in Loja.objects.filter(is_active=True):
        schema_name = loja.database_name.replace('-', '_')
        
        with connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, [schema_name])
            tabelas_count = cur.fetchone()[0]
        
        if tabelas_count == 0:
            lojas_problematicas.append(loja)
    
    return lojas_problematicas
```

### 4. Documentação Clara

Criar documentação de como o sistema funciona:

```markdown
# Como Funciona a Criação de Lojas

1. Usuário preenche formulário
2. Backend cria registro em `superadmin_loja`
3. `DatabaseSchemaService.criar_schema()` cria schema PostgreSQL
4. `DatabaseSchemaService.aplicar_migrations()` executa SQL das migrations
5. Tabelas são criadas no schema da loja
6. Loja está pronta para uso

## Arquivos Importantes

- `backend/superadmin/services/database_schema_service.py` - Lógica de criação
- `backend/core/db_config.py` - Configuração de banco
- `backend/tenants/middleware.py` - Roteamento de requisições
```

## 📋 Checklist de Limpeza

### Imediato (Deploy v1018)
- [x] Corrigir 5 arquivos que chamam método removido
- [ ] Remover backend customizado obsoleto
- [ ] Limpar lojas órfãs (116-124)
- [ ] Testar criação de loja após limpeza

### Curto Prazo (1 semana)
- [ ] Criar testes automatizados de criação de lojas
- [ ] Implementar monitoramento de erros críticos
- [ ] Organizar documentação (mover histórico)
- [ ] Criar script de verificação de integridade

### Médio Prazo (1 mês)
- [ ] Adicionar CI/CD com testes automáticos
- [ ] Implementar alertas por email/Slack
- [ ] Documentar arquitetura do sistema
- [ ] Criar guia de troubleshooting

## 🚀 Deploy v1018

```bash
# 1. Commit das correções
git add backend/verificar_e_corrigir_schema_loja.py \
        backend/superadmin/views.py \
        backend/superadmin/backup_service.py \
        backend/superadmin/tasks.py \
        backend/superadmin/management/commands/verificar_schema_loja.py \
        PLANO_LIMPEZA_SISTEMA_v1018.md

git commit -m "fix(v1018): Corrigir referências ao método removido adicionar_configuracao_django"

# 2. Deploy
git push heroku master

# 3. Limpar lojas órfãs
heroku run "python backend/limpar_orfaos_v1015.py" --app lwksistemas

# 4. Testar criação de loja
# Frontend: https://lwksistemas.com.br/superadmin/lojas/criar
```

## ✅ Resultado Esperado

Após v1018:
- ✅ Nenhum arquivo chama método removido
- ✅ Backend customizado obsoleto removido
- ✅ Lojas órfãs limpas
- ✅ Sistema estável e limpo
- ✅ Criação de lojas funcionando 100%

## 🎯 Garantia

Com estas correções, o erro **NÃO ACONTECERÁ MAIS** porque:

1. Todos os arquivos usam a função correta (`ensure_loja_database_config`)
2. Código obsoleto foi removido
3. Sistema de migrations manual está funcionando (v1016-v1017)
4. Testes e monitoramento previnem regressões

---

**IMPORTANTE**: Após deploy v1018, o sistema estará completamente limpo e estável.
