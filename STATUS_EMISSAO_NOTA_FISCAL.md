# STATUS: Emissão Automática de Nota Fiscal - Aguardando Teste

## Situação Atual (25/03/2026)

### Problema Identificado
A emissão de nota fiscal está falhando com erro "Endereço do cliente incompleto" porque:

1. **Lojas antigas**: Criadas ANTES do deploy v1320 já têm clientes no Asaas SEM endereço
2. **Lojas sem endereço**: Mesmo com v1320, se a loja não tem endereço no banco de dados, o erro persiste
3. **Sistema de consulta CEP**: O sistema faz consulta automática de CEP no frontend e preenche os campos automaticamente

### Correções Implementadas

#### v1319 - Correção de Leitura de Variáveis de Ambiente
**Arquivo**: `backend/asaas_integration/invoice_service.py`
**Problema**: `getattr(settings, 'ASAAS_INVOICE_SERVICE_CODE')` retornava `None`
**Solução**: Usar `os.environ.get('ASAAS_INVOICE_SERVICE_CODE', '01.07')` diretamente
**Resultado**: ✅ Código municipal agora é lido corretamente (01.07)

#### v1320 - Inclusão de Endereço Completo ao Criar Cliente
**Arquivos Modificados**:
1. `backend/superadmin/sync_service.py` (linhas 575-585)
2. `backend/superadmin/asaas_service.py` (linhas 120-132)
3. `backend/superadmin/cobranca_service.py` (linhas 60-67)

**Campos Adicionados ao `loja_data`**:
```python
loja_data = {
    'nome': loja.nome,
    'slug': loja.slug,
    'email': loja.owner.email,
    'cpf_cnpj': loja.cpf_cnpj or '000.000.000-00',
    'telefone': getattr(loja.owner, 'telefone', ''),
    # ✅ CORREÇÃO v1320: Incluir endereço completo para emissão de NF
    'endereco': loja.logradouro or '',
    'numero': loja.numero or '',
    'complemento': loja.complemento or '',
    'bairro': loja.bairro or '',
    'cidade': loja.cidade or '',
    'estado': loja.uf or '',
    'cep': loja.cep or '',
}
```

**Resultado**: ✅ Novas lojas criadas após v1320 terão endereço completo no Asaas

### Campos de Endereço no Modelo Loja
**Arquivo**: `backend/superadmin/models.py` (linhas 167-173)

```python
# Endereço
cep = models.CharField(max_length=9, blank=True)
logradouro = models.CharField(max_length=200, blank=True)
numero = models.CharField(max_length=20, blank=True)
complemento = models.CharField(max_length=100, blank=True)
bairro = models.CharField(max_length=100, blank=True)
cidade = models.CharField(max_length=100, blank=True)
uf = models.CharField(max_length=2, blank=True)
```

### Serializer de Criação de Loja
**Arquivo**: `backend/superadmin/serializers.py` (linhas 226-350)

O `LojaCreateSerializer` já inclui todos os campos de endereço:
```python
fields = [
    'nome', 'slug', 'descricao', 'cpf_cnpj',
    'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
    'tipo_loja', 'plano', 'tipo_assinatura', 'provedor_boleto_preferido',
    'owner_full_name', 'owner_username', 'owner_password', 'owner_email', 'owner_telefone', 'dia_vencimento',
    'logo', 'cor_primaria', 'cor_secundaria', 'dominio_customizado'
]
```

### Fluxo de Emissão de NF
**Arquivo**: `backend/superadmin/sync_service.py` (linhas 540-570)

