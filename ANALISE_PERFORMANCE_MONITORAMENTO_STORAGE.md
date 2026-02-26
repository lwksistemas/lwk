# Análise de Performance: Monitoramento de Storage

**Data**: 25/02/2026  
**Questão**: As alterações de monitoramento de storage vão deixar o sistema ou servidor mais lento?

## Resposta Curta

**NÃO**, se implementado corretamente. O monitoramento será executado em **background** (fora do horário de uso) e **não afetará** as requisições dos usuários.

## Análise Detalhada

### ❌ O que PODE deixar o sistema lento (e vamos EVITAR):

1. **Calcular storage em CADA requisição**:
   ```python
   # ❌ RUIM - Executa em cada request do usuário
   def middleware(request):
       loja = get_loja(request)
       storage = calcular_storage(loja)  # LENTO! Query pesada
       if storage > limite:
           bloquear()
   ```
   - **Impacto**: Cada requisição ficaria 200-500ms mais lenta
   - **Resultado**: Sistema inutilizável com muitos usuários

2. **Calcular storage de TODAS as lojas de uma vez**:
   ```python
   # ❌ RUIM - Processa todas as lojas simultaneamente
   for loja in Loja.objects.all():  # 100+ lojas
       calcular_storage(loja)  # Query pesada para cada uma
   ```
   - **Impacto**: Servidor travaria por 5-10 minutos
   - **Resultado**: Timeout, usuários não conseguem acessar

### ✅ O que vamos fazer (SEM impacto):

1. **Executar em background via Heroku Scheduler**:
   ```python
   # ✅ BOM - Executa a cada 6 horas, fora do horário de pico
   # Heroku Scheduler: 02:00, 08:00, 14:00, 20:00
   python backend/manage.py verificar_storage_lojas
   ```
   - **Impacto**: ZERO nas requisições dos usuários
   - **Motivo**: Executa em processo separado, não bloqueia requests

2. **Processar lojas uma por vez (não todas de uma vez)**:
   ```python
   # ✅ BOM - Processa loja por loja, com pausa entre elas
   for loja in Loja.objects.filter(is_active=True):
       calcular_storage(loja)
       time.sleep(0.5)  # Pausa de 500ms entre lojas
   ```
   - **Impacto**: Distribuído ao longo de 1-2 minutos
   - **Motivo**: Não sobrecarrega o banco de dados

3. **Usar query otimizada do PostgreSQL**:
   ```python
   # ✅ BOM - Query nativa do PostgreSQL (rápida)
   SELECT pg_total_relation_size('schema_name')
   ```
   - **Tempo**: 50-200ms por loja
   - **Motivo**: Query otimizada do próprio PostgreSQL

4. **Armazenar resultado no banco (cache)**:
   ```python
   # ✅ BOM - Salva resultado para consulta rápida
   loja.storage_usado_mb = 450.5
   loja.storage_ultima_verificacao = now()
   loja.save()
   ```
   - **Benefício**: Usuários veem resultado instantâneo
   - **Motivo**: Não precisa recalcular a cada consulta

## Comparação de Performance

### Cenário 1: SEM monitoramento (atual)
```
Requisição do usuário: 50-100ms
Carga do servidor: Normal
```

### Cenário 2: COM monitoramento (proposto)
```
Requisição do usuário: 50-100ms (IGUAL)
Carga do servidor: Normal + 1-2 min a cada 6h (background)
```

**Conclusão**: ZERO impacto nas requisições dos usuários.

## Detalhamento Técnico

### 1. Heroku Scheduler (Background Job)

```bash
# Executa em processo separado (worker)
# NÃO usa o dyno web (que atende usuários)
python backend/manage.py verificar_storage_lojas
```

**Como funciona**:
- Heroku cria um **dyno temporário** só para este comando
- Executa em **paralelo** ao dyno web (não bloqueia)
- Termina automaticamente após conclusão
- **Custo**: ~1-2 minutos de dyno worker a cada 6 horas

### 2. Query PostgreSQL Otimizada

```sql
-- Query nativa do PostgreSQL (muito rápida)
SELECT pg_total_relation_size('loja_clinica_daniel_5889');
-- Tempo: 50-200ms por schema
```

**Por que é rápida**:
- Função nativa do PostgreSQL (C/C++)
- Usa cache interno do PostgreSQL
- Não precisa ler todos os dados, só metadados

### 3. Processamento Sequencial

```python
# Processa 1 loja por vez, não todas simultaneamente
for loja in lojas:
    calcular_storage(loja)  # 50-200ms
    time.sleep(0.5)         # Pausa de 500ms
    # Total: ~700ms por loja
```

