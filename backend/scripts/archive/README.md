# Scripts Arquivados

Este diretório contém scripts one-off que foram executados para correções específicas ou debugging.

## ⚠️ IMPORTANTE

**Estes scripts NÃO devem ser executados novamente.**

São mantidos apenas como referência histórica e documentação de correções aplicadas.

## Estrutura

### 2026-03-debug/
Scripts de debug e diagnóstico usados para investigar problemas específicos.

### 2026-03-client-fixes/
Scripts de correção específicos para clientes individuais (one-off fixes).

### 2026-03-tests/
Scripts de teste e validação que não fazem parte da suite de testes oficial.

## Migração para Management Commands

Os scripts de uso recorrente foram migrados para Django Management Commands:

- `verificar_orfaos.py` → `python manage.py check_orfaos`
- `corrigir_database_names.py` → `python manage.py fix_database_names`
- `limpar_orfaos_completo.py` → `python manage.py cleanup_orfaos`
- `criar_loja_teste_crm.py` → `python manage.py create_loja`
- `check_schemas.py` → `python manage.py check_schemas`

Veja `backend/management/commands/README.md` para mais informações.

---

**Arquivado em:** 31 de Março de 2026  
**Motivo:** Refatoração e organização do código
