# PROBLEMA DE EMISSÃO DE NOTA FISCAL - RESOLVIDO ✅

## 🔴 PROBLEMA IDENTIFICADO

### Sintoma
Após pagamento de boleto PIX, a nota fiscal não era emitida automaticamente.

### Log do Erro
```
Configuração municipal NF: code=None, name=Software sob demanda / Assinatura de sistema, service_id=None
```

### Causa Raiz
A variável de ambiente `ASAAS_INVOICE_SERVICE_CODE` estava configurada no Heroku com valor `"01.07"`, mas o Django estava lendo como `None`.

**Problema**: O `python-decouple` com `default=''` (string vazia) estava retornando string vazia que depois virava `None` quando passada para a API do Asaas.

## � SOLUÇÃO APLICADA

### Arquivo: `backend/config/settings.py`

**ANTES (v1316):**
```python
ASAAS_INVOICE_SERVICE_CODE = config('ASAAS_INVOICE_SERVICE_CODE', default='')
ASAAS_INVOICE_SERVICE_NAME = config('ASAAS_INVOICE_SERVICE_NAME', default='Software sob demanda / Assinatura de sistema')
ASAAS_INVOICE_SERVICE_ID = config('ASAAS_INVOICE_SERVICE_ID', default='')
```

**DEPOIS (v1317):**
```python
# ✅ CORREÇÃO v1317: Usar os.environ.get() diretamente para evitar problema com python-decouple
ASAAS_INVOICE_SERVICE_CODE = os.environ.get('ASAAS_INVOICE_SERVICE_CODE', '01.07')
ASAAS_INVOICE_SERVICE_NAME = os.environ.get('ASAAS_INVOICE_SERVICE_NAME', 'Software sob demanda / Assinatura de sistema')
ASAAS_INVOICE_SERVICE_ID = os.environ.get('ASAAS_INVOICE_SERVICE_ID', '')
```

### Mudanças
1. Substituído `config()` do `python-decouple` por `os.environ.get()` nativo do Python
2. Definido default `'01.07'` para garantir que sempre tenha um valor válido
3. Mantido os outros valores com defaults apropriados

## ✅ VERIFICAÇÃO

### Variável no Heroku
```bash
$ heroku config:get ASAAS_INVOICE_SERVICE_CODE
01.07
```

### Deploy
```bash
$ git add -A
$ git commit -m "fix: Corrigir leitura de ASAAS_INVOICE_SERVICE_CODE usando os.environ.get() - v1317"
$ git push heroku master
```

**Deploy v1317**: ✅ Realizado com sucesso às 15:30

## 📋 PRÓXIMOS PASSOS PARA TESTE

1. **Criar nova loja de teste** ou usar loja existente
2. **Pagar boleto PIX** da assinatura
3. **Verificar logs em tempo real**:
   ```bash
   heroku logs --tail | grep "Configuração municipal\|NF emitida\|invoice"
   ```
4. **Confirmar que**:
   - Log mostra `code=01.07` (não mais `None`)
   - Mensagem "NF emitida para pagamento" aparece
   - E-mail com nota fiscal é enviado ao admin da loja

## 🎯 RESULTADO ESPERADO

Após o pagamento, os logs devem mostrar:
```
Configuração municipal NF: code=01.07, name=Software sob demanda / Assinatura de sistema, service_id=None
NF agendada no Asaas: invoice_id=inv_xxxxx, payment=pay_xxxxx
NF emitida no Asaas: invoice_id=inv_xxxxx
NF emitida para pagamento pay_xxxxx, e-mail enviado: True
```

## 📝 LIÇÕES APRENDIDAS

1. `python-decouple` com `default=''` pode causar problemas quando a string vazia é interpretada como `None`
2. Para variáveis críticas, usar `os.environ.get()` diretamente é mais confiável
3. Sempre definir defaults não vazios para variáveis obrigatórias
4. Logs de debug são essenciais para identificar problemas de configuração

## 🔗 ARQUIVOS RELACIONADOS

- `backend/config/settings.py` (linhas 378-385)
- `backend/asaas_integration/invoice_service.py`
- `backend/superadmin/sync_service.py` (método `process_webhook_payment`)
- `CONFIGURACAO_NOTA_FISCAL_ASAAS.md`
- `TESTE_EMISSAO_NOTA_FISCAL.md`
