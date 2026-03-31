# GUIA DE CONTINUAÇÃO DA REFATORAÇÃO
**Data:** 31 de Março de 2026  
**Para:** Equipe de Desenvolvimento  
**Objetivo:** Instruções práticas para continuar a refatoração

---

## 🎯 VISÃO GERAL

Este guia fornece instruções passo a passo para continuar a refatoração do sistema CRM.

**Status Atual:**
- ✅ Fase 1 Concluída (90 linhas reduzidas, infraestrutura criada)
- 🔄 Fase 2 Planejada (1.000+ linhas a reduzir)
- 🔄 Fase 3 Planejada (polimento e padronização)

---

## 📋 FASE 2: PRÓXIMAS AÇÕES

### 1. MIGRAR MODAIS PARA GENERICCRUDMODAL

#### Passo 1: Escolher um Modal para Migrar

Comece com o mais simples: `ModalClientes` do cabeleireiro

**Arquivo Original:** `frontend/components/cabeleireiro/modals/ModalClientes.tsx`

#### Passo 2: Criar Configuração de Campos

```typescript
// frontend/components/cabeleireiro/config/clienteFields.ts
import { FieldConfig } from '@/components/shared/GenericCrudModal';

export const clienteFields: FieldConfig[] = [
  { 
    name: 'nome', 
    label: 'Nome', 
    type: 'text', 
    required: true,
    placeholder: 'Nome completo do cliente'
  },
  { 
    name: 'email', 
    label: 'E-mail', 
    type: 'email',
    placeholder: 'email@exemplo.com'
  },
  { 
    name: 'telefone', 
    label: 'Telefone', 
    type: 'tel', 
    required: true,
    placeholder: '(00) 00000-0000'
  },
  { 
    name: 'cpf', 
    label: 'CPF', 
    type: 'text',
    placeholder: '000.000.000-00',
    maxLength: 14
  },
  { 
    name: 'data_nascimento', 
    label: 'Data de Nascimento', 
    type: 'date'
  },
  { 
    name: 'observacoes', 
    label: 'Observações', 
    type: 'textarea',
    rows: 3
  },
];
```

#### Passo 3: Substituir Modal Antigo

```typescript
// Antes
import { ModalClientes } from '@/components/cabeleireiro/modals/ModalClientes';

<ModalClientes loja={loja} onClose={handleClose} />

// Depois
import { GenericCrudModal } from '@/components/shared/GenericCrudModal';
import { clienteFields } from '@/components/cabeleireiro/config/clienteFields';

<GenericCrudModal
  title="Clientes"
  endpoint="/cabeleireiro/clientes/"
  fields={clienteFields}
  loja={loja}
  onClose={handleClose}
  onSuccess={handleSuccess}
/>
```

#### Passo 4: Testar

```bash
# Iniciar servidor de desenvolvimento
cd frontend
npm run dev

# Testar:
# 1. Abrir modal de clientes
# 2. Adicionar novo cliente
# 3. Editar cliente existente
# 4. Excluir cliente
# 5. Verificar validações
```

#### Passo 5: Remover Arquivo Antigo

```bash
# Após confirmar que funciona
git rm frontend/components/cabeleireiro/modals/ModalClientes.tsx
git commit -m "refactor: migrar ModalClientes para GenericCrudModal"
```

#### Passo 6: Repetir para Outros Modais

Ordem sugerida (do mais simples ao mais complexo):
1. ✅ ModalClientes (cabeleireiro)
2. ModalClientes (clinica)
3. ModalClientes (servicos)
4. ModalServicos (cabeleireiro)
5. ModalServicos (clinica)
6. ModalFuncionarios (cabeleireiro)
7. ModalFuncionarios (clinica)
8. ModalAgendamentos (cabeleireiro) - mais complexo
9. ModalAgendamentos (clinica) - mais complexo

---

### 2. MIGRAR SCRIPTS PARA MANAGEMENT COMMANDS

#### Passo 1: Escolher um Script

Comece com: `check_schemas.py`

#### Passo 2: Criar Django Command

```python
# backend/management/commands/check/check_schemas.py
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Verifica schemas do banco de dados PostgreSQL'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar informações detalhadas',
        )
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('Verificando schemas...'))
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%'
                ORDER BY schema_name
            """)
            schemas = cursor.fetchall()
        
        if not schemas:
            self.stdout.write(self.style.WARNING('Nenhum schema encontrado'))
            return
        
        self.stdout.write(f'\nEncontrados {len(schemas)} schemas:')
        for schema in schemas:
            self.stdout.write(f'  - {schema[0]}')
            
            if verbose:
                # Mostrar tabelas do schema
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = '{schema[0]}'
                        ORDER BY table_name
                    """)
                    tables = cursor.fetchall()
                    self.stdout.write(f'    Tabelas: {len(tables)}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Verificação concluída'))
```

