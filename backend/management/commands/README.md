# Management Commands

Comandos Django organizados por categoria para manutenção do sistema.

## Estrutura

```
commands/
├── check/      # Comandos de verificação (schemas, clientes, orfãos)
├── fix/        # Comandos de correção (database names, vendedores)
├── create/     # Comandos de criação (lojas, admins, schemas)
└── cleanup/    # Comandos de limpeza (orfãos, schemas antigos)
```

## Como Usar

### Comandos de Verificação
```bash
python manage.py check_schemas
python manage.py check_orfaos
python manage.py check_clientes
```

### Comandos de Correção
```bash
python manage.py fix_database_names
python manage.py fix_vendedores
```

### Comandos de Criação
```bash
python manage.py create_loja --nome "Minha Loja" --tipo cabeleireiro
python manage.py create_admin --loja-id 123
```

### Comandos de Limpeza
```bash
python manage.py cleanup_orfaos
python manage.py cleanup_schemas
```

## Migração de Scripts Antigos

Scripts soltos na raiz do backend devem ser migrados para esta estrutura:

1. Identificar a categoria do script (check, fix, create, cleanup)
2. Converter para Django Command
3. Mover para o diretório apropriado
4. Deletar script original

### Exemplo de Conversão

**Antes** (`backend/check_schemas.py`):
```python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# código do script...
```

**Depois** (`backend/management/commands/check/check_schemas.py`):
```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Verifica schemas do banco de dados'
    
    def handle(self, *args, **options):
        # código do script...
        self.stdout.write(self.style.SUCCESS('Verificação concluída'))
```

## Boas Práticas

1. **Nomeação**: Use verbos claros (check, fix, create, cleanup)
2. **Help Text**: Sempre adicione descrição no `help`
3. **Arguments**: Use `add_arguments()` para parâmetros
4. **Output**: Use `self.stdout.write()` para mensagens
5. **Errors**: Use `self.stderr.write()` para erros
6. **Style**: Use `self.style.SUCCESS()`, `self.style.ERROR()`, etc.

## Scripts a Migrar

### Prioridade Alta (Uso Frequente)
- [ ] `check_schemas.py` → `check/check_schemas.py`
- [ ] `verificar_orfaos.py` → `check/check_orfaos.py`
- [ ] `limpar_orfaos_completo.py` → `cleanup/cleanup_orfaos.py`
- [ ] `criar_loja_teste_crm.py` → `create/create_loja.py`
- [ ] `corrigir_database_names.py` → `fix/fix_database_names.py`

### Prioridade Média (Uso Ocasional)
- [ ] `check_clientes.sh` → `check/check_clientes.py`
- [ ] `verificar_isolamento_lojas.py` → `check/check_isolamento.py`
- [ ] `criar_superadmin.py` → `create/create_superadmin.py`
- [ ] `limpar_schemas_orfaos.py` → `cleanup/cleanup_schemas.py`

### Prioridade Baixa (Scripts Específicos de Cliente)
- Scripts com nomes de clientes específicos devem ser movidos para `scripts/archive/`
- Exemplos: `fix_clinica_daniel.py`, `corrigir_data_luiz_salao.py`

## Arquivamento

Scripts obsoletos ou específicos de clientes devem ser movidos para:
```
backend/scripts/archive/YYYY-MM/
```

Exemplo:
```
backend/scripts/archive/2026-03/
├── fix_clinica_daniel.py
├── corrigir_data_luiz_salao.py
└── README.md  # Explicando contexto dos scripts
```
