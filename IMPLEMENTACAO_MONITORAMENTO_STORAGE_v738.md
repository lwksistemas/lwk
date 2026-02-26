# Implementação v738: Sistema de Monitoramento de Storage

**Data**: 25/02/2026  
**Status**: ✅ Implementado (aguardando migration e deploy)

## Resumo

Sistema completo de monitoramento de uso de storage (espaço em disco) por loja com alertas automáticos quando atingir 80% do limite.

## Arquivos Modificados/Criados

### 1. Modelo `Loja` (`backend/superadmin/models.py`)

**Campos adicionados**:
```python
# ✅ NOVO v738: Monitoramento de Storage
storage_usado_mb = models.DecimalField(
    max_digits=10, decimal_places=2, default=0,
    help_text='Espaço em disco usado pela loja (em MB)'
)
storage_limite_mb = models.IntegerField(
    default=500,
    help_text='Limite de storage da loja (em MB) - baseado no plano'
)
storage_alerta_enviado = models.BooleanField(
    default=False,
    help_text='Indica se alerta de 80% já foi enviado'
)
storage_ultima_verificacao = models.DateTimeField(
    null=True, blank=True,
    help_text='Data da última verificação de storage'
)
```

**Métodos adicionados**:
```python
def get_storage_percentual(self):
    """Retorna o percentual de uso de storage (0-100)"""
    
def is_storage_critical(self):
    """Verifica se o storage está em nível crítico (>= 80%)"""
    
def is_storage_full(self):
    """Verifica se o storage está cheio (>= 100%)"""
```

**Índice adicionado**:
```python
models.Index(fields=['storage_ultima_verificacao'], name='loja_storage_check_idx')
```

### 2. Comando de Gerenciamento (`backend/superadmin/management/commands/verificar_storage_lojas.py`)

**Funcionalidades**:
- Calcula tamanho do schema PostgreSQL de cada loja
- Atualiza campos de storage no banco
- Envia alertas quando atingir 80%
- Bloqueia loja automaticamente quando atingir 100%
- Processa lojas sequencialmente (não sobrecarrega)
- Pausa de 500ms entre lojas

**Uso**:
```bash
# Verificar todas as lojas
python backend/manage.py verificar_storage_lojas

# Verificar loja específica
python backend/manage.py verificar_storage_lojas --loja-id=1

# Forçar envio de alerta
python backend/manage.py verificar_storage_lojas --force-alert

# Simular sem salvar
python backend/manage.py verificar_storage_lojas --dry-run
```

**Query PostgreSQL otimizada**:
```sql
SELECT 
    COALESCE(SUM(pg_total_relation_size(
        quote_ident(schemaname) || '.' || quote_ident(tablename)
    )), 0) as size_bytes
FROM pg_tables
WHERE schemaname = 'loja_clinica_daniel_5889'
```

### 3. EmailService (`backend/superadmin/email_service.py`)

**Métodos adicionados**:
```python
def enviar_alerta_storage_cliente(loja, usado_mb, limite_mb, percentual):
    """Envia alerta de 80% para o cliente"""

def enviar_alerta_storage_admin(loja, usado_mb, limite_mb, percentual):
    """Envia alerta de 80% para o superadmin"""

def enviar_alerta_bloqueio_storage_cliente(loja, usado_mb, limite_mb):
    """Envia alerta de bloqueio para o cliente"""

def enviar_alerta_bloqueio_storage_admin(loja, usado_mb, limite_mb):
    """Envia alerta de bloqueio para o superadmin"""
```

### 4. Endpoints API (`backend/superadmin/views.py`)

**Novos endpoints**:

1. **POST `/api/superadmin/lojas/{loja_id}/verificar-storage/`**
   - Verifica storage de uma loja específica (manual)
   - Apenas superadmin
   - Retorna dados atualizados

2. **GET `/api/superadmin/storage/`**
   - Lista uso de storage de todas as lojas
   - Apenas superadmin
   - Ordenado por percentual (maior primeiro)
   - Inclui estatísticas

### 5. Rotas (`backend/superadmin/urls.py`)

```python
path('lojas/<int:loja_id>/verificar-storage/', verificar_storage_loja),
path('storage/', listar_storage_lojas),
```

## Boas Práticas Aplicadas

### 1. Performance
- ✅ Executa em background (Heroku Scheduler)
- ✅ Processa lojas sequencialmente (não todas de uma vez)
- ✅ Pausa de 500ms entre lojas (não sobrecarrega)
- ✅ Query otimizada do PostgreSQL (50-200ms por loja)
- ✅ Resultado em cache (banco de dados)
- ✅ Índice para queries rápidas

### 2. Segurança
- ✅ Apenas superadmin pode acessar endpoints
- ✅ Validação de permissões
- ✅ Logs detalhados de erros
- ✅ Try-catch em todas as operações críticas

### 3. Manutenibilidade
- ✅ Código bem documentado
- ✅ Docstrings em todos os métodos
- ✅ Logs informativos
- ✅ Separação de responsabilidades
- ✅ Métodos reutilizáveis