1. Webhook recebe notificação de pagamento confirmado
2. `process_webhook_payment()` identifica o pagamento
3. `_update_loja_financeiro_from_payment()` atualiza financeiro da loja
4. **Emissão de NF** (linhas 555-570):
   ```python
   if loja:
       try:
           from asaas_integration.invoice_service import emitir_nf_para_pagamento
           nf_value = float(payment_data.get('value', 0))
           nf_description = payment_data.get('description') or f"Assinatura - {loja.nome}"
           nf_result = emitir_nf_para_pagamento(
               asaas_payment_id=payment_id,
               loja=loja,
               value=nf_value,
               description=nf_description,
               send_email=True,
           )
           if nf_result.get('success'):
               logger.info(f"NF emitida para pagamento {payment_id}, e-mail enviado: {nf_result.get('email_sent')}")
           else:
               logger.warning(f"Falha ao emitir NF para {payment_id}: {nf_result.get('error')}")
       except Exception as nf_err:
           logger.exception(f"Erro ao emitir NF no webhook: {nf_err}")
   ```

### Teste Realizado
**Loja**: Clínica da Beleza
**Resultado**: ❌ Erro "Endereço do cliente incompleto"
**Motivo**: Loja criada ANTES do deploy v1320, cliente no Asaas sem endereço

### Próximos Passos

#### TESTE PLANEJADO: Exclusão + Importação de Backup + Emissão de NF

**Loja de Teste**: https://lwksistemas.com.br/loja/41449198000172/login
**CNPJ**: 41.449.198/0001-72

**Fluxo do Teste**:

1. ⏳ **Excluir loja existente**
   - Loja: 41449198000172
   - Objetivo: Limpar dados antigos para teste limpo

2. ⏳ **Importar backup da loja**
   - Testar funcionalidade de restore de backup
   - Verificar se todos os dados são restaurados corretamente
   - Confirmar que endereço completo está no banco de dados

3. ⏳ **Pagar boleto da loja restaurada**
   - Webhook será acionado
   - Sistema tentará emitir NF com endereço completo
   - Monitorar logs para verificar sucesso

4. 🔍 **Verificar resultados**
   - ✅ Backup restaurado com sucesso?
   - ✅ Endereço completo no banco de dados?
   - ✅ Cliente criado no Asaas com endereço?
   - ✅ NF emitida com sucesso?
   - ✅ Email da NF enviado ao admin da loja?

**Benefícios deste teste**:
- Valida sistema de backup/restore
- Testa emissão de NF com dados reais
- Confirma que correção v1320 funciona
- Verifica fluxo completo end-to-end

### Variáveis de Ambiente Configuradas
**Heroku Config Vars**:
```bash
ASAAS_INVOICE_SERVICE_CODE="01.07"
ASAAS_INVOICE_SERVICE_NAME="Software sob demanda / Assinatura de sistema"
```

### Webhook URL
```
https://lwksistemas-38ad47519238.herokuapp.com/api/asaas/webhook/
```

### Modo Sandbox
```
ASAAS_SANDBOX=true
```

### Chave PIX
```
lwksistemas@gmail.com
```

## Deploys Realizados

- **v1312**: Email profissional de recuperação de senha
- **v1313**: Email HTML profissional com botão para todos os emails
- **v1314**: Variáveis de ambiente para NF configuradas
- **v1315**: Documentação de teste (apenas docs)
- **v1316**: Log de debug para identificar problema (revelou code=None)
- **v1317**: Tentativa de usar `os.environ.get()` no settings.py (não funcionou)
- **v1318**: Redeploy forçado (não funcionou)
- **v1319**: ✅ Usar `os.environ.get()` diretamente no `invoice_service.py` (FUNCIONOU - code=01.07)
- **v1320**: ✅ Incluir endereço completo da loja ao criar cliente no Asaas

## Observações Importantes

1. **Consulta automática de CEP**: O sistema já faz isso no frontend, preenchendo automaticamente os campos de endereço
2. **Campos obrigatórios**: Para emissão de NF, o Asaas exige endereço completo do cliente
3. **Lojas antigas**: Precisam ter o endereço atualizado manualmente ou recriar o cliente no Asaas
4. **Novas lojas**: Com v1320, todas as novas lojas terão endereço completo automaticamente
