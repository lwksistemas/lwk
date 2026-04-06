# Deploy: Correção de Vencimento para Planos Anuais

## 📅 Data do Deploy
06/04/2026

## 🎯 Objetivo
Corrigir o cálculo de vencimento para planos anuais que estava adicionando apenas 30 dias ao invés de 365 dias (1 ano).

## 🐛 Bug Corrigido
Cliente **Dani Pitakos** pagou plano anual em **09/04/2026** mas o sistema mostrava:
- ❌ Próximo Pagamento: 09/04/2026 (mesma data!)
- ✅ Deveria mostrar: 09/04/2027 (1 ano depois)

## 📝 Commit
```
commit f7e96016
fix: Corrigir cálculo de vencimento para planos anuais

- Adicionar lógica para diferenciar planos mensais (30 dias) e anuais (365 dias)
- Corrigir sync_service.py para considerar tipo_assinatura ao calcular próxima cobrança
- Corrigir financeiro_service.py método calcular_proxima_cobranca
- Corrigir cobranca_service.py método _calcular_proxima_cobranca
- Adicionar script para corrigir vencimento do cliente Dani Pitakos
```

## 🚀 Deploy Realizado

### 1. Backend (Heroku)
```bash
git push heroku master
```

**Status:** ✅ Sucesso
- Build: OK
- Release: v1502
- Migrations: Nenhuma pendente
- URL: https://lwksistemas-38ad47519238.herokuapp.com/

### 2. Frontend (Vercel)
```bash
cd frontend && vercel --prod
```

**Status:** ✅ Sucesso
- Build: OK
- Deploy: Production
- URL: https://lwksistemas.com.br

### 3. Correção do Cliente Dani Pitakos
```bash
heroku run python backend/corrigir_vencimento_dani_pitakos.py --app lwksistemas
```

**Status:** ✅ Sucesso

**Dados ANTES da correção:**
- Próxima Cobrança: 2026-05-06 ❌
- Data Vencimento Asaas: 2026-05-06 ❌

**Dados DEPOIS da correção:**
- Próxima Cobrança: 2027-04-09 ✅
- Data Vencimento Asaas: 2027-04-09 ✅

## 📊 Arquivos Modificados

1. `backend/superadmin/sync_service.py`
   - Método `_update_loja_financeiro_from_payment()`
   - Agora considera `tipo_assinatura` ao calcular próxima data

2. `backend/superadmin/services/financeiro_service.py`
   - Método `calcular_proxima_cobranca()`
   - Adicionado parâmetro `tipo_assinatura`
   - Calcula 1 ano para anual, 1 mês para mensal

3. `backend/superadmin/cobranca_service.py`
   - Método `_calcular_proxima_cobranca()`
   - Mesma lógica aplicada

4. `backend/corrigir_vencimento_dani_pitakos.py` (novo)
   - Script para corrigir vencimento de clientes específicos

5. `CORRECAO_VENCIMENTO_PLANO_ANUAL.md` (novo)
   - Documentação completa da correção

## ✅ Validação

### Cliente Dani Pitakos
- ✅ Loja encontrada: Dani Pitakos Produtivos (31682991890)
- ✅ Tipo Assinatura: anual
- ✅ Plano: Profissional Clínica
- ✅ Data Pagamento: 09/04/2026
- ✅ Próximo Vencimento: 09/04/2027 (365 dias depois)

### Próximos Pagamentos
- Planos mensais: continuam com 30 dias ✅
- Planos anuais: agora com 365 dias ✅

## 🔍 Monitoramento

Para verificar se há outros clientes afetados:

```bash
heroku run python backend/manage.py shell --app lwksistemas
```

```python
from superadmin.models import Loja, FinanceiroLoja
from datetime import date, timedelta

# Buscar lojas com plano anual
lojas_anuais = Loja.objects.filter(tipo_assinatura='anual', is_active=True)

for loja in lojas_anuais:
    financeiro = loja.financeiro
    ultimo_pag = financeiro.ultimo_pagamento
    proxima_cob = financeiro.data_proxima_cobranca
    
    if ultimo_pag and proxima_cob:
        dias_diff = (proxima_cob - ultimo_pag.date()).days
        
        # Se a diferença for ~30 dias, está errado (deveria ser ~365)
        if dias_diff < 100:
            print(f"⚠️  {loja.nome}: {dias_diff} dias (deveria ser ~365)")
```

## 📈 Impacto

- ✅ Bug crítico corrigido
- ✅ Cliente Dani Pitakos com data correta
- ✅ Novos pagamentos anuais serão calculados corretamente
- ⚠️  Outros clientes com plano anual podem precisar de correção manual

## 🎉 Resultado

Deploy concluído com sucesso! O sistema agora calcula corretamente:
- **Planos Mensais:** Próximo vencimento em 30 dias
- **Planos Anuais:** Próximo vencimento em 365 dias (1 ano)
