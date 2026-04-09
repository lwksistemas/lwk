# Separação de Emissão de NFS-e - Dois Sistemas Independentes

## Data: 09/04/2026

## Visão Geral

O sistema LWK possui DOIS fluxos de emissão de NFS-e completamente separados e independentes:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA LWK                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. NF DA ASSINATURA (LWK → Loja Cliente)                  │ │
│  │                                                              │ │
│  │  Emissor: LWK Sistemas (CNPJ da empresa)                   │ │
│  │  Tomador: Loja cliente (owner da loja)                     │ │
│  │  Quando: Pagamento de assinatura mensal                    │ │
│  │  Certificado: Da LWK Sistemas                              │ │
│  │  Arquivo: backend/asaas_integration/invoice_service.py     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  2. NF DA LOJA (Loja → Cliente Final)                      │ │
│  │                                                              │ │
│  │  Emissor: Cada loja (CNPJ próprio)                         │ │
│  │  Tomador: Clientes da loja                                 │ │
│  │  Quando: Loja presta serviço para seus clientes           │ │
│  │  Certificado: De cada loja (separado)                      │ │
│  │  Arquivo: backend/crm_vendas/models_config.py             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 1. NF da Assinatura (LWK Sistemas)

### Descrição
Nota fiscal emitida pela LWK Sistemas quando uma loja paga sua mensalidade.

### Características
- **Emissor**: LWK Sistemas (CNPJ: [CNPJ_DA_LWK])
- **Tomador**: Administrador da loja (CPF/CNPJ do owner)
- **Serviço**: Licenciamento de software / Assinatura de sistema
- **Certificado**: Certificado digital da LWK Sistemas
- **Provedor**: Asaas (intermediário)
- **Configuração**: Variáveis de ambiente do sistema

### Fluxo
```
1. Loja paga assinatura (boleto/PIX/cartão)
2. Webhook do Asaas notifica pagamento confirmado
3. sync_service.py chama emitir_nf_para_pagamento()
4. NF emitida com CNPJ da LWK Sistemas
5. Email enviado para owner da loja com NF
```

### Arquivos Envolvidos
```
backend/asaas_integration/
├── invoice_service.py          # Emissão de NF da assinatura
├── client.py                   # Cliente Asaas
└── models.py                   # Configuração Asaas

backend/superadmin/
├── sync_service.py             # Processa webhook e emite NF
└── models.py                   # Modelo Loja, FinanceiroLoja
```

### Variáveis de Ambiente
```bash
# Configuração do serviço municipal (LWK Sistemas)
ASAAS_INVOICE_SERVICE_ID=xxx        # ID do serviço no Asaas
ASAAS_INVOICE_SERVICE_CODE=1401     # Código municipal
ASAAS_INVOICE_SERVICE_NAME=Desenvolvimento de software
```

### Código Relevante
```python
# backend/asaas_integration/invoice_service.py

def emitir_nf_para_pagamento(
    asaas_payment_id: str,
    loja,  # Loja que está pagando (TOMADOR)
    value: float,
    description: str,
    send_email: bool = True,
):
    """
    Emite NF da LWK Sistemas para a loja cliente.
    
    EMISSOR: LWK Sistemas (CNPJ da empresa)
    TOMADOR: Loja (owner.email, owner_telefone)
    """
    # Usa certificado e credenciais da LWK Sistemas
    # Configurado via variáveis de ambiente
```

## 2. NF da Loja (Para Clientes Finais)

### Descrição
Nota fiscal emitida por cada loja quando presta serviços aos seus próprios clientes.

### Características
- **Emissor**: Cada loja (CNPJ próprio da loja)
- **Tomador**: Clientes da loja (CPF/CNPJ do cliente final)
- **Serviço**: Serviços prestados pela loja aos seus clientes
- **Certificado**: Certificado digital de cada loja (separado)
- **Provedor**: Configurável por loja (Asaas, ISSNet, API Nacional, Manual)
- **Configuração**: Por loja em CRMConfig

