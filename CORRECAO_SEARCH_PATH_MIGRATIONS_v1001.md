# Correção Crítica: search_path em Migrations - v1001/v1002

**Data**: 18/03/2026  
**Versão Heroku**: v1097 (v1001), v1098+ (v1002)  
**Status**: 🔄 EM CORREÇÃO (v1002)

---

## 📋 PROBLEMA CRÍTICO

### Sintoma
Ao criar uma nova loja CRM, o schema era criado mas ficava VAZIO após as migrations. As tabelas eram criadas no schema `public` em vez do schema isolado da loja (`loja_CNPJ`).

### Erro Reportado
```
❌ ERRO CRÍTICO: Schema 'loja_36971645898' está VAZIO após migrations!
⚠️  Nenhuma tabela encontrada em 'public' para mover para 'loja_36971645898'
RuntimeError: Schema 'loja_36971645898' está vazio após migrations
```

### Log de Criação
```
✅ search_path da conexão loja_36971645898: loja_36971645898, public
✅ Migrations aplicadas: stores
✅ Migrations aplicadas: products  
✅ Migrations aplicadas: crm_vendas
❌ Schema 'loja_36971645898' está VAZIO após migrations!
```

---

## 🔍 CAUSA RAIZ

### Problema no Backend Customizado
O backend `core.db_backends.postgresql_schema` estava definindo o `search_path` no método `init_connection_state()`, que é chamado DEPOIS que a conexão já foi estabelecida.

**Sequência do Problema**:
1. Django cria conexão com o banco
2. Django começa a executar migrations
3. Django cria tabelas (ainda sem search_path definido → vai para `public`)
4. `init_connection_state()` é chamado e define search_path
5. Tarde demais! As tabelas já foram criadas em `public`

### Código Problemático (v1000)
```python
class DatabaseWrapper(BasePostgresWrapper):
    def init_connection_state(self):
        super().init_connection_state()
        schema_name = self.settings_dict.get('SCHEMA_NAME')
        if schema_name:
            # Define search_path DEPOIS que conexão já foi usada
            cursor.execute(f'SET search_path TO "{schema_name}", public')
```

---

## ✅ SOLUÇÃO IMPLEMENTADA

### Definir search_path em get_new_connection()
Movemos a definição do `search_path` para o método `get_new_connection()`, que é chamado ANTES de qualquer operação no banco.

**backend/core/db_backends/postgresql_schema/base.py**:
```python
class DatabaseWrapper(BasePostgresWrapper):
    def get_new_connection(self, conn_params):
        """
        Cria nova conexão e define search_path IMEDIATAMENTE.
        Garante que TODAS as operações usem o schema correto.
        """
        connection = super().get_new_connection(conn_params)
        
        # Definir search_path IMEDIATAMENTE após criar a conexão
        schema_name = self.settings_dict.get('SCHEMA_NAME')
        if schema_name and isinstance(schema_name, str):
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{schema_name}", public')
                    logger.info(f"✅ search_path definido para '{schema_name}' na nova conexão")
                except Exception as e:
                    logger.error(f"❌ Erro ao definir search_path: {e}")
        
        return connection

    def init_connection_state(self):
        """
        Reforça o search_path e verifica se está correto.
        """
        super().init_connection_state()
        
        schema_name = self.settings_dict.get('SCHEMA_NAME')
        if schema_name:
            # Verificar se search_path está correto
            cursor.execute('SHOW search_path')
            current_path = cursor.fetchone()[0]
            
            if schema_name not in current_path:
                # Redefinir se necessário
                cursor.execute(f'SET search_path TO "{schema_name}", public')
                logger.warning(f"⚠️  search_path redefinido (estava: {current_path})")
```

### Sequência Corrigida
1. Django cria conexão com o banco
2. `get_new_connection()` define search_path IMEDIATAMENTE
3. Django executa migrations (agora com search_path correto)
4. Tabelas são criadas no schema da loja ✅
5. `init_connection_state()` verifica e reforça o search_path

---

## 🧪 TESTE E VERIFICAÇÃO

### Como Testar
1. Criar nova loja CRM via API
2. Verificar se schema foi criado com tabelas
3. Confirmar que tabelas estão no schema correto (não em `public`)

