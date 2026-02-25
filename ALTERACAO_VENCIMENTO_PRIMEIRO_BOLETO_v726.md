# Alteração: Vencimento do Primeiro Boleto - v726

## 📋 Resumo

Alteração na lógica de vencimento do primeiro boleto ao criar uma nova loja.

## 🎯 Regra Implementada

### Antes (v725)
- Primeiro boleto: vencimento no próximo mês, no dia escolhido pelo cliente
- Próximos boletos: mesmo dia fixo

### Depois (v726)
- **Primeiro boleto**: vencimento em **3 dias** a partir da criação da loja
- **Próximos boletos**: dia fixo escolhido pelo cliente ao criar a loja

## 💡 Motivação

Dar ao cliente um prazo curto (3 dias) para realizar o primeiro pagamento e ativar a loja rapidamente, enquanto mantém um dia fixo de vencimento para as mensalidades seguintes.

## 🔧 Implementação

### Arquivo Modificado
`backend/superadmin/serializers.py` - Classe `LojaCreateSerializer`, método `create()`

### Código Alterado

```python
# ✅ MODIFICAÇÃO v726: Primeiro boleto vence em 3 dias
# Próximos boletos: dia fixo escolhido pelo cliente
hoje = date.today()

# Primeiro boleto: 3 dias a partir de hoje
primeiro_vencimento = hoje + timedelta(days=3)

# Usar primeiro_vencimento para a cobrança inicial
proxima_cobranca = primeiro_vencimento
```

### Fluxo Completo

1. **Criação da Loja**
   - Cliente escolhe dia de vencimento (ex: dia 10)
   - Sistema cria `FinanceiroLoja` com:
     - `data_proxima_cobranca` = hoje + 3 dias
     - `dia_vencimento` = 10 (salvo para próximas cobranças)

2. **Primeira Cobrança**
   - Signal cria boleto/PIX com vencimento em 3 dias
   - Cliente tem 3 dias para pagar

3. **Após Primeiro Pagamento**
   - Webhook processa pagamento
   - Sistema calcula próxima cobrança usando `dia_vencimento` (dia 10)
   - Função `_update_loja_financeiro_after_mercadopago_payment()` ou similar usa o `dia_vencimento` salvo

4. **Próximas Cobranças**
   - Sempre no dia fixo escolhido (dia 10)
   - Calculado pela função de renovação

## 📊 Exemplo Prático

### Cenário
- Loja criada em: 25/02/2026 (terça-feira)
- Dia de vencimento escolhido: 10

### Resultado
- **Primeiro boleto**: vence em 28/02/2026 (3 dias depois)
- **Segunda mensalidade**: vence em 10/04/2026 (dia 10 do próximo mês após pagamento)
- **Terceira mensalidade**: vence em 10/05/2026 (dia 10)
- **E assim por diante**: sempre dia 10

## ✅ Testes Necessários

### Teste 1: Loja com Asaas
1. Criar loja escolhendo dia 15
2. Verificar que primeiro boleto vence em 3 dias
3. Pagar primeiro boleto
4. Verificar que próxima cobrança é dia 15 do próximo mês

### Teste 2: Loja com Mercado Pago
1. Criar loja escolhendo dia 20
2. Verificar que primeiro boleto/PIX vence em 3 dias
3. Pagar via PIX
4. Verificar que próxima cobrança é dia 20 do próximo mês

### Teste 3: Dia Inválido
1. Criar loja escolhendo dia 31
2. Verificar que primeiro boleto vence em 3 dias
3. Pagar
4. Verificar que próxima cobrança em fevereiro é dia 28 (último dia do mês)

## 🔍 Verificação

### Comando para verificar
```bash
heroku run python backend/manage.py shell --app lwksistemas
```

```python
from superadmin.models import Loja
from datetime import date, timedelta

# Buscar loja recém-criada
loja = Loja.objects.latest('created_at')
financeiro = loja.financeiro

print(f"Loja: {loja.nome}")
print(f"Criada em: {loja.created_at.date()}")
print(f"Primeiro vencimento: {financeiro.data_proxima_cobranca}")
print(f"Dia vencimento fixo: {financeiro.dia_vencimento}")

# Verificar se primeiro vencimento é 3 dias após criação
esperado = loja.created_at.date() + timedelta(days=3)
print(f"\nEsperado: {esperado}")
print(f"Correto: {financeiro.data_proxima_cobranca == esperado}")
```

## 📝 Observações

1. O campo `dia_vencimento` no `FinanceiroLoja` continua armazenando o dia fixo escolhido
2. Apenas o primeiro vencimento é calculado como "hoje + 3 dias"
3. As renovações automáticas usam o `dia_vencimento` salvo
4. Funciona para Asaas e Mercado Pago

## 🚀 Deploy

```bash
git add backend/superadmin/serializers.py ALTERACAO_VENCIMENTO_PRIMEIRO_BOLETO_v726.md
git commit -m "v726: Primeiro boleto vence em 3 dias, próximos no dia fixo"
git push heroku master
```

## 📅 Data da Alteração

25 de Fevereiro de 2026

## ✅ Status

Implementado e pronto para teste

---

**Próximos passos**: Testar criação de nova loja e verificar se primeiro boleto vence em 3 dias.