### Fluxo
```
1. Loja presta serviço para cliente final
2. Loja emite NF através do sistema
3. Sistema usa configuração da loja (CRMConfig)
4. NF emitida com CNPJ da loja
5. Email enviado para cliente final
```

### Arquivos Envolvidos
```
backend/crm_vendas/
├── models_config.py            # CRMConfig com campos de NFS-e
├── serializers.py              # CRMConfigSerializer
└── migrations/
    └── 0044_add_nfse_config.py # Migration com campos

frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/
└── nota-fiscal/
    └── page.tsx                # Interface de configuração

frontend/contexts/
└── CRMConfigContext.tsx        # Context com campos de NFS-e
```

### Campos no Banco (CRMConfig)
```python
# backend/crm_vendas/models_config.py

class CRMConfig(models.Model):
    # ... campos existentes ...
    
    # Provedor de NF (escolha da loja)
    provedor_nf = models.CharField(
        choices=[
            ('asaas', 'Asaas (Intermediário)'),
            ('issnet', 'ISSNet - Ribeirão Preto (Direto)'),
            ('nacional', 'API Nacional NFS-e (Direto)'),
            ('manual', 'Emissão Manual'),
        ],
        default='asaas'
    )
    
    # Credenciais ISSNet (da loja)
    issnet_usuario = models.CharField(max_length=100, blank=True)
    issnet_senha = models.CharField(max_length=100, blank=True)
    issnet_certificado = models.FileField(
        upload_to='certificados_nfse/%Y/%m/',
        blank=True,
        null=True,
        help_text='Certificado Digital A1 da LOJA'
    )
    issnet_senha_certificado = models.CharField(max_length=100, blank=True)
    
    # Configurações gerais (da loja)
    codigo_servico_municipal = models.CharField(max_length=10, default='1401')
    descricao_servico_padrao = models.TextField(default='...')
    aliquota_iss = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    emitir_nf_automaticamente = models.BooleanField(default=True)
```

### Código Futuro (Fase 3)
```python
# backend/nfse_integration/service.py (A CRIAR)

def emitir_nfse_loja(loja, cliente, valor, descricao):
    """
    Emite NF da loja para cliente final.
    
    EMISSOR: Loja (CNPJ da loja)
    TOMADOR: Cliente final (CPF/CNPJ do cliente)
    """
    config = CRMConfig.get_or_create_for_loja(loja.id)
    
    if config.provedor_nf == 'asaas':
        # Usar Asaas com credenciais da loja
        return emitir_via_asaas(loja, cliente, valor, descricao)
    
    elif config.provedor_nf == 'issnet':
        # Usar ISSNet com certificado da loja
        client = ISSNetClient(
            usuario=config.issnet_usuario,
            senha=config.issnet_senha,
            certificado_path=config.issnet_certificado.path,
            senha_cert=config.issnet_senha_certificado
        )
        return client.emitir_nfse(loja, cliente, valor, descricao)
```

## Comparação Lado a Lado

| Aspecto | NF da Assinatura (LWK) | NF da Loja (Cliente Final) |
|---------|------------------------|----------------------------|
| **Emissor** | LWK Sistemas | Cada loja |
| **CNPJ Emissor** | CNPJ da LWK | CNPJ da loja |
| **Tomador** | Loja cliente | Cliente final da loja |
| **Certificado** | Da LWK Sistemas | De cada loja (separado) |
| **Configuração** | Variáveis de ambiente | CRMConfig (por loja) |
| **Provedor** | Asaas (fixo) | Configurável (Asaas, ISSNet, etc) |
| **Quando** | Pagamento de assinatura | Serviço prestado pela loja |
| **Arquivo** | `invoice_service.py` | `nfse_integration/` (futuro) |
| **Status** | ✅ Implementado | ⏳ Fase 2 concluída (config) |

