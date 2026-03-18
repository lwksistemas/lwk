# Análise Final: Problema na Criação de Lojas CRM

## Situação Crítica

Sistema **NÃO CONSEGUE** criar lojas CRM desde 17/03/2026.

## Histórico Completo

### Quando Funcionava
- **Última versão funcional**: Antes do commit `5fcce997` (17/03/2026 17:48)
- **Código que funcionava**: Commit `0da66668`

### O Que Mudou
Commit `5fcce997` adicionou backend PostgreSQL customizado para melhorar criação de lojas.

### Tentativas de Correção (TODAS FALHARAM)

#### v1001-v1005: Tentativas com Backend Customizado
- v1001: `set_session` → Erro "cannot be used inside transaction"
- v1002-v1004: OPTIONS com search_path → Schema vazio
- v1005: PGOPTIONS → Schema vazio

#### v1006: Correção de Sintaxe
- Corrigiu erro de sintaxe mas schema continua vazio

#### v1007: Remover Backend Customizado
- Voltou para ENGINE padrão → Schema vazio

#### v1008: ALTER DATABASE
- Definiu search_path padrão no banco → Schema vazio

#### v1009: Restaurar Código Original (v1111)
- **Restaurado código EXATO do commit 0da66668**
- **AINDA FALHA** → Schema vazio

## Diagnóstico Final

### Problema NÃO É o Código
O código que funcionava ANTES (commit 0da66668) **NÃO FUNCIONA MAIS** mesmo sendo restaurado exatamente.

### Hipóteses

1. **Heroku mudou configuração do PostgreSQL**
   - PgBouncer pode ter mudado comportamento
   - Versão do PostgreSQL pode ter sido atualizada

2. **Django mudou comportamento**
   - Versão 4.2.11 pode ter bug com search_path
   - `call_command('migrate')` pode ter mudado internamente

3. **Migrations estão corrompidas**
   - Estado das migrations pode estar inconsistente
   - Tabelas podem estar sendo criadas em local desconhecido

### Evidências

```
✅ Schema criado com sucesso
✅ search_path configurado: loja_36971645898,public
✅ Migrations executam SEM erro
❌ Schema fica VAZIO (0 tabelas)
❌ Tabelas NÃO aparecem em public
❌ Tabelas NÃO aparecem no schema da loja
```

**CONCLUSÃO**: As tabelas estão sendo criadas em algum lugar desconhecido OU não estão sendo criadas.

## Soluções Possíveis

### Opção 1: Rollback Completo (RECOMENDADO)
Fazer rollback para commit ANTES de `5fcce997`:

```bash
git revert 5fcce997..HEAD
git push heroku master
```

### Opção 2: Investigação Profunda
1. Conectar diretamente no PostgreSQL do Heroku
2. Executar migrations manualmente
3. Ver onde as tabelas estão sendo criadas
4. Verificar logs completos do PostgreSQL

### Opção 3: Criar Tabelas Manualmente
Script Python que cria tabelas diretamente no schema usando SQL:

```python
# Copiar estrutura de uma loja existente
CREATE TABLE "loja_xxx".stores_store (LIKE public.stores_store INCLUDING ALL);
```

### Opção 4: Migrar para django-tenants
Usar biblioteca especializada em multi-tenancy com schemas PostgreSQL.

## Impacto no Negócio

- ❌ Sistema NÃO pode criar novas lojas CRM
- ✅ Lojas existentes continuam funcionando
- ⚠️ Problema afeta APENAS criação de novas lojas
- ⏰ Problema existe há **1 dia** (desde 17/03)

## Recomendação Urgente

**FAZER ROLLBACK IMEDIATO** para versão antes de `5fcce997`.

Motivo: Código que funcionava não funciona mais, indicando problema ambiental ou de versão que não podemos controlar.

## Próximos Passos

1. **URGENTE**: Fazer rollback
2. Testar criação de loja após rollback
3. Se funcionar, investigar o que mudou no ambiente
4. Considerar abordagem alternativa (django-tenants ou SQL manual)

## Lojas Órfãs Criadas Durante Testes

IDs para limpar: 108, 109, 112, 113, 114, 115, 116, 117, 118, 119

```bash
heroku run "python backend/limpar_orfaos_completo.py" --app lwksistemas
```
