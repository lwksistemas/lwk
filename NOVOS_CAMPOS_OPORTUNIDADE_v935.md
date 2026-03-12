# Novos Campos em Oportunidade - Deploy v935

**Data**: 11/03/2026  
**Deploy Backend**: v932 (Heroku)  
**Status**: ✅ Backend concluído - Frontend pendente

## Campos Adicionados

### 1. data_fechamento_ganho
- **Tipo**: DateField (nullable)
- **Descrição**: Data em que a oportunidade foi fechada como ganha
- **Uso**: Registrar quando a venda foi efetivamente ganha

### 2. data_fechamento_perdido
- **Tipo**: DateField (nullable)
- **Descrição**: Data em que a oportunidade foi fechada como perdida
- **Uso**: Registrar quando a venda foi perdida

### 3. valor_comissao
- **Tipo**: DecimalField (max_digits=10, decimal_places=2, nullable)
- **Descrição**: Valor da comissão para esta oportunidade
- **Uso**: Calcular comissões dos vendedores

## Implementação Backend

### Modelo Atualizado
```python
class Oportunidade(LojaIsolationMixin, models.Model):
    # ... campos existentes
    data_fechamento_ganho = models.DateField(
        null=True, 
        blank=True, 
        help_text='Data em que a oportunidade foi fechada como ganha'
    )
    data_fechamento_perdido = models.DateField(
        null=True, 
        blank=True, 
        help_text='Data em que a oportunidade foi fechada como perdida'
    )
    valor_comissao = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text='Valor da comissão para esta oportunidade'
    )
```

### Serializer Atualizado
```python
class OportunidadeSerializer(serializers.ModelSerializer):
    # ... campos existentes
    
    class Meta:
        model = Oportunidade
        fields = [
            'id', 'titulo', 'lead', 'lead_nome', 'valor', 'etapa', 
            'vendedor', 'vendedor_nome', 'probabilidade', 
            'data_fechamento_prevista', 'data_fechamento', 
            'data_fechamento_ganho',      # NOVO
            'data_fechamento_perdido',    # NOVO
            'valor_comissao',             # NOVO
            'observacoes', 'created_at', 'updated_at',
        ]
```

### Índices Adicionados
- `crm_opor_loja_dtfechganho_idx`: Índice em (loja_id, data_fechamento_ganho)
- `crm_opor_loja_dtfechperd_idx`: Índice em (loja_id, data_fechamento_perdido)

## Migration Aplicada

- **Arquivo**: `backend/crm_vendas/migrations/0008_add_comissao_data_fechamento_fields.py`
- **Status**: ✅ Aplicada com sucesso no Heroku Postgres
- **Comando**: `heroku run python backend/manage.py migrate crm_vendas`

## Próximos Passos - Frontend

### 1. Atualizar Interface do Pipeline
Adicionar campos no formulário de Nova Oportunidade:

```typescript
interface Oportunidade {
  // ... campos existentes
  data_fechamento_ganho?: string | null;
  data_fechamento_perdido?: string | null;
  valor_comissao?: number | null;
}
```

### 2. Formulário de Criação/Edição
Adicionar inputs no modal de oportunidade:

- **Data Fechamento Ganho**: Input tipo `date` (visível quando etapa = 'closed_won')
- **Data Fechamento Perdido**: Input tipo `date` (visível quando etapa = 'closed_lost')
- **Valor Comissão**: Input tipo `number` com formatação de moeda

### 3. Lógica de Negócio
- Quando etapa mudar para 'closed_won', sugerir preencher data_fechamento_ganho
- Quando etapa mudar para 'closed_lost', sugerir preencher data_fechamento_perdido
- Calcular automaticamente valor_comissao baseado em percentual (se configurado)

### 4. Visualização no Pipeline
- Mostrar data de fechamento nos cards das oportunidades fechadas
- Mostrar valor de comissão nos cards (se preenchido)
- Adicionar filtros por data de fechamento

## Casos de Uso

### 1. Registrar Venda Ganha
```json
{
  "etapa": "closed_won",
  "data_fechamento_ganho": "2026-03-11",
  "valor_comissao": 500.00
}
```

### 2. Registrar Venda Perdida
```json
{
  "etapa": "closed_lost",
  "data_fechamento_perdido": "2026-03-11"
}
```

### 3. Relatório de Comissões
```sql
SELECT 
  vendedor_id,
  SUM(valor_comissao) as total_comissao,
  COUNT(*) as total_vendas
FROM crm_vendas_oportunidade
WHERE etapa = 'closed_won'
  AND data_fechamento_ganho >= '2026-03-01'
  AND data_fechamento_ganho < '2026-04-01'
GROUP BY vendedor_id;
```

## Benefícios

1. **Rastreamento Preciso**: Saber exatamente quando cada venda foi fechada
2. **Cálculo de Comissões**: Automatizar pagamento de comissões aos vendedores
3. **Relatórios Financeiros**: Gerar relatórios de vendas por período
4. **Análise de Performance**: Comparar vendedores por comissões geradas
5. **Histórico Completo**: Manter registro de quando vendas foram perdidas

## Compatibilidade

- ✅ Campos nullable - não quebra oportunidades existentes
- ✅ Backward compatible - API continua funcionando sem os novos campos
- ✅ Índices otimizados - queries por data de fechamento serão rápidas
- ✅ Serializer atualizado - novos campos disponíveis na API

## Status Atual

- ✅ Backend: Modelo, serializer e migration prontos
- ⏳ Frontend: Aguardando implementação da interface
- ⏳ Testes: Aguardando implementação do frontend para testar fluxo completo