### 4. Escalabilidade
- ✅ Suporta milhares de lojas
- ✅ Processamento distribuído ao longo do tempo
- ✅ Não bloqueia requisições dos usuários
- ✅ Pode ser executado em paralelo (múltiplos workers)

### 5. Usabilidade
- ✅ Comandos com opções flexíveis (--loja-id, --force-alert, --dry-run)
- ✅ Output colorido e informativo
- ✅ Resumo final com estatísticas
- ✅ Emails claros e acionáveis

## Fluxo de Funcionamento

### 1. Verificação Automática (Heroku Scheduler)

```
A cada 6 horas (02:00, 08:00, 14:00, 20:00):
1. Heroku Scheduler executa comando
2. Comando busca todas as lojas ativas
3. Para cada loja:
   a. Calcula tamanho do schema PostgreSQL
   b. Atualiza campos no banco
   c. Verifica se atingiu 80% (alerta)
   d. Verifica se atingiu 100% (bloqueio)
   e. Envia emails se necessário
   f. Pausa 500ms
4. Exibe resumo final
```

### 2. Verificação Manual (Endpoint)

```
Superadmin clica em "Verificar Storage":
1. Frontend chama POST /api/superadmin/lojas/{id}/verificar-storage/
2. Backend executa comando para loja específica
3. Retorna dados atualizados
4. Frontend atualiza interface
```

### 3. Alertas

**80% do limite (Alerta)**:
- Email para cliente: "Espaço atingindo o limite"
- Email para superadmin: "Entrar em contato para upgrade"
- Flag `storage_alerta_enviado = True` (envia apenas uma vez)

**100% do limite (Bloqueio)**:
- Email para cliente: "Sistema bloqueado - URGENTE"
- Email para superadmin: "Loja bloqueada - Ação imediata"
- Loja bloqueada automaticamente (`is_blocked = True`)
- Motivo: "Limite de storage atingido"

## Configuração do Heroku Scheduler

### Passo 1: Acessar Heroku Dashboard
```
https://dashboard.heroku.com/apps/lwksistemas/scheduler
```

### Passo 2: Adicionar Job
```
Comando: python backend/manage.py verificar_storage_lojas
Frequência: A cada 6 horas
Próxima execução: 02:00 UTC
```

### Passo 3: Monitorar Logs
```bash
heroku logs --tail --app lwksistemas | grep "verificar_storage"
```

## Testes

### 1. Teste Local (Dry-run)
```bash
python backend/manage.py verificar_storage_lojas --dry-run
```

### 2. Teste com Loja Específica
```bash
python backend/manage.py verificar_storage_lojas --loja-id=1
```

### 3. Teste de Alerta Forçado
```bash
python backend/manage.py verificar_storage_lojas --loja-id=1 --force-alert
```

### 4. Teste de Endpoint
```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/1/verificar-storage/
```

## Próximos Passos

### 1. Criar Migration
```bash
python backend/manage.py makemigrations superadmin
python backend/manage.py migrate
```

### 2. Deploy Backend
```bash
git add .
git commit -m "v738: Sistema de monitoramento de storage"
git push heroku master
```

### 3. Configurar Heroku Scheduler
- Acessar dashboard do Heroku
- Adicionar job conforme instruções acima

### 4. Testar em Produção
```bash
# Executar comando manualmente
heroku run python backend/manage.py verificar_storage_lojas --app lwksistemas

# Monitorar logs
heroku logs --tail --app lwksistemas
```

### 5. Frontend (Opcional)
- Criar dashboard de storage no painel do superadmin
- Mostrar gráficos de uso
- Botão "Verificar Agora"
- Lista de lojas críticas

## Estimativa de Impacto

### Performance
- **Tempo de execução**: 30-60 segundos para 50 lojas
- **Impacto nas requisições**: ZERO (executa em background)
- **Uso de CPU**: < 10% durante execução
- **Uso de memória**: < 50 MB

### Benefícios
- ✅ Previne perda de dados por storage cheio
- ✅ Alerta proativo para clientes
- ✅ Oportunidade de upsell (upgrade de plano)
- ✅ Monitoramento centralizado
- ✅ Bloqueio automático para proteção

## Observações Importantes

1. **Migration obrigatória**: Antes do deploy, executar migration
2. **Heroku Scheduler**: Configurar após deploy
3. **Emails**: Verificar configuração SMTP
4. **Logs**: Monitorar primeiras execuções
5. **Limites por plano**: Ajustar conforme necessário

## Arquivos Criados

- `backend/superadmin/models.py` (modificado)
- `backend/superadmin/management/commands/verificar_storage_lojas.py` (novo)
- `backend/superadmin/email_service.py` (modificado)
- `backend/superadmin/views.py` (modificado)
- `backend/superadmin/urls.py` (modificado)
- `ANALISE_MONITORAMENTO_STORAGE_v738.md` (documentação)
- `ANALISE_PERFORMANCE_MONITORAMENTO_STORAGE.md` (análise de performance)
- `IMPLEMENTACAO_MONITORAMENTO_STORAGE_v738.md` (este arquivo)
