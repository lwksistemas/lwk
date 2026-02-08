# Análise do Problema de Isolamento de Dados - v485

## Problema Relatado
Cliente reportou que ao criar uma nova loja de clínica de estética, ela já vinha com cadastros de outra loja (Clínica Daniele).

## Análise Técnica

### Como o Sistema DEVERIA Funcionar
1. Cada loja tem um `database_name` único (ex: `loja_clinica_daniele_5860`)
2. Cada `database_name` corresponde a um **schema isolado** no PostgreSQL
3. Cada schema tem suas próprias tabelas independentes
4. Dados de uma loja NÃO podem aparecer em outra loja

### Possíveis Causas do Problema

#### 1. **Database Names Duplicados** (MAIS PROVÁVEL)
Se duas lojas compartilham o mesmo `database_name`, elas acessam o mesmo schema e veem os mesmos dados.

**Como verificar:**
```bash
cd backend
python verificar_isolamento_lojas.py
```

**Como acontece:**
- Slug duplicado ou muito similar
- Erro na geração do `database_name`
- Loja criada manualmente com `database_name` errado

**Solução:**
```python
# Corrigir database_name da loja problemática
python manage.py shell
>>> from superadmin.models import Loja
>>> loja = Loja.objects.get(slug='clinica-daniele-5860')
>>> loja.database_name = 'loja_clinica_daniele_5860_novo'  # Nome único
>>> loja.save()
>>> # Criar novo schema e migrar dados
```

#### 2. **Schema Não Criado**
Loja foi criada mas o schema PostgreSQL não foi criado, então usa o schema `public` (compartilhado).

**Como verificar:**
```sql
-- No PostgreSQL
SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'loja_%';
```

**Solução:**
```python
# Criar schema manualmente
python manage.py shell
>>> from django.db import connection
>>> schema_name = 'loja_clinica_daniele_5860'
>>> with connection.cursor() as cursor:
>>>     cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
>>> # Aplicar migrations
>>> from django.core.management import call_command
>>> call_command('migrate', 'clinica_estetica', '--database', 'loja-clinica-daniele-5860')
```

#### 3. **Contexto de Loja Incorreto**
Middleware não está definindo o `loja_id` corretamente, fazendo queries retornarem dados de outra loja.

**Como verificar:**
- Verificar logs do middleware
- Verificar header `X-Loja-ID` nas requisições
- Verificar se URL contém o slug correto

**Solução:**
- Verificar `TenantMiddleware` em `backend/tenants/middleware.py`
- Garantir que `X-Loja-ID` está sendo enviado corretamente

#### 4. **Dados Copiados Durante Criação**
Algum código está copiando dados de uma loja "template" para novas lojas.

**Como verificar:**
```bash
cd backend
grep -r "copy.*data\|template.*loja" --include="*.py" | grep -v venv
```

**Resultado:** Não encontrado código que copia dados.

### Scripts de Diagnóstico Criados

#### 1. `verificar_isolamento_lojas.py`
Verifica:
- Database names duplicados
- Schemas existentes no PostgreSQL
- Contagem de dados por loja

**Uso:**
```bash
cd backend
python verificar_isolamento_lojas.py
```

#### 2. `limpar_dados_loja.py`
Limpa TODOS os dados de uma loja específica (DESTRUTIVO!)

**Uso:**
```bash
cd backend
python limpar_dados_loja.py --loja-slug "clinica-daniele-5860"
# ou
python limpar_dados_loja.py --loja-id 123
```

**ATENÇÃO:** Este script apaga TODOS os dados da loja!

## Plano de Ação

### Passo 1: Diagnóstico
```bash
cd backend
python verificar_isolamento_lojas.py
```

Isso irá mostrar:
- Se há database_names duplicados
- Se os schemas existem
- Quantos dados cada loja tem

### Passo 2: Identificar a Causa
Com base no resultado do diagnóstico:

**Se houver database_names duplicados:**
- Corrigir os database_names
- Criar novos schemas
- Migrar dados se necessário

**Se schemas não existirem:**
- Criar schemas faltantes
- Aplicar migrations

**Se dados estiverem misturados:**
- Limpar dados da loja problemática
- Verificar código de criação de lojas

### Passo 3: Correção

#### Opção A: Limpar Dados (Mais Simples)
Se a loja ainda não tem dados importantes:
```bash
python limpar_dados_loja.py --loja-slug "clinica-daniele-5860"
```

#### Opção B: Corrigir Isolamento (Mais Complexo)
Se precisa manter os dados:
1. Criar novo schema com nome único
2. Copiar dados para o novo schema
3. Atualizar `database_name` da loja
4. Testar acesso

### Passo 4: Prevenção
Adicionar validações na criação de lojas:
- Garantir `database_name` único
- Criar schema automaticamente
- Validar criação antes de retornar sucesso

## Código de Segurança Existente

### 1. LojaIsolationManager
Filtra automaticamente por `loja_id`:
```python
# backend/core/mixins.py
def get_queryset(self):
    loja_id = get_current_loja_id()
    if loja_id:
        return super().get_queryset().filter(loja_id=loja_id)
    return super().get_queryset().none()
```

### 2. TenantMiddleware
Define contexto da loja por requisição:
```python
# backend/tenants/middleware.py
# Extrai loja_id da URL ou header X-Loja-ID
# Define no thread-local storage
```

### 3. Validação no Save
Impede salvar dados em outra loja:
```python
# backend/core/mixins.py
def save(self, *args, **kwargs):
    if current_loja_id and self.loja_id != current_loja_id:
        raise ValidationError('Você não pode criar/editar dados de outra loja')
```

## Recomendações

### Imediato
1. Executar `verificar_isolamento_lojas.py` para diagnóstico
2. Identificar a causa raiz
3. Aplicar correção apropriada

### Curto Prazo
1. Adicionar validação mais rigorosa na criação de lojas
2. Adicionar testes automatizados de isolamento
3. Monitorar logs para detectar problemas similares

### Longo Prazo
1. Considerar migrar para django-tenants (biblioteca especializada)
2. Adicionar auditoria de acesso entre lojas
3. Implementar testes de penetração

## Contato
Se precisar de ajuda adicional, forneça:
1. Output do `verificar_isolamento_lojas.py`
2. Logs do servidor (últimas 100 linhas)
3. URL da loja problemática
4. Quando o problema foi detectado