## Isolamento de Dados

### Certificados Digitais
```
/media/certificados_nfse/
├── lwk_sistemas.pfx              # Certificado da LWK (assinatura)
└── {ano}/{mes}/
    ├── loja_123_cert.pfx         # Certificado da Loja 123
    ├── loja_456_cert.pfx         # Certificado da Loja 456
    └── loja_789_cert.pfx         # Certificado da Loja 789
```

### Credenciais
```
LWK Sistemas (Assinatura):
- Variáveis de ambiente (ASAAS_INVOICE_SERVICE_ID, etc)
- Único para todo o sistema
- Usado em invoice_service.py

Cada Loja (Clientes Finais):
- Banco de dados (CRMConfig)
- Um registro por loja
- Isolado por loja_id
```

## Interface do Usuário

### Para Administrador da Loja
```
URL: /loja/{slug}/crm-vendas/configuracoes/nota-fiscal

┌─────────────────────────────────────────────────────────┐
│  Configuração de Nota Fiscal da Loja                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ⚠️ Importante: Duas emissões diferentes                 │
│                                                           │
│  • NF da sua assinatura LWK: Emitida automaticamente     │
│    pela LWK Sistemas quando você paga sua mensalidade    │
│                                                           │
│  • NF para seus clientes: Esta configuração é para       │
│    quando VOCÊ prestar serviços aos SEUS clientes        │
│                                                           │
│  Cada loja tem seu próprio CNPJ e certificado digital.   │
│  As configurações abaixo são exclusivas da sua loja.     │
│                                                           │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Provedor de Nota Fiscal:                                │
│  ○ Asaas (Intermediário - Padrão)                        │
│  ○ ISSNet - Ribeirão Preto (Direto)                      │
│  ○ API Nacional NFS-e (Em breve)                         │
│  ○ Emissão Manual                                        │
│                                                           │
│  [Se ISSNet selecionado]                                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Credenciais ISSNet                                 │  │
│  │                                                     │  │
│  │ ⚠️ Certificado da SUA loja (não da LWK)           │  │
│  │                                                     │  │
│  │ Usuário ISSNet: [____________]                     │  │
│  │ Senha ISSNet: [____________]                       │  │
│  │ Certificado .pfx: [Upload]                         │  │
│  │ Senha do Certificado: [____________]               │  │
│  └───────────────────────────────────────────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Segurança

### Separação de Certificados
- ✅ Certificado da LWK armazenado em variáveis de ambiente
- ✅ Certificados das lojas armazenados em `media/certificados_nfse/`
- ✅ Cada loja acessa apenas seu próprio certificado
- ✅ Isolamento por `loja_id` no banco de dados

### Senhas
- ✅ Senhas ISSNet armazenadas como `write_only` no serializer
- ⏳ Implementar criptografia no banco (próxima fase)
- ⏳ Rotação automática de credenciais

## Próximos Passos

### Fase 3: Cliente ISSNet (Backend)
1. Criar módulo `backend/nfse_integration/`
2. Implementar `ISSNetClient` com certificado da loja
3. Construtor de XML RPS com dados da loja
4. Assinatura digital com certificado da loja

### Fase 4: Serviço Unificado
1. Criar `NFSeService` que escolhe provedor baseado em `CRMConfig`
2. Integrar com fluxo de vendas/serviços da loja
3. Dashboard de notas emitidas pela loja
4. Logs e auditoria por loja

## Documentação Relacionada

- [Implementação Interface NFS-e](./IMPLEMENTACAO_INTERFACE_NFSE.md)
- [Análise Emissão NFS-e Ribeirão Preto](./ANALISE_EMISSAO_NFSE_RIBEIRAO_PRETO.md)
- [Configuração NFS-e Loja](./CONFIGURACAO_NFSE_LOJA.md)

---

**Atualizado em**: 09/04/2026
**Versão**: 1.0
**Status**: Documentação completa da separação