#### Passo 3: Testar Command

```bash
# Testar comando
python manage.py check_schemas

# Testar com verbose
python manage.py check_schemas --verbose

# Verificar help
python manage.py check_schemas --help
```

#### Passo 4: Remover Script Antigo

```bash
# Após confirmar que funciona
git rm backend/check_schemas.py
git commit -m "refactor: migrar check_schemas para management command"
```

#### Passo 5: Repetir para Outros Scripts

Ordem sugerida:
1. ✅ check_schemas.py
2. verificar_orfaos.py → check/check_orfaos.py
3. limpar_orfaos_completo.py → cleanup/cleanup_orfaos.py
4. criar_loja_teste_crm.py → create/create_loja.py
5. corrigir_database_names.py → fix/fix_database_names.py

---

### 3. REMOVER CÓDIGO NÃO UTILIZADO

#### Passo 1: Remover Arquivos SQLite

```bash
# Adicionar ao .gitignore
echo "*.sqlite3" >> backend/.gitignore

# Remover do repositório
git rm backend/*.sqlite3
git commit -m "chore: remover arquivos SQLite de desenvolvimento"
```

#### Passo 2: Verificar e Remover Views de Debug

```bash
# Verificar se são usadas
grep -r "views_debug" backend/
grep -r "views_enviar_cliente" backend/

# Se não usadas, remover
git rm backend/crm_vendas/views_debug.py
git rm backend/crm_vendas/views_enviar_cliente.py
git commit -m "chore: remover views de debug não utilizadas"
```

#### Passo 3: Arquivar Scripts de Clientes

```bash
# Criar diretório de arquivo
mkdir -p backend/scripts/archive/2026-03

# Mover scripts
mv backend/fix_clinica_*.py backend/scripts/archive/2026-03/
mv backend/corrigir_data_*_salao.py backend/scripts/archive/2026-03/
mv backend/sync_clinica_*.py backend/scripts/archive/2026-03/

# Criar README
cat > backend/scripts/archive/2026-03/README.md << 'EOF'
# Scripts Arquivados - Março 2026

Scripts one-off para correções específicas de clientes.
Mantidos para referência histórica.

## Uso

Estes scripts NÃO devem ser executados novamente.
São mantidos apenas como referência histórica.
EOF

# Commit
git add backend/scripts/archive/
git commit -m "chore: arquivar scripts específicos de clientes"
```

---

## 🧪 TESTES RECOMENDADOS

### Para Cada Modal Migrado

```typescript
// Checklist de testes
✅ Modal abre corretamente
✅ Lista de itens carrega
✅ Adicionar novo item funciona
✅ Editar item existente funciona
✅ Excluir item funciona
✅ Validações funcionam (campos obrigatórios)
✅ Mensagens de erro aparecem
✅ Loading states funcionam
✅ Modal fecha corretamente
✅ Callback onSuccess é chamado
```

### Para Cada Command Migrado

```bash
# Checklist de testes
✅ Comando executa sem erros
✅ Help text está correto
✅ Argumentos funcionam
✅ Output está formatado
✅ Erros são tratados
✅ Resultado é o esperado
```

---

## 📊 TRACKING DE PROGRESSO

### Modais Migrados

```
[ ] ModalClientes (cabeleireiro)
[ ] ModalClientes (clinica)
[ ] ModalClientes (servicos)
[ ] ModalServicos (cabeleireiro)
[ ] ModalServicos (clinica)
[ ] ModalFuncionarios (cabeleireiro)
[ ] ModalFuncionarios (clinica)
[ ] ModalAgendamentos (cabeleireiro)
[ ] ModalAgendamentos (clinica)

Progresso: 0/9 (0%)
Linhas Reduzidas: 0/~1.000
```

### Scripts Migrados

```
[ ] check_schemas.py
[ ] verificar_orfaos.py
[ ] limpar_orfaos_completo.py
[ ] criar_loja_teste_crm.py
[ ] corrigir_database_names.py

Progresso: 0/5 (0%)
```

### Código Removido

```
[ ] Arquivos SQLite
[ ] Views de debug
[ ] Scripts de clientes arquivados
[ ] Diretórios vazios

Progresso: 0/4 (0%)
```

---

## 🚨 PROBLEMAS COMUNS E SOLUÇÕES

### Problema 1: Modal Genérico Não Funciona

**Sintoma:** Modal não abre ou não carrega dados

