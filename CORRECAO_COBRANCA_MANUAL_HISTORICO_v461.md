# Correção: Cobrança Manual Não Aparecia no Histórico da Loja - v461

## 📋 Problema Identificado

Quando uma cobrança manual era criada pelo SuperAdmin, ela aparecia:
- ✅ No SuperAdmin Financeiro (aba Pagamentos)
- ✅ No SuperAdmin Financeiro (card de assinatura)
- ❌ **NO HISTÓRICO DE PAGAMENTOS DA LOJA** (não aparecia)

## 🔍 Causa Raiz

O sistema usa 2 modelos diferentes para armazenar pagamentos:

1. **`AsaasPayment`** - Usado pelo SuperAdmin para gerenciar cobranças
2. **`PagamentoLoja`** - Usado pela loja para ver seu histórico de pagamentos

### Implementações Anteriores:
- **v457**: Salvar em `AsaasPayment` ✅
- **v458**: Atualizar `FinanceiroLoja` ✅
- **v459**: Atualizar `current_payment` da assinatura ✅
- **v460**: Criar registro em `PagamentoLoja` ⚠️ (com erro)

### Erro no v460:
O código estava criando `PagamentoLoja` mas **faltava o campo `financeiro`** que é obrigatório (ForeignKey):

```python
# ❌ CÓDIGO COM ERRO (v460)
pagamento_loja = PagamentoLoja.objects.create(
    loja=loja,
    asaas_payment_id=resultado['payment_id'],
    valor=resultado['value'],
    status='pendente',
    data_vencimento=resultado['due_date'],
    boleto_url=resultado.get('boleto_url', '')
)
```

## ✅ Solução Implementada (v461)

Adicionado o campo `financeiro` obrigatório e outros campos necessários:

```python
# ✅ CÓDIGO CORRIGIDO (v461)
try:
    financeiro = FinanceiroLoja.objects.get(loja=loja)
    
    # Calcular referência do mês baseado na data de vencimento
    from datetime import datetime
    due_date_obj = datetime.strptime(resultado['due_date'], '%Y-%m-%d').date()
    referencia_mes = due_date_obj.replace(day=1)
    
    pagamento_loja = PagamentoLoja.objects.create(
        loja=loja,
        financeiro=financeiro,  # ✅ Campo obrigatório adicionado
        asaas_payment_id=resultado['payment_id'],
        valor=resultado['value'],
        status='pendente',
        data_vencimento=resultado['due_date'],
        referencia_mes=referencia_mes,  # ✅ Campo obrigatório adicionado
        forma_pagamento='boleto',  # ✅ Campo obrigatório adicionado
        boleto_url=resultado.get('boleto_url', ''),
        boleto_pdf_url=resultado.get('boleto_url', ''),
        pix_copy_paste=resultado.get('pix_copy_paste', '')
    )
    
    logger.info(f"✅ Pagamento salvo no PagamentoLoja (ID: {pagamento_loja.id})")
except FinanceiroLoja.DoesNotExist:
    logger.error(f"❌ FinanceiroLoja não encontrado para {loja.slug}")
except Exception as e:
    logger.error(f"❌ Erro ao criar PagamentoLoja: {e}")
```

## 📦 Campos Adicionados

1. **`financeiro`** (ForeignKey) - Obrigatório, vincula ao FinanceiroLoja
2. **`referencia_mes`** (DateField) - Obrigatório, mês de referência do pagamento
3. **`forma_pagamento`** (CharField) - Obrigatório, tipo de pagamento (boleto/pix)
4. **`boleto_pdf_url`** (URLField) - URL do PDF do boleto
5. **`pix_copy_paste`** (TextField) - Código PIX copia e cola

## 🧪 Como Testar

1. Acesse o SuperAdmin Financeiro:
   https://lwksistemas.com.br/superadmin/financeiro

2. Clique em "Nova Cobrança" em um card de assinatura

3. Escolha uma data de vencimento e clique em "Criar Cobrança"

4. Verifique se a cobrança aparece em:
   - ✅ SuperAdmin Financeiro (aba Pagamentos)
   - ✅ SuperAdmin Financeiro (card de assinatura)
   - ✅ **Histórico de Pagamentos da Loja** (agora deve aparecer!)

5. Acesse o dashboard da loja:
   https://lwksistemas.com.br/loja/luiz-5889/dashboard

6. Clique em "⚙️ Configurações da Loja"

7. Verifique se a nova cobrança aparece no "📋 Histórico de Pagamentos"

## 📊 Estrutura do Modelo PagamentoLoja

```python
class PagamentoLoja(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    financeiro = models.ForeignKey(FinanceiroLoja, on_delete=models.CASCADE)  # ✅ Obrigatório
    
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    referencia_mes = models.DateField()  # ✅ Obrigatório
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    asaas_payment_id = models.CharField(max_length=100, blank=True)
    boleto_url = models.URLField(blank=True)
    boleto_pdf_url = models.URLField(blank=True)
    pix_qr_code = models.TextField(blank=True)
    pix_copy_paste = models.TextField(blank=True)
    
    forma_pagamento = models.CharField(max_length=50)  # ✅ Obrigatório
    data_vencimento = models.DateField()
    data_pagamento = models.DateTimeField(null=True, blank=True)
```

## 🚀 Deploy

```bash
# Backend v461
git add -A
git commit -m "v461: Corrigir criação de PagamentoLoja - adicionar campo financeiro obrigatório"
git push heroku master
```

## 📝 Arquivos Modificados

- `backend/asaas_integration/views.py` (função `create_manual_payment`)

## ✅ Status

- **Deploy Backend**: v461 ✅
- **Deploy Frontend**: v456 (sem alterações necessárias)
- **Status**: Aguardando teste do usuário

## 🔄 Próximos Passos

1. Usuário deve criar uma **nova cobrança manual** para testar v461
2. Verificar se aparece no histórico da loja
3. Se funcionar, problema resolvido! 🎉