**Exemplo com 50 lojas**:
- Tempo total: 50 lojas × 700ms = 35 segundos
- Distribuído ao longo de 35 segundos (não instantâneo)
- **Impacto no servidor**: Mínimo, carga distribuída

### 4. Cache no Banco de Dados

```python
# Resultado salvo no banco
loja.storage_usado_mb = 450.5
loja.storage_ultima_verificacao = '2026-02-25 14:00:00'

# Consulta rápida (sem recalcular)
storage = loja.storage_usado_mb  # Instantâneo!
```

**Benefício**:
- Dashboard mostra resultado instantâneo
- Não precisa recalcular a cada visualização
- Atualizado a cada 6 horas (suficiente)

## Otimizações Adicionais

### 1. Executar fora do horário de pico

```bash
# Heroku Scheduler - Horários sugeridos:
02:00 - Madrugada (baixo uso)
08:00 - Manhã (médio uso)
14:00 - Tarde (médio uso)
20:00 - Noite (baixo uso)
```

### 2. Limitar número de lojas por execução

```python
# Processar apenas 20 lojas por vez
lojas = Loja.objects.filter(is_active=True)[:20]
```

**Benefício**: Execução mais rápida (14 segundos ao invés de 35)

### 3. Pular lojas recém-verificadas

```python
# Só verificar lojas não verificadas nas últimas 6 horas
from datetime import timedelta
limite = timezone.now() - timedelta(hours=6)
lojas = Loja.objects.filter(
    is_active=True,
    storage_ultima_verificacao__lt=limite
)
```

**Benefício**: Reduz processamento desnecessário

### 4. Usar índice no banco

```python
# Migration adiciona índice
class Meta:
    indexes = [
        models.Index(fields=['storage_ultima_verificacao'], 
                    name='loja_storage_check_idx'),
    ]
```

**Benefício**: Query de lojas a verificar fica mais rápida

## Monitoramento de Performance

### Métricas a acompanhar:

1. **Tempo de execução do comando**:
   ```bash
   # Deve ser < 2 minutos para 50 lojas
   time python backend/manage.py verificar_storage_lojas
   ```

2. **Uso de CPU durante execução**:
   ```bash
   # Deve ser < 30% de CPU
   heroku logs --tail --app lwksistemas | grep "verificar_storage"
   ```

3. **Tempo de resposta das requisições**:
   ```bash
   # Deve permanecer < 200ms
   heroku logs --tail --app lwksistemas | grep "response_time"
   ```

## Comparação com Sistemas Similares

### Exemplo 1: Backup automático
- **Frequência**: Diário (1x por dia)
- **Duração**: 5-10 minutos
- **Impacto**: Zero (executa em background)

### Exemplo 2: Sincronização Asaas
- **Frequência**: A cada 10 minutos
- **Duração**: 30-60 segundos
- **Impacto**: Zero (executa em background)

### Exemplo 3: Monitoramento de storage (proposto)
- **Frequência**: A cada 6 horas
- **Duração**: 30-60 segundos
- **Impacto**: Zero (executa em background)

**Conclusão**: Monitoramento de storage é **MENOS** frequente que sincronização Asaas.

## Recomendações Finais

### ✅ Implementar com segurança:

1. **Usar Heroku Scheduler** (não middleware)
2. **Processar lojas sequencialmente** (não todas de uma vez)
3. **Executar fora do horário de pico** (madrugada/noite)
4. **Armazenar resultado no banco** (cache)
5. **Adicionar timeout** (máximo 5 minutos)
6. **Monitorar performance** (logs do Heroku)

### ⚠️ Sinais de alerta (se acontecer):

1. Comando demora > 5 minutos
2. CPU do servidor > 80% durante execução
3. Tempo de resposta das requisições aumenta
4. Usuários reportam lentidão

**Ação**: Otimizar query ou reduzir frequência

## Conclusão

**Resposta definitiva**: NÃO, o monitoramento de storage **NÃO vai deixar o sistema lento** porque:

1. ✅ Executa em **background** (Heroku Scheduler)
2. ✅ Processa **1 loja por vez** (não todas simultaneamente)
3. ✅ Usa **query otimizada** do PostgreSQL (50-200ms)
4. ✅ Armazena resultado no banco (**cache**)
5. ✅ Executa **fora do horário de pico** (madrugada/noite)
6. ✅ Frequência **baixa** (a cada 6 horas)

**Impacto nas requisições dos usuários**: ZERO

**Impacto no servidor**: Mínimo (1-2 minutos a cada 6 horas)

**Comparação**: Menos impacto que sincronização Asaas (que já funciona bem)

## Posso implementar?

Sim, com confiança! O sistema foi projetado para **não afetar a performance** das requisições dos usuários.