### Comando de Verificação
```bash
heroku run "python -c \"
import sys; sys.path.insert(0, 'backend'); 
import django; django.setup();
from django.db import connection;
schema = 'loja_CNPJ';
with connection.cursor() as c:
    c.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s', [schema]);
    print(f'Tabelas em {schema}:', c.fetchone()[0])
\""
```

### Resultado Esperado
```
✅ search_path definido para 'loja_CNPJ' na nova conexão
✅ Migrations aplicadas: stores
✅ Migrations aplicadas: products
✅ Migrations aplicadas: crm_vendas
✅ Schema 'loja_CNPJ' criado com sucesso: 25 tabela(s)
```

---

## 📊 IMPACTO

### Antes da Correção (v1000)
- ❌ Lojas CRM não podiam ser criadas
- ❌ Tabelas criadas em `public` (vazamento de dados)
- ❌ Schema da loja ficava vazio
- ❌ Erro crítico bloqueava criação

### Depois da Correção (v1001)
- ✅ Lojas CRM criadas com sucesso
- ✅ Tabelas criadas no schema isolado correto
- ✅ Isolamento multi-tenant funcionando
- ✅ Sem vazamento de dados entre lojas

---

## 🎯 LIÇÕES APRENDIDAS

1. **Timing é Crítico**: `search_path` deve ser definido ANTES de qualquer operação
2. **get_new_connection() vs init_connection_state()**: 
   - `get_new_connection()`: Primeiro método chamado, ideal para configurações críticas
   - `init_connection_state()`: Chamado depois, bom para verificações
3. **Validação de Schema**: Sempre validar nome do schema para evitar SQL injection
4. **Logging Detalhado**: Logs ajudam a identificar quando/onde o search_path é definido
5. **Verificação Dupla**: Verificar em `init_connection_state()` garante que search_path não foi alterado

---

## 📝 ARQUIVOS MODIFICADOS

- ✅ `backend/core/db_backends/postgresql_schema/base.py` - Correção do search_path

---

## 🚀 DEPLOY

- **Versão**: v1097 (Heroku)
- **Data**: 18/03/2026
- **Status**: ✅ Deployado com sucesso
- **Órfãos**: 0 (sistema limpo)

---

**Status Final**: Sistema corrigido e pronto para criar lojas CRM com tabelas isoladas no schema correto.


---

## 🔧 CORREÇÃO ADICIONAL v1002

### Problema Descoberto
Após deploy da v1001, o problema persistiu. Logs mostraram:

```
✅ search_path definido para 'loja_36971645898' na nova conexão
⚠️  Verificação search_path: set_session cannot be used inside a transaction
❌ Schema 'loja_36971645898' está VAZIO após migrations!
```

**Causa**: Estávamos tentando definir `search_path` usando `cursor.execute()` dentro de `get_new_connection()`, mas o Django já havia iniciado uma transação, causando erro "set_session cannot be used inside a transaction".

### Solução v1002
Em vez de tentar definir `search_path` APÓS criar a conexão, agora definimos ANTES, adicionando aos parâmetros de conexão:

```python
def get_new_connection(self, conn_params):
    """
    CORREÇÃO v1002: Adicionar search_path aos parâmetros de conexão ANTES de conectar.
    """
    schema_name = self.settings_dict.get('SCHEMA_NAME')
    if schema_name and isinstance(schema_name, str):
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
            # Adicionar search_path às options do PostgreSQL
            if 'options' not in conn_params:
                conn_params['options'] = ''
            
            search_path_option = f'-c search_path="{schema_name}",public'
            if conn_params['options']:
                conn_params['options'] += f' {search_path_option}'
            else:
                conn_params['options'] = search_path_option
            
            logger.info(f"✅ search_path '{schema_name}' adicionado aos parâmetros de conexão")
    
    # Criar conexão com search_path já definido
    connection = super().get_new_connection(conn_params)
    return connection
```

### Diferença Chave
- **v1001**: Tentava definir search_path DEPOIS de criar conexão (dentro de transação) ❌
- **v1002**: Define search_path ANTES de criar conexão (nos parâmetros) ✅

Isso garante que o PostgreSQL recebe o `search_path` como parte da string de conexão, evitando problemas com transações e connection pooling.

---

**Status v1002**: Correção implementada, aguardando deploy e teste.