**Solução:**
```typescript
// Verificar endpoint
console.log('Endpoint:', endpoint);

// Verificar resposta da API
const response = await apiClient.get(endpoint);
console.log('Response:', response);

// Verificar se extractArrayData está funcionando
import { extractArrayData } from '@/lib/api-helpers';
const data = extractArrayData(response);
console.log('Data:', data);
```

### Problema 2: Command Não Encontrado

**Sintoma:** `python manage.py <command>` não funciona

**Solução:**
```bash
# Verificar estrutura de diretórios
ls -la backend/management/commands/

# Verificar __init__.py
cat backend/management/commands/__init__.py

# Verificar nome do arquivo
# Deve ser: backend/management/commands/<categoria>/<nome>.py
```

### Problema 3: Import Error

**Sintoma:** `ModuleNotFoundError` ao importar

**Solução:**
```python
# Verificar INSTALLED_APPS em settings.py
INSTALLED_APPS = [
    # ...
    'management',  # Adicionar se necessário
]

# Verificar __init__.py em todos os diretórios
```

---

## 📝 TEMPLATE DE COMMIT

### Para Modais

```bash
git commit -m "refactor: migrar ModalClientes (cabeleireiro) para GenericCrudModal

- Remove implementação duplicada
- Usa componente genérico reutilizável
- Mantém mesma funcionalidade
- Reduz ~100 linhas de código

Refs: REFATORACAO_FASE1_EXECUTADA.md"
```

### Para Commands

```bash
git commit -m "refactor: migrar check_schemas para management command

- Converte script solto para Django command
- Adiciona argumentos e help text
- Melhora output com cores
- Facilita manutenção

Refs: REFATORACAO_FASE1_EXECUTADA.md"
```

### Para Remoção

```bash
git commit -m "chore: remover código não utilizado

- Remove arquivos SQLite de desenvolvimento
- Remove views de debug
- Arquiva scripts específicos de clientes

Refs: CODIGO_NAO_UTILIZADO_ANALISE.md"
```

---

## 🎯 METAS SEMANAIS

### Semana 1
- [ ] Migrar 3 modais
- [ ] Migrar 2 scripts
- [ ] Remover arquivos SQLite

**Meta:** 300-400 linhas reduzidas

### Semana 2
- [ ] Migrar 3 modais
- [ ] Migrar 2 scripts
- [ ] Arquivar scripts de clientes

**Meta:** 300-400 linhas reduzidas

### Semana 3
- [ ] Migrar 3 modais restantes
- [ ] Migrar 1 script
- [ ] Remover views de debug

**Meta:** 300-400 linhas reduzidas

### Total (3 Semanas)
**Meta:** ~1.000 linhas reduzidas

---

## ✅ CHECKLIST FINAL

Antes de considerar a refatoração completa:

### Código
- [ ] Todos os modais migrados
- [ ] Todos os scripts prioritários migrados
- [ ] Código não utilizado removido
- [ ] Helpers consolidados
- [ ] API client consolidado

### Testes
- [ ] Todos os modais testados
- [ ] Todos os commands testados
- [ ] Testes automatizados adicionados (se possível)
- [ ] Testes em staging

### Documentação
- [ ] README atualizado
- [ ] CHANGELOG atualizado
- [ ] Documentação de APIs atualizada
- [ ] Guias de uso atualizados

### Deploy
- [ ] Deploy em staging
- [ ] Testes de aceitação
- [ ] Deploy em produção
- [ ] Monitoramento pós-deploy

---

## 📚 RECURSOS ÚTEIS

### Documentação
- `ANALISE_COMPLETA_ESTRUTURA_CRM_PRODUCAO.md` - Análise inicial
- `REFATORACAO_FASE1_EXECUTADA.md` - Detalhes da Fase 1
- `CODIGO_NAO_UTILIZADO_ANALISE.md` - Código não usado
- `REFATORACAO_COMPLETA_RESUMO_v2.md` - Resumo executivo

### Componentes
- `frontend/components/shared/GenericCrudModal.tsx` - Modal genérico
- `frontend/lib/api-client.ts` - API client consolidado
- `frontend/lib/array-helpers.ts` - Helpers de array

### Estrutura
- `backend/management/commands/` - Commands organizados
- `backend/management/commands/README.md` - Guia de commands

---

## 🤝 SUPORTE

### Dúvidas?

1. Consultar documentação acima
2. Verificar exemplos em código existente
3. Testar em ambiente de desenvolvimento
4. Pedir ajuda ao time

### Problemas?

1. Verificar logs de erro
2. Consultar seção "Problemas Comuns"
3. Reverter mudanças se necessário
4. Documentar problema para referência

---

**Guia criado por:** Kiro AI  
**Última Atualização:** 31 de Março de 2026  
**Versão:** 1.0
